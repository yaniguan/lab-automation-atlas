"""Balanced Markdown link parser, SSRF/HTTPS redirect guard, concurrent checker, and JSON reporter."""

from __future__ import annotations

import concurrent.futures
import html
import ipaddress
import json
import re
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

DEFAULT_USER_AGENT = (
    "lab-automation-atlas-linkcheck/0.2 (+https://github.com/yaniguan/lab-automation-atlas)"
)
BROWSER_FALLBACK_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
MAX_BODY_BYTES = 16_384

# Commercial vendor / publisher marketing domains known to block datacenter IP sweeps with HTTP 403.
# Open-source code hosts and scientific registries (github.com, arxiv.org, huggingface.co, pypi.org,
# doi.org, gitlab.io, protocols.io, open-reaction-database.org, ncbi.nlm.nih.gov) are NEVER allowlisted.
WAF_403_ALLOWLIST_DOMAINS: frozenset[str] = frozenset(
    {
        "hamiltoncompany.com",
        "tecan.com",
        "automata.tech",
        "biosero.com",
        "emeraldcloudlab.com",
        "strateos.com",
        "ginkgobioworks.com",
        "bio-protocol.org",
    }
)

TRANSIENT_HTTP_CODES: frozenset[int] = frozenset({429, 502, 503, 504})
HEAD_FALLBACK_CODES: frozenset[int] = frozenset({400, 403, 405, 501})

_SOFT_404_TITLE_PATTERNS = (
    re.compile(r"\b404\b.*\bnot\s+found\b", re.IGNORECASE),
    re.compile(r"\bpage\s+not\s+found\b", re.IGNORECASE),
    re.compile(r"\bdomain\s+(?:is\s+)?for\s+sale\b", re.IGNORECASE),
    re.compile(r"\bparked\s+domain\b", re.IGNORECASE),
)

