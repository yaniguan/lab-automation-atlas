"""Offline unit tests for Markdown link parsing, SSRF/HTTPS safety, retries, concurrency, and exit codes."""

from __future__ import annotations

import email.message
import importlib
import io
import json
import os
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from lab_atlas.linkcheck import (
    DEFAULT_USER_AGENT,
    MAX_BODY_BYTES,
    WAF_403_ALLOWLIST_DOMAINS,
    SafeRedirectHandler,
    SecurityValidationError,
    audit_markdown_files,
    check_local_link,
    check_url,
    check_urls_concurrent,
    extract_links,
    extract_urls,
    is_waf_allowlisted_domain,
    validate_url_target,
)


class _SpyResponse:
    def __init__(self, status: int, url: str, body: bytes = b"") -> None:
        self.status = status
        self._url = url
        self._stream = io.BytesIO(body)
        self.closed = False
        self.read_sizes: list[int] = []

    def getcode(self) -> int:
        return self.status

    def geturl(self) -> str:
        return self._url

    def read(self, amt: int | None = None) -> bytes:
        self.read_sizes.append(-1 if amt is None else amt)
        return self._stream.read(amt)

    def close(self) -> None:
        self.closed = True

    def __enter__(self) -> "_SpyResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _make_http_error(url: str, code: int, reason: str = "Error", headers: dict[str, str] | None = None):
    hdrs = email.message.Message()
    for k, v in (headers or {}).items():
        hdrs[k] = v
    fp = io.BytesIO(b"error")
    return urllib.error.HTTPError(url, code, reason, hdrs, fp)


def _public_dns_stub(host: str, port: int, type: int = 0):
    return [(2, 1, 6, "", ("93.184.216.34", port))]


def test_import_check_links_script_has_no_network_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Issue #14: Importing scripts/check_links.py must not perform network I/O at import time."""

    def _forbid_urlopen(*args, **kwargs):
        raise AssertionError("urlopen called at import time!")

    monkeypatch.setattr(urllib.request, "urlopen", _forbid_urlopen)
    import scripts.check_links as script_mod

    reloaded = importlib.reload(script_mod)
    assert callable(reloaded.main)
    assert callable(reloaded.extract_urls)


def test_extract_links_handles_balanced_parens_titles_refs_autolinks_and_code() -> None:
    """Issue #2: Balanced parentheses, optional link titles, reference defs, autolinks, code stripping."""
    md = """
# Heading One

Inline with balanced parens: [DOI](https://doi.org/10.1002/(SICI)1097-0290(1999)62:1)
Inline with title: [Opentrons](https://docs.opentrons.com/v2/ "Opentrons API v2 Docs")
Angle bracketed: [Spec](<https://example.org/spec(v1)>)
Autolink: <https://sila-standard.com/>
Relative link with anchor: [Arch](docs/ARCHITECTURE_AND_HISTORY.md#1-object)

[ref-id]: https://arxiv.org/abs/2407.10362 'LAB-Bench Paper'

```markdown
[Ignored inside fenced block](https://broken.invalid/should-not-parse)
```

Inline code `[Ignored](https://broken.invalid/inline)` is skipped too.
"""
    links = extract_links(md, source_file="README.md")
    ext_urls = extract_urls(md)
    assert "https://doi.org/10.1002/(SICI)1097-0290(1999)62:1" in ext_urls
    assert "https://docs.opentrons.com/v2/" in ext_urls
    assert "https://example.org/spec(v1)" in ext_urls
    assert "https://sila-standard.com/" in ext_urls
    assert "https://arxiv.org/abs/2407.10362" in ext_urls
    assert all("broken.invalid" not in u for u in ext_urls)

    local_targets = [x.target for x in links if x.kind == "local"]
    assert "docs/ARCHITECTURE_AND_HISTORY.md#1-object" in local_targets


