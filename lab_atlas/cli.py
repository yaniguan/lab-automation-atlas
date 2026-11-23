"""Command-line interface (`lab-atlas`) for querying, validating, exporting, and link-checking."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .catalog import (
    ALLOWED_CATEGORIES,
    ALLOWED_PURPOSES,
    ALLOWED_STATUSES,
    REPO_ROOT,
    build_compatibility_matrix,
    dump_catalog_yaml,
    filter_entries,
    load_catalog,
    resolve_catalog_path,
    validate_catalog,
)
from .linkcheck import audit_markdown_files, write_link_report
from .render import check_readme_sync, sync_readme


def _cmd_list(args: argparse.Namespace) -> int:
    catalog = load_catalog(args.catalog)
    commercial_ok: bool | None = None
    if args.commercial_ok:
        commercial_ok = True
    elif args.non_commercial_only:
        commercial_ok = False

    has_sim: bool | None = True if args.has_simulator else None
    osi_only: bool | None = True if args.osi_only else None

    matched = filter_entries(
        catalog["entries"],
        category=args.category,
        layer=args.layer,
        spdx_license=args.license,
        commercial_ok=commercial_ok,
        osi_approved=osi_only,
        status=args.status,
        hardware=args.hardware,
        protocol_format=args.protocol_format,
        allowed_purpose=args.purpose,
        has_simulator=has_sim,
        query=args.query,
    )

    if args.json:
        print(json.dumps(matched, indent=2, ensure_ascii=False))
        return 0

    if not matched:
        print("No matching entries.")
        return 0

    header = f"{'ID':<26} {'CATEGORY':<27} {'STATUS':<14} {'SPDX LICENSE':<24} {'COMM':<5}"
    print(header)
    print("-" * len(header))
    for e in matched:
        comm = "yes" if e["commercial_use_ok"] else "no"
        print(
            f"{e['id']:<26} {e['category']:<27} {e['maintenance_status']:<14} "
            f"{e['spdx_license'][:24]:<24} {comm:<5}"
        )
    print(f"\n{len(matched)} entry/entries matched.")
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    catalog = load_catalog(args.catalog)
    for entry in catalog["entries"]:
        if entry["id"] == args.entry_id:
            if args.json:
                print(json.dumps(entry, indent=2, ensure_ascii=False))
            else:
                print(dump_catalog_yaml(entry))
            return 0
    print(f"Entry {args.entry_id!r} not found.", file=sys.stderr)
    return 1


def _cmd_compatibility(args: argparse.Namespace) -> int:
    catalog = load_catalog(args.catalog)
    rows = build_compatibility_matrix(catalog)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0
    for row in rows:
        print(f"- {row['hardware_platform']}")
        print(f"    SDKs/Drivers : {', '.join(row['open_sdks_and_drivers']) or 'none'}")
        print(f"    Protocol IRs : {', '.join(row['protocol_irs']) or 'none'}")
        print(f"    Simulators   : {', '.join(row['offline_simulators']) or 'none'}")
        print(f"    Auto-Lab     : {', '.join(row['autolab_integrations']) or 'none'}")
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    catalog = load_catalog(args.catalog)
    if args.format == "json":
        text = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    else:
        text = dump_catalog_yaml(catalog) + "\n"
    if args.output:
        out = Path(args.output).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Exported {args.format.upper()} catalog to {out}")
    else:
        sys.stdout.write(text)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    cat_path = resolve_catalog_path(args.catalog)
    raw = json.loads(cat_path.read_text(encoding="utf-8"))
    errors = validate_catalog(raw)
    if errors:
        for err in errors:
            print(f"SCHEMA ERROR: {err}", file=sys.stderr)
        return 1

    readme_path = Path(args.readme).resolve() if args.readme else (REPO_ROOT / "README.md")
    if readme_path.is_file() and not args.skip_readme_sync:
        if not check_readme_sync(readme_path, raw):
            print(
                f"SYNC ERROR: {readme_path} is out of sync with {cat_path}. "
                "Run `python scripts/sync_catalog.py` or `lab-atlas sync-readme`.",
                file=sys.stderr,
            )
            return 1

    print(f"OK: {len(raw['entries'])} catalog entries validated and synchronized.")
    return 0


def _cmd_sync_readme(args: argparse.Namespace) -> int:
    catalog = load_catalog(args.catalog)
    readme_path = Path(args.readme).resolve() if args.readme else (REPO_ROOT / "README.md")
    if args.check:
        if check_readme_sync(readme_path, catalog):
            print("README.md is byte-for-byte synchronized with atlas.json.")
            return 0
        print("README.md is out of sync with atlas.json.", file=sys.stderr)
        return 1
    changed = sync_readme(readme_path, catalog)
    status = "Updated" if changed else "Already synchronized"
    print(f"{status}: {readme_path}")
    return 0


def _cmd_check_links(args: argparse.Namespace) -> int:
    root = Path(args.repo_root).resolve() if args.repo_root else REPO_ROOT
    md_files = [Path(p).resolve() for p in args.files] if args.files else None
    report = audit_markdown_files(
        root,
        markdown_files=md_files,
        offline=args.offline,
        max_workers=args.max_workers,
        per_host_limit=args.per_host_limit,
        timeout=args.timeout,
        max_retries=args.max_retries,
    )

    for res in report["local_results"]:
        if not res["ok"]:
            print(f"LOCAL_BROKEN {res['source_file']} -> {res['target']} ({res['error']})")

    for res in report["external_results"]:
        status_str = (
            f"{res['status_code']} (WAF allowlisted)"
            if res["waf_allowlisted"]
            else str(res["status_code"])
        )
        flags: list[str] = []
        if res["cross_domain_redirect"]:
            flags.append(f"cross-domain->{res['final_url']}")
        if res["root_redirect_warning"]:
            flags.append(f"subpath->root({res['final_url']})")
        if res["soft_404_warning"]:
            flags.append("soft-404")
        suffix = f" [{' | '.join(flags)}]" if flags else ""
        print(f"{status_str} {res['url']}{suffix}")

    total_ext = report["total_external_links"]
    bad_ext = report["broken_external_count"]
    total_loc = report["total_local_links"]
    bad_loc = report["broken_local_count"]
    print(
        f"{total_ext} external links ({bad_ext} broken), "
        f"{total_loc} local links ({bad_loc} broken), "
        f"{report['warning_count']} redirect/soft-404 warning(s)"
    )

    if args.json_out:
        out_path = write_link_report(report, args.json_out)
        print(f"Wrote link report to {out_path}")

    if report["broken_total"] > 0 and not args.warn_only:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lab-atlas",
        description="Query, validate, export, and audit the lab-automation-atlas registry.",
    )
    parser.add_argument("--catalog", default=None, help="Optional path to atlas.json")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="Filter and list catalog entries")
    p_list.add_argument("--category", choices=ALLOWED_CATEGORIES)
    p_list.add_argument("--layer", help="Auto-Lab layer tag (Hub, L0..L6)")
    p_list.add_argument("--license", help="Substring match on SPDX license")
    p_list.add_argument("--commercial-ok", action="store_true", help="Only commercial-use-safe entries")
    p_list.add_argument("--non-commercial-only", action="store_true", help="Only non-commercial entries")
    p_list.add_argument("--osi-only", action="store_true", help="Only OSI-approved open-source licenses")
    p_list.add_argument("--status", choices=ALLOWED_STATUSES)
    p_list.add_argument("--hardware", help="Substring match on supported_hardware")
    p_list.add_argument("--protocol-format", help="Substring match on protocol_formats")
    p_list.add_argument("--purpose", choices=ALLOWED_PURPOSES, help="Filter by allowed_purposes")
    p_list.add_argument("--has-simulator", action="store_true", help="Only tools with offline simulator")
    p_list.add_argument("--query", "-q", help="Free-text keyword search")
    p_list.add_argument("--json", action="store_true", help="Output JSON array")
    p_list.set_defaults(func=_cmd_list)

    p_ins = sub.add_parser("inspect", help="Show full metadata for one entry by ID")
    p_ins.add_argument("entry_id", help="Catalog entry ID")
    p_ins.add_argument("--json", action="store_true", help="Output JSON object")
    p_ins.set_defaults(func=_cmd_inspect)

    p_comp = sub.add_parser("compatibility", help="Show hardware-to-SDK-to-IR compatibility matrix")
    p_comp.add_argument("--json", action="store_true", help="Output JSON array")
    p_comp.set_defaults(func=_cmd_compatibility)

    p_exp = sub.add_parser("export", help="Export full catalog in JSON or YAML format")
    p_exp.add_argument("--format", choices=("json", "yaml"), default="json")
    p_exp.add_argument("--output", "-o", help="Optional output file path")
    p_exp.set_defaults(func=_cmd_export)

    p_val = sub.add_parser("validate", help="Validate atlas.json schema and README.md sync")
    p_val.add_argument("--readme", default=None, help="Path to README.md")
    p_val.add_argument("--skip-readme-sync", action="store_true")
    p_val.set_defaults(func=_cmd_validate)

    p_sync = sub.add_parser("sync-readme", help="Synchronize README.md tables from atlas.json")
    p_sync.add_argument("--readme", default=None, help="Path to README.md")
    p_sync.add_argument("--check", action="store_true", help="Exit non-zero if out of sync")
    p_sync.set_defaults(func=_cmd_sync_readme)

    p_chk = sub.add_parser("check-links", help="Audit external and local Markdown links")
    p_chk.add_argument("--repo-root", default=None, help="Repository root directory")
    p_chk.add_argument("--files", nargs="*", help="Specific Markdown files to scan")
    p_chk.add_argument("--offline", action="store_true", help="Validate syntax, schemes, and local links offline")
    p_chk.add_argument("--warn-only", action="store_true", help="Exit 0 even when broken links are detected")
    p_chk.add_argument("--json-out", default=None, help="Write JSON link status report to path")
    p_chk.add_argument("--max-workers", type=int, default=8)
    p_chk.add_argument("--per-host-limit", type=int, default=2)
    p_chk.add_argument("--timeout", type=float, default=12.0)
    p_chk.add_argument("--max-retries", type=int, default=2)
    p_chk.set_defaults(func=_cmd_check_links)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