_FENCED_CODE_RE = re.compile(r"(^|\n)(```+|~~~+)[^\n]*\n.*?\n\2[ \t]*(?=\n|$)", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"(`+)([^`]*?)\1")
_REF_DEF_RE = re.compile(
    r"^[ ]{0,3}\[([^\]]+)\]:[ \t]*(?:<([^>\s]+)>|([^\s\"'(]+))(?:[ \t]+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?[ \t]*$",
    re.MULTILINE,
)
_AUTOLINK_RE = re.compile(r"<((?:https?|ftp|file|javascript|data):[^>\s]+)>", re.IGNORECASE)
_HEADING_RE = re.compile(r"^[ ]{0,3}#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)
_TITLE_TAG_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

_SECOND_LEVEL_TLDS = frozenset({"co.uk", "ac.uk", "org.uk", "gov.uk", "edu.au", "co.jp"})


class SecurityValidationError(ValueError):
    """Raised when a URL or redirect violates scheme or SSRF safety rules."""


@dataclass(frozen=True)
class ExtractedLink:
    target: str
    kind: str  # "external", "local", "unsafe_scheme"
    source_file: str
    syntax: str  # "inline", "reference", "autolink"


@dataclass
class LocalLinkResult:
    source_file: str
    target: str
    resolved_path: str
    ok: bool
    error: str | None = None


@dataclass
class LinkCheckResult:
    url: str
    final_url: str
    status_code: int | str
    ok: bool
    method: str
    redirect_count: int = 0
    cross_domain_redirect: bool = False
    root_redirect_warning: bool = False
    soft_404_warning: bool = False
    waf_allowlisted: bool = False
    page_title: str | None = None
    latency_ms: float = 0.0
    error: str | None = None

    def display_status(self) -> str:
        if self.waf_allowlisted:
            return f"{self.status_code} (WAF allowlisted)"
        return str(self.status_code)


def _strip_code_regions(markdown_text: str) -> str:
    """Remove fenced code blocks and inline code spans prior to link extraction."""
    without_fenced = _FENCED_CODE_RE.sub("\n", markdown_text)
    return _INLINE_CODE_RE.sub("", without_fenced)


def _parse_inline_destination(raw_inside: str) -> str | None:
    """Parse balanced Markdown link destination, stripping optional title strings."""
    s = raw_inside.strip()
    if not s:
        return None
    if s.startswith("<"):
        end_angle = s.find(">")
        if end_angle == -1:
            return None
        return s[1:end_angle].strip()

    # Scan destination until unescaped whitespace at paren depth 0
    depth = 0
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "\\" and i + 1 < n:
            i += 2
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth > 0:
                depth -= 1
        elif ch in (" ", "\t", "\r", "\n") and depth == 0:
            break
        i += 1
    dest = s[:i].strip()
    return dest or None


def _iter_inline_targets(cleaned_md: str) -> list[str]:
    """Extract all inline `[label](...)` targets supporting nested balanced parentheses."""
    targets: list[str] = []
    n = len(cleaned_md)
    idx = 0
    while idx < n:
        pos = cleaned_md.find("](", idx)
        if pos == -1:
            break
        # Ensure the preceding '[' wasn't escaped
        start = pos + 2
        if start < n and cleaned_md[start] == "<":
            close_angle = cleaned_md.find(">", start + 1)
            if close_angle != -1:
                close_paren = cleaned_md.find(")", close_angle + 1)
                if close_paren != -1:
                    dest = _parse_inline_destination(cleaned_md[start:close_paren])
                    if dest:
                        targets.append(dest)
                    idx = close_paren + 1
                    continue

        depth = 1
        j = start
        in_quote: str | None = None
        while j < n and depth > 0:
            ch = cleaned_md[j]
            if ch == "\\" and j + 1 < n:
                j += 2
                continue
            if in_quote is not None:
                if ch == in_quote:
                    in_quote = None
            else:
                if ch in ('"', "'") and j > start and cleaned_md[j - 1] in (" ", "\t"):
                    in_quote = ch
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        break
            j += 1

        if depth == 0:
            raw_inside = cleaned_md[start:j]
            dest = _parse_inline_destination(raw_inside)
            if dest:
                targets.append(dest)
            idx = j + 1
        else:
            idx = start
    return targets


def _classify_target(target: str) -> str | None:
    lower = target.lower()
    if lower.startswith("mailto:"):
        return None
    if lower.startswith(("https://", "http://")):
        return "external"
    if lower.startswith(("javascript:", "data:", "file:", "ftp:")):
        return "unsafe_scheme"
    if ":" in target.split("/", 1)[0] and not target.startswith("#"):
        return "unsafe_scheme"
    return "local"


def extract_links(markdown_text: str, source_file: str = "README.md") -> list[ExtractedLink]:
    """Extract inline, reference-style, and autolink targets from Markdown text."""
    cleaned = _strip_code_regions(markdown_text)
    extracted: list[ExtractedLink] = []

    for dest in _iter_inline_targets(cleaned):
        kind = _classify_target(dest)
        if kind:
            extracted.append(ExtractedLink(target=dest, kind=kind, source_file=source_file, syntax="inline"))

    for match in _REF_DEF_RE.finditer(cleaned):
        dest = (match.group(2) or match.group(3) or "").strip()
        if dest:
            kind = _classify_target(dest)
            if kind:
                extracted.append(
                    ExtractedLink(target=dest, kind=kind, source_file=source_file, syntax="reference")
                )

    for match in _AUTOLINK_RE.finditer(cleaned):
        dest = match.group(1).strip()
        kind = _classify_target(dest)
        if kind:
            extracted.append(ExtractedLink(target=dest, kind=kind, source_file=source_file, syntax="autolink"))

    return extracted


def extract_urls(markdown_text: str) -> list[str]:
    """Extract sorted unique external HTTP(S) URLs from Markdown text."""
    urls = {
        item.target
        for item in extract_links(markdown_text)
        if item.kind == "external"
    }
    return sorted(urls)


def discover_markdown_files(repo_root: Path) -> list[Path]:
    """Return README.md and all docs/**/*.md files in deterministic order."""
    files: list[Path] = []
    readme = repo_root / "README.md"
    if readme.is_file():
        files.append(readme)
    docs_dir = repo_root / "docs"
    if docs_dir.is_dir():
        files.extend(sorted(docs_dir.rglob("*.md")))
    return files


def github_heading_slug(heading_text: str) -> str:
    """Compute GitHub-style Markdown anchor slug from heading text."""
    # Strip inline markdown links [text](url) -> text and formatting characters
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading_text)
    text = text.replace("`", "").strip().lower()
    # Keep alphanumeric, spaces, hyphens, underscores (GitHub anchor behavior)
    cleaned_chars: list[str] = []
    for ch in text:
        if ch.isalnum() or ch in ("-", "_"):
            cleaned_chars.append(ch)
        elif ch.isspace():
            cleaned_chars.append("-")
    return "".join(cleaned_chars).strip("-")