def test_local_link_and_anchor_validation(tmp_path: Path) -> None:
    """Issue #2: Verify relative paths, missing files, repo-root confinement, and #anchor slugs."""
    (tmp_path / "docs").mkdir()
    doc = tmp_path / "docs" / "guide.md"
    doc.write_text("# Setup Guide\n\n## Deep Section\nText.\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text("# Root\n", encoding="utf-8")

    assert check_local_link("docs/guide.md#deep-section", readme, tmp_path).ok is True
    missing_anchor = check_local_link("docs/guide.md#nonexistent", readme, tmp_path)
    assert missing_anchor.ok is False
    assert "not found" in (missing_anchor.error or "")

    missing_file = check_local_link("docs/missing.md", readme, tmp_path)
    assert missing_file.ok is False

    escaped = check_local_link("../../etc/passwd", readme, tmp_path)
    assert escaped.ok is False
    assert "escapes repository root" in (escaped.error or "")


def test_utf8_and_cwd_independence_and_stream_closure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Issue #3: UTF-8 punctuation, CWD independence, and deterministic socket closure."""
    md = tmp_path / "README.md"
    md.write_text("UTF-8 em—dash · middle dot [Link](https://example.com/ok)\n", encoding="utf-8")

    sub = tmp_path / "subdir"
    sub.mkdir()
    monkeypatch.chdir(sub)

    created_responses: list[_SpyResponse] = []

    class _FakeOpener:
        def open(self, req: urllib.request.Request, timeout: float = 10.0) -> _SpyResponse:
            if req.get_method() == "HEAD":
                raise _make_http_error(req.full_url, 405, "Method Not Allowed")
            resp = _SpyResponse(200, req.full_url, b"<html><title>Healthy Page</title></html>" + b"x" * 50000)
            created_responses.append(resp)
            return resp

    report = audit_markdown_files(
        tmp_path,
        max_workers=2,
        opener_factory=lambda _rh: _FakeOpener(),  # type: ignore[arg-type]
        resolver=_public_dns_stub,
    )
    assert report["broken_total"] == 0
    assert len(created_responses) == 1
    assert created_responses[0].closed is True
    assert created_responses[0].read_sizes == [MAX_BODY_BYTES]


def test_waf_403_allowlist_vs_github_403_and_retries() -> None:
    """Issue #4: Allowlist vendor 403s only, fail GitHub/HF/arXiv 403s, and retry 429/503 with HEAD->GET."""
    for host in ("github.com", "arxiv.org", "huggingface.co", "pypi.org"):
        assert is_waf_allowlisted_domain(host) is False
    assert is_waf_allowlisted_domain("www.hamiltoncompany.com") is True
    assert len(WAF_403_ALLOWLIST_DOMAINS) >= 5

    # 403 on github.com must FAIL
    class _Always403Opener:
        def open(self, req: urllib.request.Request, timeout: float = 10.0):
            raise _make_http_error(req.full_url, 403, "Forbidden")

    gh_res = check_url(
        "https://github.com/yaniguan/private-or-removed",
        opener_factory=lambda _rh: _Always403Opener(),  # type: ignore[arg-type]
        resolver=_public_dns_stub,
        sleep_fn=lambda _s: None,
    )
    assert gh_res.ok is False
    assert gh_res.waf_allowlisted is False

    # 403 on allowlisted vendor domain passes with explicit waf_allowlisted=True
    vendor_res = check_url(
        "https://www.hamiltoncompany.com/automated-liquid-handling",
        opener_factory=lambda _rh: _Always403Opener(),  # type: ignore[arg-type]
        resolver=_public_dns_stub,
        sleep_fn=lambda _s: None,
    )
    assert vendor_res.ok is True
    assert vendor_res.waf_allowlisted is True
    assert vendor_res.display_status() == "403 (WAF allowlisted)"

    # Transient 429 -> 503 -> 206 Partial Content succeeds with recorded backoff sleeps
    calls: list[str] = []
    sleeps: list[float] = []

    class _FlakyOpener:
        def open(self, req: urllib.request.Request, timeout: float = 10.0):
            calls.append(req.get_method())
            if len(calls) == 1:
                raise _make_http_error(req.full_url, 429, "Too Many Requests", {"Retry-After": "1"})
            if len(calls) == 2:
                raise _make_http_error(req.full_url, 503, "Service Unavailable")
            return _SpyResponse(206, req.full_url, b"")

    flaky_res = check_url(
        "https://arxiv.org/abs/2407.10362",
        max_retries=3,
        opener_factory=lambda _rh: _FlakyOpener(),  # type: ignore[arg-type]
        resolver=_public_dns_stub,
        sleep_fn=sleeps.append,
    )
    assert flaky_res.ok is True
    assert flaky_res.status_code == 206
    assert len(sleeps) == 2
    assert sleeps[0] == 1.0


def test_ssrf_https_validation_and_redirect_downgrade_blocking() -> None:
    """Issue #6: Honest User-Agent, HTTPS-only, SSRF IP/DNS checks, and redirect downgrade rejection."""
    assert "lab-automation-atlas-linkcheck" in DEFAULT_USER_AGENT

    for bad_url in (
        "http://example.com/insecure",
        "file:///etc/passwd",
        "ftp://ftp.example.com/file",
        "https://localhost/admin",
        "https://127.0.0.1:8080/secret",
        "https://169.254.169.254/latest/meta-data/",
        "https://10.0.0.5/internal",
        "https://[::1]/loopback",
        "https://[::ffff:127.0.0.1]/mapped",
        "https://user:pass@example.com/path",
    ):
        with pytest.raises(SecurityValidationError):
            validate_url_target(bad_url, require_https=True, resolve_dns=False)

    # DNS rebinding / private A-record resolution blocked
    def _private_dns(host: str, port: int, type: int = 0):
        return [(2, 1, 6, "", ("192.168.1.10", port))]

    with pytest.raises(SecurityValidationError):
        validate_url_target("https://rebind.example.com/", require_https=True, resolve_dns=True, resolver=_private_dns)

    # HTTPS -> HTTP downgrade redirect blocked by SafeRedirectHandler
    handler = SafeRedirectHandler(max_redirects=5, require_https=True, resolve_dns=False)
    req = urllib.request.Request("https://example.com/start")
    with pytest.raises(SecurityValidationError, match="downgrade"):
        handler.redirect_request(req, None, 301, "Moved", {}, "http://example.com/downgraded")

    # Redirect to loopback IP blocked
    with pytest.raises(SecurityValidationError, match="SSRF"):
        handler.redirect_request(req, None, 302, "Found", {}, "https://127.0.0.1/internal")


def test_parallel_threadpool_concurrency_and_sorted_output() -> None:
    """Issue #5: Bounded ThreadPoolExecutor with per-host semaphore and deterministic sorted output."""
    urls = [
        f"https://host-{i % 3}.example.com/item-{i:02d}"
        for i in range(12)
    ]
    lock = threading.Lock()
    in_flight_per_host: dict[str, int] = {}
    max_seen_per_host: dict[str, int] = {}
    max_total_in_flight = 0
    total_in_flight = 0

    class _SlowOpener:
        def open(self, req: urllib.request.Request, timeout: float = 10.0):
            nonlocal total_in_flight, max_total_in_flight
            host = req.host
            with lock:
                total_in_flight += 1
                max_total_in_flight = max(max_total_in_flight, total_in_flight)
                in_flight_per_host[host] = in_flight_per_host.get(host, 0) + 1
                max_seen_per_host[host] = max(max_seen_per_host.get(host, 0), in_flight_per_host[host])
            time.sleep(0.02)
            with lock:
                total_in_flight -= 1
                in_flight_per_host[host] -= 1
            return _SpyResponse(200, req.full_url, b"")

    results = check_urls_concurrent(
        list(reversed(urls)),
        max_workers=6,
        per_host_limit=2,
        opener_factory=lambda _rh: _SlowOpener(),  # type: ignore[arg-type]
        resolver=_public_dns_stub,
    )
    assert [r.url for r in results] == sorted(urls)
    assert max_total_in_flight >= 2
    assert all(v <= 2 for v in max_seen_per_host.values())


def test_exit_codes_soft_404_and_json_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Issues #1 & #20: Non-zero exit code on broken/soft-404 links, --warn-only override, and JSON report."""
    import scripts.check_links as check_links_script

    md = tmp_path / "README.md"
    md.write_text(
        "- [Dead](https://example.com/missing)\n"
        "- [Moved](https://example.com/docs/v2/guide)\n"
        "- [Soft404](https://example.com/soft-missing)\n",
        encoding="utf-8",
    )

    class _ReportOpener:
        def open(self, req: urllib.request.Request, timeout: float = 10.0):
            if req.full_url.endswith("/missing"):
                raise _make_http_error(req.full_url, 404, "Not Found")
            if req.full_url.endswith("/docs/v2/guide"):
                return _SpyResponse(200, "https://other-domain.example.org/", b"")
            if req.get_method() == "HEAD":
                raise _make_http_error(req.full_url, 405, "Use GET")
            return _SpyResponse(200, req.full_url, b"<html><title>Error 404 - Page Not Found</title></html>")

    orig_audit = check_links_script.audit_markdown_files

    def _patched_audit(repo_root: Path, **kwargs):
        kwargs["opener_factory"] = lambda _rh: _ReportOpener()
        kwargs["resolver"] = _public_dns_stub
        kwargs["sleep_fn"] = lambda _s: None
        return orig_audit(repo_root, **kwargs)

    monkeypatch.setattr(check_links_script, "audit_markdown_files", _patched_audit)

    json_report = tmp_path / "reports" / "link_status.json"
    rc_fail = check_links_script.main(["--repo-root", str(tmp_path), "--json-out", str(json_report)])
    assert rc_fail == 1
    assert json_report.is_file()

    payload = json.loads(json_report.read_text(encoding="utf-8"))
    assert payload["broken_external_count"] == 2  # /missing (404) + /soft-missing (soft-404 title)
    assert payload["warning_count"] >= 2
    by_url = {r["url"]: r for r in payload["external_results"]}
    assert by_url["https://example.com/docs/v2/guide"]["root_redirect_warning"] is True
    assert by_url["https://example.com/docs/v2/guide"]["cross_domain_redirect"] is True
    assert by_url["https://example.com/soft-missing"]["soft_404_warning"] is True
    assert by_url["https://example.com/soft-missing"]["ok"] is False

    rc_warn = check_links_script.main(["--repo-root", str(tmp_path), "--warn-only"])
    assert rc_warn == 0


@pytest.mark.parametrize(
    "obfuscated_or_transition_url",
    [
        "https://localhost./admin",
        "https://api.localhost/mcp",
        "https://svc.internal/mcp",
        "https://printer.home.arpa/ipp",
        "https://intranet/secret",
        "https://@example.com/mcp",
        "https://user:secret@example.com/mcp",
        "https://example.com:70000/mcp",
        "https://example.com:80:80/mcp",
        "https://public.example.com\\@127.0.0.1/mcp",
        "https://127.1/internal-config",
        "https://127.0.1/internal-config",
        "https://2130706433/internal-config",
        "https://0177.0.0.1/internal-config",
        "https://127.0.0.01/internal-config",
        "https://0x7f000001/internal-config",
        "https://0x7f.0.0.1/internal-config",
        "https://169.254.43518/latest/meta-data",
        "https://[::127.0.0.1]/mcp",
        "https://[64:ff9b::127.0.0.1]/mcp",
        "https://[64:ff9b:1::127.0.0.1]/mcp",
        "https://[::ffff:0:127.0.0.1]/mcp",
        "https://[2002:7f00:0001::1]/mcp",
        "https://[2001:0000:7f00:0001:0000:ffff:80ff:fffe]/mcp",
        "https://[fe80::1%25eth0]/mcp",
        "https://[::1%lo0]/mcp",
    ],
)
def test_issue_24_ssrf_canonicalization_ipv4_forms_and_ipv6_transitions(
    obfuscated_or_transition_url: str,
) -> None:
    """Issue #24: Block non-canonical IPv4 literals, IPv6 transitions, trailing dots, and port/userinfo tricks."""
    with pytest.raises(SecurityValidationError):
        validate_url_target(obfuscated_or_transition_url, require_https=True, resolve_dns=False)


def test_issue_24_dns_pinned_https_connection_prevents_toctou_rebinding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Issue #24: Ensure TCP socket dials the pre-validated IP while preserving TLS SNI server_hostname."""
    from lab_atlas.linkcheck import _PinnedHTTPSConnection

    dns_calls = 0

    def _rebind_resolver(host: str, port: int, type: int = 0):
        nonlocal dns_calls
        dns_calls += 1
        # First lookup returns safe public IP; any second lookup would return 127.0.0.1 (rebind attack)
        ip = "93.184.216.34" if dns_calls == 1 else "127.0.0.1"
        return [(2, 1, 6, "", (ip, port))]

    pinned_ips: dict[tuple[str, int], list[str]] = {}
    validate_url_target(
        "https://rebind.example.com/resource",
        require_https=True,
        resolve_dns=True,
        resolver=_rebind_resolver,
        pinned_ips=pinned_ips,
    )
    assert dns_calls == 1
    assert pinned_ips[("rebind.example.com", 443)] == ["93.184.216.34"]

    dialed_targets: list[tuple[str, int]] = []
    sni_hosts: list[str | None] = []

    class _DummyRawSock:
        def close(self) -> None:
            pass

    class _DummyTlsSock:
        def close(self) -> None:
            pass

    def _fake_create_connection(address: tuple[str, int], timeout=None, source_address=None):
        dialed_targets.append(address)
        return _DummyRawSock()

    import socket as socket_mod
    import ssl as ssl_mod

    real_ctx = ssl_mod.create_default_context()
    monkeypatch.setattr(socket_mod, "create_connection", _fake_create_connection)
    monkeypatch.setattr(
        real_ctx,
        "wrap_socket",
        lambda sock, server_hostname=None: (sni_hosts.append(server_hostname) or _DummyTlsSock()),
    )
    conn = _PinnedHTTPSConnection(
        "rebind.example.com",
        443,
        pinned_ips=pinned_ips,
        resolver=_rebind_resolver,
        context=real_ctx,
    )
    conn.connect()

    # Must NOT perform a second DNS lookup and must dial strictly 93.184.216.34 with SNI=rebind.example.com
    assert dns_calls == 1
    assert dialed_targets == [("93.184.216.34", 443)]
    assert conn.connected_ip == "93.184.216.34"
    assert sni_hosts == ["rebind.example.com"]
    assert conn.tls_server_hostname == "rebind.example.com"


def test_issue_29_cross_domain_redirect_waf_403_bypass_blocked() -> None:
    """Issue #29: Cross-domain redirect from allowlisted vendor host to GitHub 403 must fail."""

    class _RedirectToGitHub403Opener:
        def open(self, req: urllib.request.Request, timeout: float = 10.0):
            raise _make_http_error(
                "https://github.com/vendor/removed-private-repo",
                403,
                "Forbidden",
            )

    res = check_url(
        "https://www.hamiltoncompany.com/legacy-sdk-link",
        opener_factory=lambda _rh: _RedirectToGitHub403Opener(),  # type: ignore[arg-type]
        resolver=_public_dns_stub,
        sleep_fn=lambda _s: None,
    )
    assert res.final_url == "https://github.com/vendor/removed-private-repo"
    assert res.ok is False
    assert res.waf_allowlisted is False


def test_issue_29_http_416_range_not_satisfiable_retries_unranged_get() -> None:
    """Issue #29: Retry GET without Range header when ranged GET returns 416 Range Not Satisfiable."""
    seen_requests: list[tuple[str, str | None]] = []

    class _StrictRangeOpener:
        def open(self, req: urllib.request.Request, timeout: float = 10.0):
            method = req.get_method()
            range_hdr = req.get_header("Range")
            seen_requests.append((method, range_hdr))
            if method == "HEAD":
                raise _make_http_error(req.full_url, 405, "Method Not Allowed")
            if range_hdr is not None:
                raise _make_http_error(req.full_url, 416, "Range Not Satisfiable")
            return _SpyResponse(200, req.full_url, b"<html><title>Zero-Byte Friendly</title></html>")

    res = check_url(
        "https://example.com/strict-range-endpoint",
        opener_factory=lambda _rh: _StrictRangeOpener(),  # type: ignore[arg-type]
        resolver=_public_dns_stub,
        sleep_fn=lambda _s: None,
    )
    assert res.ok is True
    assert res.status_code == 200
    assert seen_requests == [
        ("HEAD", None),
        ("GET", f"bytes=0-{MAX_BODY_BYTES - 1}"),
        ("GET", None),
    ]


def test_issue_29_redirect_count_preserved_on_http_error_and_ssrf_block() -> None:
    """Issue #29: Preserve redirect_handler.redirect_urls count when redirect chain ends in failure."""

    def _build_404_after_hop_opener(rh: SafeRedirectHandler):
        class _HopThen404Opener:
            def open(self, req: urllib.request.Request, timeout: float = 10.0):
                rh.redirect_request(
                    req,
                    None,
                    302,
                    "Found",
                    {},
                    "https://example.com/hop-1",
                )
                raise _make_http_error("https://example.com/hop-1", 404, "Not Found")

        return _HopThen404Opener()

    res_404 = check_url(
        "https://example.com/start",
        opener_factory=_build_404_after_hop_opener,  # type: ignore[arg-type]
        resolver=_public_dns_stub,
        sleep_fn=lambda _s: None,
    )
    assert res_404.ok is False
    assert res_404.status_code == 404
    assert res_404.redirect_count == 1
    assert res_404.final_url == "https://example.com/hop-1"

    def _build_ssrf_on_hop2_opener(rh: SafeRedirectHandler):
        class _HopThenSsrfOpener:
            def open(self, req: urllib.request.Request, timeout: float = 10.0):
                next_req = rh.redirect_request(
                    req,
                    None,
                    302,
                    "Found",
                    {},
                    "https://example.com/hop-1",
                )
                rh.redirect_request(
                    next_req,
                    None,
                    302,
                    "Found",
                    {},
                    "https://127.0.0.1/internal",
                )
                return _SpyResponse(200, req.full_url, b"")

        return _HopThenSsrfOpener()

    res_ssrf = check_url(
        "https://example.com/start",
        opener_factory=_build_ssrf_on_hop2_opener,  # type: ignore[arg-type]
        resolver=_public_dns_stub,
        sleep_fn=lambda _s: None,
    )
    assert res_ssrf.ok is False
    assert res_ssrf.status_code == "BLOCKED"
    assert res_ssrf.redirect_count == 1
    assert res_ssrf.final_url == "https://example.com/hop-1"


def test_issue_29_markdown_unbracketed_prose_escaped_brackets_and_indented_fences() -> None:
    """Issue #29: Ignore unbracketed `](`, escaped `\\[`, and list-indented tilde/backtick code fences."""
    md = (
        "Escaped bracket prose: \\[not a link\\](missing_file.md)\n"
        "Half-escaped open bracket: \\[also not a link](also_missing.md)\n"
        "Unmatched paren prose: array](index) and [Real](https://example.com/real) trailing](bogus)\n"
        "- List item with indented tilde fence:\n"
        "  ~~~markdown\n"
        "  [Example](https://broken.invalid/in-tilde-fence)\n"
        "  ~~~\n"
        "- List item with indented backtick fence:\n"
        "   ```python\n"
        "   # [CodeComment](https://broken.invalid/in-backtick-fence)\n"
        "   ```\n"
        "Code-formatted label: [`MIT`](https://example.com/license)\n"
        "Nested badge: [![CI](https://example.com/badge.svg)](https://example.com/builds)\n"
    )
    links = extract_links(md, source_file="README.md")
    targets = [item.target for item in links]

    assert "missing_file.md" not in targets
    assert "also_missing.md" not in targets
    assert "index" not in targets
    assert "bogus" not in targets
    assert "https://broken.invalid/in-tilde-fence" not in targets
    assert "https://broken.invalid/in-backtick-fence" not in targets

    assert targets == [
        "https://example.com/real",
        "https://example.com/license",
        "https://example.com/badge.svg",
        "https://example.com/builds",
    ]
