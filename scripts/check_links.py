"""Audit external HTTPS links and local Markdown paths across README.md and docs/*.md."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab_atlas.linkcheck import (  # noqa: E402
    DEFAULT_USER_AGENT,
    WAF_403_ALLOWLIST_DOMAINS,
    LinkCheckResult,
    LocalLinkResult,
    SafeRedirectHandler,
    SecurityValidationError,
    audit_markdown_files,
    check_local_link,
    check_url,
    check_urls_concurrent,
    discover_markdown_files,
    extract_links,
    extract_urls,
    is_waf_allowlisted_domain,
    validate_url_target,
    write_link_report,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify external HTTPS URLs and local relative links across Markdown files."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="Repository root directory (defaults to parent of scripts/).",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        type=Path,
        default=None,
        help="Optional explicit Markdown file paths to scan.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Validate link extraction, URL schemes/SSRF rules, and local files without network I/O.",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Return exit code 0 even when broken links are detected.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Write structured JSON link-status report to this path.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Maximum worker threads for concurrent URL checks.",
    )
    parser.add_argument(
        "--per-host-limit",
        type=int,
        default=2,
        help="Maximum concurrent requests to any single hostname.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=12.0,
        help="Per-request socket timeout in seconds.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Retries on transient 429/502/503/504 or timeout errors.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    md_files = [p.resolve() for p in args.files] if args.files else None

    report = audit_markdown_files(
        repo_root,
        markdown_files=md_files,
        offline=args.offline,
        max_workers=args.max_workers,
        per_host_limit=args.per_host_limit,
        timeout=args.timeout,
        max_retries=args.max_retries,
    )

    for loc in report["local_results"]:
        if not loc["ok"]:
            print(f"LOCAL_BROKEN {loc['source_file']} -> {loc['target']}: {loc['error']}")

    for res in report["external_results"]:
        status_label = (
            f"{res['status_code']} (WAF allowlisted)"
            if res["waf_allowlisted"]
            else str(res["status_code"])
        )
        notes: list[str] = []
        if res["cross_domain_redirect"]:
            notes.append(f"cross-domain->{res['final_url']}")
        if res["root_redirect_warning"]:
            notes.append(f"subpath->root({res['final_url']})")
        if res["soft_404_warning"]:
            notes.append("soft-404")
        suffix = f" [{' | '.join(notes)}]" if notes else ""
        print(f"{status_label} {res['url']}{suffix}")

    bad = report["broken_total"]
    print(
        f"{report['total_external_links']} links, {bad} not reachable "
        f"(external_broken={report['broken_external_count']}, "
        f"local_broken={report['broken_local_count']}, "
        f"warnings={report['warning_count']})"
    )

    if args.json_out is not None:
        out_path = write_link_report(report, args.json_out)
        print(f"Saved JSON report to {out_path}")

    return 0 if (bad == 0 or args.warn_only) else 1


__all__ = [
    "DEFAULT_USER_AGENT",
    "ROOT",
    "WAF_403_ALLOWLIST_DOMAINS",
    "LinkCheckResult",
    "LocalLinkResult",
    "SafeRedirectHandler",
    "SecurityValidationError",
    "audit_markdown_files",
    "check_local_link",
    "check_url",
    "check_urls_concurrent",
    "discover_markdown_files",
    "extract_links",
    "extract_urls",
    "is_waf_allowlisted_domain",
    "main",
    "validate_url_target",
    "write_link_report",
]


if __name__ == "__main__":
    sys.exit(main())