def extract_heading_slugs(markdown_text: str) -> set[str]:
    """Extract all valid GitHub-style anchor slugs (including duplicate `-1`, `-2` suffixes)."""
    cleaned = _strip_code_regions(markdown_text)
    counts: dict[str, int] = {}
    slugs: set[str] = set()
    for match in _HEADING_RE.finditer(cleaned):
        base = github_heading_slug(match.group(1))
        if not base:
            continue
        if base not in counts:
            counts[base] = 0
            slugs.add(base)
        else:
            counts[base] += 1
            slugs.add(f"{base}-{counts[base]}")
    return slugs


def check_local_link(target: str, source_file: Path, repo_root: Path) -> LocalLinkResult:
    """Verify relative file existence, repo-root confinement, and Markdown #anchor validity."""
    repo_root = repo_root.resolve()
    source_file = source_file.resolve()
    rel_source = str(source_file.relative_to(repo_root)).replace("\\", "/")

    path_part, sep, fragment = target.partition("#")
    path_part = urllib.parse.unquote(path_part)

    if path_part == "":
        target_path = source_file
    elif path_part.startswith("/"):
        target_path = (repo_root / path_part.lstrip("/")).resolve()
    else:
        target_path = (source_file.parent / path_part).resolve()

    try:
        resolved_rel = str(target_path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        return LocalLinkResult(
            source_file=rel_source,
            target=target,
            resolved_path=str(target_path),
            ok=False,
            error="Local link escapes repository root.",
        )

    if not target_path.exists():
        return LocalLinkResult(
            source_file=rel_source,
            target=target,
            resolved_path=resolved_rel,
            ok=False,
            error=f"Target path '{resolved_rel}' does not exist.",
        )

    if sep and fragment and target_path.is_file() and target_path.suffix.lower() == ".md":
        md_content = target_path.read_text(encoding="utf-8")
        slugs = extract_heading_slugs(md_content)
        if fragment.lower() not in slugs:
            return LocalLinkResult(
                source_file=rel_source,
                target=target,
                resolved_path=resolved_rel,
                ok=False,
                error=f"Heading anchor '#{fragment}' not found in '{resolved_rel}'.",
            )

    return LocalLinkResult(
        source_file=rel_source,
        target=target,
        resolved_path=resolved_rel,
        ok=True,
        error=None,
    )


def _check_ip_safe(ip_str: str) -> None:
    ip_obj = ipaddress.ip_address(ip_str)
    mapped = getattr(ip_obj, "ipv4_mapped", None)
    for candidate in (ip_obj, mapped) if mapped is not None else (ip_obj,):
        if (
            candidate.is_private
            or candidate.is_loopback
            or candidate.is_link_local
            or candidate.is_multicast
            or candidate.is_reserved
            or candidate.is_unspecified
        ):
            raise SecurityValidationError(
                f"Blocked non-public IP address {ip_str} (SSRF protection)."
            )


def validate_url_target(
    url: str,
    *,
    require_https: bool = True,
    resolve_dns: bool = False,
    resolver: Callable[..., Any] | None = None,
) -> urllib.parse.SplitResult:
    """Validate URL scheme, credentials, hostname, and IP/DNS SSRF boundaries."""
    parsed = urllib.parse.urlsplit(url)
    scheme = parsed.scheme.lower()
    if require_https and scheme != "https":
        raise SecurityValidationError(f"Non-HTTPS URL rejected: {url!r} (scheme={scheme!r}).")
    if not require_https and scheme not in ("http", "https"):
        raise SecurityValidationError(f"Unsupported URL scheme: {url!r} (scheme={scheme!r}).")
    if parsed.username or parsed.password:
        raise SecurityValidationError(f"Credentials in URL are forbidden: {url!r}.")

    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host:
        raise SecurityValidationError(f"Missing hostname in URL: {url!r}.")
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise SecurityValidationError(f"Blocked local hostname {host!r} (SSRF protection).")

    try:
        ipaddress.ip_address(host)
        is_literal_ip = True
    except ValueError:
        is_literal_ip = False

    if is_literal_ip:
        _check_ip_safe(host)
    elif resolve_dns:
        lookup = resolver or socket.getaddrinfo
        port = parsed.port or (443 if scheme == "https" else 80)
        try:
            infos = lookup(host, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise urllib.error.URLError(f"DNS lookup failed for {host}: {exc}") from exc
        if not infos:
            raise urllib.error.URLError(f"DNS lookup returned no records for {host}")
        for info in infos:
            sockaddr = info[4]
            if sockaddr:
                _check_ip_safe(sockaddr[0])

    return parsed


def registrable_domain(hostname: str) -> str:
    """Approximate registrable domain (eTLD+1) for cross-domain redirect flagging."""
    host = hostname.strip().lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    tail2 = ".".join(parts[-2:])
    if tail2 in _SECOND_LEVEL_TLDS and len(parts) >= 3:
        return ".".join(parts[-3:])
    return tail2


def is_waf_allowlisted_domain(hostname: str) -> bool:
    """Return True strictly when hostname belongs to an explicitly allowlisted vendor WAF domain."""
    host = hostname.strip().lower().rstrip(".")
    return any(host == dom or host.endswith("." + dom) for dom in WAF_403_ALLOWLIST_DOMAINS)


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Redirect handler enforcing HTTPS-only redirects, SSRF checks, and hop bounds."""

    def __init__(
        self,
        *,
        max_redirects: int = 5,
        require_https: bool = True,
        resolve_dns: bool = False,
        resolver: Callable[..., Any] | None = None,
    ) -> None:
        super().__init__()
        self.max_redirects = max_redirects
        self.require_https = require_https
        self.resolve_dns = resolve_dns
        self.resolver = resolver
        self.redirect_urls: list[str] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        if len(self.redirect_urls) >= self.max_redirects:
            raise SecurityValidationError(
                f"Exceeded maximum redirects ({self.max_redirects}) reaching {newurl!r}."
            )
        orig_scheme = urllib.parse.urlsplit(req.full_url).scheme.lower()
        resolved_new = urllib.parse.urljoin(req.full_url, newurl)
        new_scheme = urllib.parse.urlsplit(resolved_new).scheme.lower()
        if orig_scheme == "https" and new_scheme != "https":
            raise SecurityValidationError(
                f"Blocked HTTPS->HTTP downgrade redirect: {req.full_url!r} -> {resolved_new!r}."
            )
        validate_url_target(
            resolved_new,
            require_https=self.require_https,
            resolve_dns=self.resolve_dns,
            resolver=self.resolver,
        )
        self.redirect_urls.append(resolved_new)
        return super().redirect_request(req, fp, code, msg, headers, resolved_new)


def _strip_fragment(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def _extract_title(body_bytes: bytes) -> str | None:
    if not body_bytes:
        return None
    text = body_bytes.decode("utf-8", errors="ignore")
    m = _TITLE_TAG_RE.search(text)
    if not m:
        return None
    raw = re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()
    return raw[:200] if raw else None


def _is_soft_404_title(title: str | None) -> bool:
    if not title:
        return False
    return any(pat.search(title) for pat in _SOFT_404_TITLE_PATTERNS)


def _compute_redirect_warnings(original_url: str, final_url: str) -> tuple[bool, bool]:
    orig = urllib.parse.urlsplit(original_url)
    fin = urllib.parse.urlsplit(final_url)
    orig_host = orig.hostname or ""
    fin_host = fin.hostname or ""
    cross_domain = bool(orig_host and fin_host and registrable_domain(orig_host) != registrable_domain(fin_host))

    orig_segments = [seg for seg in orig.path.split("/") if seg]
    fin_segments = [seg for seg in fin.path.split("/") if seg]
    root_redirect = len(orig_segments) >= 1 and len(fin_segments) == 0
    return cross_domain, root_redirect


def check_url(
    url: str,
    *,
    timeout: float = 12.0,
    max_retries: int = 2,
    backoff_base: float = 0.5,
    max_backoff: float = 4.0,
    require_https: bool = True,
    resolve_dns: bool = True,
    opener_factory: Callable[[SafeRedirectHandler], urllib.request.OpenerDirector] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    resolver: Callable[..., Any] | None = None,
) -> LinkCheckResult:
    """Check a single external URL using HEAD->GET fallback, SSRF/HTTPS validation, and retry backoff."""
    t0 = time.perf_counter()
    try:
        parsed = validate_url_target(
            url,
            require_https=require_https,
            resolve_dns=resolve_dns,
            resolver=resolver,
        )
    except SecurityValidationError as exc:
        return LinkCheckResult(
            url=url,
            final_url=url,
            status_code="BLOCKED",
            ok=False,
            method="VALIDATE",
            latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
            error=str(exc),
        )
    except urllib.error.URLError as exc:
        return LinkCheckResult(
            url=url,
            final_url=url,
            status_code="DNS_ERROR",
            ok=False,
            method="VALIDATE",
            latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
            error=str(exc.reason if hasattr(exc, "reason") else exc),
        )

    request_url = _strip_fragment(url)
    orig_host = parsed.hostname or ""
    allowlisted_waf = is_waf_allowlisted_domain(orig_host)

    def _single_attempt(method: str, user_agent: str) -> tuple[int, str, list[str], bytes]:
        redirect_handler = SafeRedirectHandler(
            max_redirects=5,
            require_https=require_https,
            resolve_dns=resolve_dns,
            resolver=resolver,
        )
        opener = (
            opener_factory(redirect_handler)
            if opener_factory is not None
            else urllib.request.build_opener(redirect_handler)
        )
        headers = {"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}
        if method == "GET":
            headers["Range"] = f"bytes=0-{MAX_BODY_BYTES - 1}"
        req = urllib.request.Request(request_url, headers=headers, method=method)
        with opener.open(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None) or resp.getcode() or 200
            final_u = resp.geturl() or request_url
            snippet = resp.read(MAX_BODY_BYTES) if method == "GET" else b""
            return int(status), final_u, list(redirect_handler.redirect_urls), snippet

    method = "HEAD"
    user_agent = DEFAULT_USER_AGENT
    last_code: int | str = "ERROR"
    last_error: str | None = None
    final_url = request_url
    redirects: list[str] = []
    body_snippet = b""

    attempt = 0
    while attempt <= max_retries:
        try:
            code, final_url, redirects, body_snippet = _single_attempt(method, user_agent)
            last_code = code
            last_error = None
            break
        except SecurityValidationError as exc:
            return LinkCheckResult(
                url=url,
                final_url=final_url,
                status_code="BLOCKED",
                ok=False,
                method=method,
                redirect_count=len(redirects),
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
                error=str(exc),
            )
        except urllib.error.HTTPError as exc:
            # Deterministically close error body socket
            try:
                final_url = exc.geturl() or final_url
            finally:
                exc.close()
            code = int(exc.code)
            last_code = code
            last_error = f"HTTP {code}: {exc.reason}"

            if method == "HEAD" and code in HEAD_FALLBACK_CODES:
                method = "GET"
                continue

            if code == 403 and allowlisted_waf and user_agent == DEFAULT_USER_AGENT:
                user_agent = BROWSER_FALLBACK_UA
                method = "GET"
                continue

            if code in TRANSIENT_HTTP_CODES and attempt < max_retries:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                delay = min(backoff_base * (2**attempt), max_backoff)
                if retry_after and retry_after.isdigit():
                    delay = min(float(int(retry_after)), max_backoff)
                sleep_fn(delay)
                attempt += 1
                continue
            break
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            # Check if wrapped SecurityValidationError
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, SecurityValidationError):
                return LinkCheckResult(
                    url=url,
                    final_url=final_url,
                    status_code="BLOCKED",
                    ok=False,
                    method=method,
                    latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
                    error=str(reason),
                )
            last_code = "TIMEOUT" if isinstance(exc, (TimeoutError, socket.timeout)) else "URL_ERROR"
            last_error = str(reason)
            if attempt < max_retries:
                delay = min(backoff_base * (2**attempt), max_backoff)
                sleep_fn(delay)
                attempt += 1
                continue
            break

    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    title = _extract_title(body_snippet)
    soft_404 = _is_soft_404_title(title)
    cross_domain, root_redirect = _compute_redirect_warnings(request_url, final_url)

    waf_used = False
    if isinstance(last_code, int) and 200 <= last_code < 300:
        ok = not soft_404
        if soft_404:
            last_error = f"Soft-404 detected in page title: {title!r}"
    elif last_code == 403 and allowlisted_waf:
        ok = True
        waf_used = True
        last_error = None
    else:
        ok = False

    return LinkCheckResult(
        url=url,
        final_url=final_url,
        status_code=last_code,
        ok=ok,
        method=method,
        redirect_count=len(redirects),
        cross_domain_redirect=cross_domain,
        root_redirect_warning=root_redirect,
        soft_404_warning=soft_404,
        waf_allowlisted=waf_used,
        page_title=title,
        latency_ms=latency_ms,
        error=last_error,
    )


def check_urls_concurrent(
    urls: list[str],
    *,
    max_workers: int = 8,
    per_host_limit: int = 2,
    timeout: float = 12.0,
    max_retries: int = 2,
    backoff_base: float = 0.5,
    require_https: bool = True,
    resolve_dns: bool = True,
    opener_factory: Callable[[SafeRedirectHandler], urllib.request.OpenerDirector] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    resolver: Callable[..., Any] | None = None,
) -> list[LinkCheckResult]:
    """Check unique URLs in parallel with per-host concurrency semaphores and sorted output."""
    unique_urls = sorted(set(urls))
    if not unique_urls:
        return []

    host_semaphores: dict[str, threading.Semaphore] = {}
    lock = threading.Lock()

    def _get_sem(url: str) -> threading.Semaphore:
        host = (urllib.parse.urlsplit(url).hostname or "").lower()
        with lock:
            sem = host_semaphores.get(host)
            if sem is None:
                sem = threading.Semaphore(max(1, per_host_limit))
                host_semaphores[host] = sem
            return sem

    def _worker(target_url: str) -> LinkCheckResult:
        sem = _get_sem(target_url)
        with sem:
            return check_url(
                target_url,
                timeout=timeout,
                max_retries=max_retries,
                backoff_base=backoff_base,
                require_https=require_https,
                resolve_dns=resolve_dns,
                opener_factory=opener_factory,
                sleep_fn=sleep_fn,
                resolver=resolver,
            )

    workers = max(1, min(max_workers, len(unique_urls)))
    results_by_url: dict[str, LinkCheckResult] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(_worker, u): u for u in unique_urls}
        for fut in concurrent.futures.as_completed(future_map):
            u = future_map[fut]
            results_by_url[u] = fut.result()

    return [results_by_url[u] for u in unique_urls]


def audit_markdown_files(
    repo_root: Path,
    *,
    markdown_files: list[Path] | None = None,
    offline: bool = False,
    max_workers: int = 8,
    per_host_limit: int = 2,
    timeout: float = 12.0,
    max_retries: int = 2,
    backoff_base: float = 0.5,
    require_https: bool = True,
    resolve_dns: bool = True,
    opener_factory: Callable[[SafeRedirectHandler], urllib.request.OpenerDirector] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    resolver: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Audit all Markdown files for unsafe schemes, broken local links/anchors, and external URL health."""
    repo_root = repo_root.resolve()
    files = markdown_files if markdown_files is not None else discover_markdown_files(repo_root)

    external_urls: set[str] = set()
    local_results: list[LocalLinkResult] = []
    unsafe_results: list[LinkCheckResult] = []
    seen_local: set[tuple[str, str]] = set()

    for md_path in files:
        resolved_md = md_path.resolve()
        rel_md = str(resolved_md.relative_to(repo_root)).replace("\\", "/")
        text = resolved_md.read_text(encoding="utf-8")
        for link in extract_links(text, source_file=rel_md):
            if link.kind == "external":
                external_urls.add(link.target)
            elif link.kind == "unsafe_scheme":
                unsafe_results.append(
                    LinkCheckResult(
                        url=link.target,
                        final_url=link.target,
                        status_code="UNSAFE_SCHEME",
                        ok=False,
                        method="PARSE",
                        error=f"Forbidden URL scheme in {rel_md}: {link.target!r}",
                    )
                )
            elif link.kind == "local":
                key = (rel_md, link.target)
                if key not in seen_local:
                    seen_local.add(key)
                    local_results.append(check_local_link(link.target, resolved_md, repo_root))

    sorted_urls = sorted(external_urls)
    if offline:
        ext_results: list[LinkCheckResult] = []
        for u in sorted_urls:
            try:
                validate_url_target(u, require_https=require_https, resolve_dns=False)
                ext_results.append(
                    LinkCheckResult(
                        url=u,
                        final_url=u,
                        status_code="OFFLINE_VALID",
                        ok=True,
                        method="OFFLINE",
                    )
                )
            except SecurityValidationError as exc:
                ext_results.append(
                    LinkCheckResult(
                        url=u,
                        final_url=u,
                        status_code="BLOCKED",
                        ok=False,
                        method="OFFLINE",
                        error=str(exc),
                    )
                )
    else:
        ext_results = check_urls_concurrent(
            sorted_urls,
            max_workers=max_workers,
            per_host_limit=per_host_limit,
            timeout=timeout,
            max_retries=max_retries,
            backoff_base=backoff_base,
            require_https=require_https,
            resolve_dns=resolve_dns,
            opener_factory=opener_factory,
            sleep_fn=sleep_fn,
            resolver=resolver,
        )

    all_http_results = unsafe_results + ext_results
    broken_external = sum(1 for r in all_http_results if not r.ok)
    broken_local = sum(1 for r in local_results if not r.ok)
    warning_count = sum(
        1
        for r in all_http_results
        if r.cross_domain_redirect or r.root_redirect_warning or r.soft_404_warning
    )

    return {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "offline": offline,
        "scanned_files": [str(f.resolve().relative_to(repo_root)).replace("\\", "/") for f in files],
        "total_external_links": len(all_http_results),
        "total_local_links": len(local_results),
        "broken_external_count": broken_external,
        "broken_local_count": broken_local,
        "broken_total": broken_external + broken_local,
        "warning_count": warning_count,
        "external_results": [asdict(r) for r in all_http_results],
        "local_results": [asdict(r) for r in local_results],
    }


def write_link_report(report: dict[str, Any], output_path: str | Path) -> Path:
    """Persist structured JSON link-audit report, creating parent directories if needed."""
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out
