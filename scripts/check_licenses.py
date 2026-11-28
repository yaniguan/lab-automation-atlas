"""Audit catalog SPDX declarations against Hugging Face, GitHub, Zenodo, and Dataverse APIs.

Compares `atlas.json` `spdx_license` declarations against:
- Hugging Face Hub `cardData.license` (`/api/datasets/<huggingface_id>`),
- GitHub license API (`/repos/<owner>/<repo>/license`) for entries citing GitHub `license_evidence`,
- Zenodo REST API `metadata.license.id` (`/api/records/<id>`) for entries citing Zenodo records,
- Harvard Dataverse API `latestVersion.license` for entries citing `10.7910/DVN/...` DOIs.

Designed for weekly scheduled CI (`links.yml` `license-audit` job) and offline unit testing.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab_atlas.catalog import load_catalog  # noqa: E402
from lab_atlas.linkcheck import DEFAULT_USER_AGENT, validate_url_target  # noqa: E402

_ZENODO_RECORD_RE = re.compile(
    r"(?:zenodo\.org/records/|10\.5281/zenodo\.)([0-9]+)",
    re.IGNORECASE,
)
_GITHUB_EVIDENCE_RE = re.compile(
    r"^https://github\.com/([^/]+)/([^/#?]+)(?:/(.*))?$",
    re.IGNORECASE,
)
_DATAVERSE_DOI_RE = re.compile(r"(10\.7910/DVN/[A-Za-z0-9]+)", re.IGNORECASE)

# Normalize legacy SPDX 2.0 / HF / Zenodo identifiers to canonical lower-case SPDX keys.
_SPDX_EQUIV_ALIASES: dict[str, str] = {
    "agpl-3.0": "agpl-3.0-only",
    "gpl-2.0": "gpl-2.0-only",
    "gpl-3.0": "gpl-3.0-only",
    "lgpl-2.1": "lgpl-2.1-only",
    "lgpl-3.0": "lgpl-3.0-only",
    "cc0": "cc0-1.0",
    "cc-by": "cc-by-4.0",
}


@dataclass
class LicenseCheckRecord:
    entry_id: str
    source: str  # "huggingface", "github", "zenodo", "dataverse"
    target: str
    catalog_spdx: str
    upstream_spdx: str | None
    status: str  # "match", "mismatch", "unasserted_upstream", "custom_licenseref", "error"
    ok: bool
    detail: str | None = None


def normalize_spdx_token(token: str) -> str:
    cleaned = token.strip().lower()
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    return _SPDX_EQUIV_ALIASES.get(cleaned, cleaned)


def _infer_spdx_from_license_text(raw_b64: object) -> list[str]:
    """Detect SPDX identifiers from Base64-encoded GitHub LICENSE/README content when licensee returns NOASSERTION."""
    if not isinstance(raw_b64, str) or not raw_b64.strip():
        return []
    try:
        text = base64.b64decode(raw_b64).decode("utf-8", errors="ignore")
    except Exception:
        return []
    low = text.lower()
    detected: list[str] = []
    if (
        "permission is hereby granted, free of charge" in low
        or "mit license" in low
        or bool(re.search(r"licenses?[^\n]{0,80}\bmit\b", low))
    ):
        detected.append("MIT")
    if (
        ("apache license" in low and "version 2.0" in low)
        or "apache-2.0" in low
        or "apache 2.0" in low
    ):
        detected.append("Apache-2.0")
    if "creative commons attribution-noncommercial 4.0" in low or "cc-by-nc-4.0" in low or "cc by-nc 4.0" in low:
        detected.append("CC-BY-NC-4.0")
    if "creative commons attribution-sharealike 4.0" in low or "cc-by-sa-4.0" in low or "cc by-sa 4.0" in low:
        detected.append("CC-BY-SA-4.0")
    if "creative commons attribution 4.0" in low or "cc-by-4.0" in low or "cc by 4.0" in low:
        detected.append("CC-BY-4.0")
    if "cc0 1.0" in low:
        detected.append("CC0-1.0")
    return detected


def spdx_matches_upstream(catalog_spdx: str, upstream_raw: str | list[str] | None) -> tuple[bool, str]:
    """Compare catalog SPDX declaration against upstream API string/list."""
    cat_norm = normalize_spdx_token(catalog_spdx)
    if upstream_raw is None:
        if cat_norm == "noassertion":
            return True, "match"
        return True, "unasserted_upstream"

    candidates = [upstream_raw] if isinstance(upstream_raw, str) else [str(x) for x in upstream_raw]
    norm_cands = [normalize_spdx_token(c) for c in candidates if str(c).strip()]
    if not norm_cands or all(c in ("other", "unknown") for c in norm_cands):
        return True, "unasserted_upstream"

    if all(c == "noassertion" for c in norm_cands):
        if cat_norm == "noassertion" or cat_norm.startswith("licenseref-") or cat_norm.startswith("cc-by"):
            return True, "match" if cat_norm == "noassertion" else "unasserted_upstream"

    if cat_norm in norm_cands:
        return True, "match"

    # Support compound OR / AND expressions where upstream reports constituent SPDX IDs
    or_parts = [normalize_spdx_token(p) for p in catalog_spdx.split(" OR ")]
    if len(or_parts) > 1 and any(p in norm_cands for p in or_parts):
        return True, "match"

    and_parts = [normalize_spdx_token(p) for p in catalog_spdx.split(" AND ")]
    if len(and_parts) > 1 and set(and_parts).issubset(set(norm_cands)):
        return True, "match"

    return False, "mismatch"


def default_json_fetcher(url: str, headers: dict[str, str] | None = None, timeout: float = 15.0) -> Any:
    """Fetch JSON over SSRF-validated HTTPS."""
    validate_url_target(url, require_https=True, resolve_dns=True)
    req_headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json",
        **(headers or {}),
    }
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_catalog_licenses(
    catalog: dict[str, Any],
    *,
    fetcher: Callable[[str, dict[str, str] | None], Any] | None = None,
    github_token: str | None = None,
    offline: bool = False,
) -> dict[str, Any]:
    """Audit catalog entries against Hugging Face, GitHub, Zenodo, and Dataverse license APIs."""
    fetch = fetcher or (lambda u, h=None: default_json_fetcher(u, headers=h))
    token = github_token if github_token is not None else os.environ.get("GITHUB_TOKEN")
    gh_headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if token:
        gh_headers["Authorization"] = f"Bearer {token}"

    records: list[LicenseCheckRecord] = []

    for entry in catalog["entries"]:
        eid = entry["id"]
        cat_spdx = entry["spdx_license"]
        ev_url = entry["license_evidence"]

        # 1. Hugging Face cardData.license check
        hf_id = entry.get("huggingface_id")
        if isinstance(hf_id, str) and hf_id.strip():
            api_url = f"https://huggingface.co/api/datasets/{hf_id.strip()}"
            if offline:
                validate_url_target(api_url, require_https=True, resolve_dns=False)
                records.append(
                    LicenseCheckRecord(
                        entry_id=eid,
                        source="huggingface",
                        target=hf_id,
                        catalog_spdx=cat_spdx,
                        upstream_spdx=None,
                        status="offline_valid",
                        ok=True,
                    )
                )
            else:
                try:
                    data = fetch(api_url, None)
                    card = data.get("cardData") if isinstance(data, dict) else None
                    raw_lic = card.get("license") if isinstance(card, dict) else None
                    ok, status = spdx_matches_upstream(cat_spdx, raw_lic)
                    records.append(
                        LicenseCheckRecord(
                            entry_id=eid,
                            source="huggingface",
                            target=hf_id,
                            catalog_spdx=cat_spdx,
                            upstream_spdx=json.dumps(raw_lic) if isinstance(raw_lic, list) else raw_lic,
                            status=status,
                            ok=ok,
                        )
                    )
                except Exception as exc:
                    records.append(
                        LicenseCheckRecord(
                            entry_id=eid,
                            source="huggingface",
                            target=hf_id,
                            catalog_spdx=cat_spdx,
                            upstream_spdx=None,
                            status="error",
                            ok=False,
                            detail=str(exc),
                        )
                    )

        # 2. Zenodo metadata.license check when Zenodo is cited in license_evidence or doi
        zenodo_ids: list[str] = []
        for candidate_text in (ev_url, entry.get("doi") or ""):
            for m_z in _ZENODO_RECORD_RE.finditer(candidate_text):
                zid = m_z.group(1)
                if zid not in zenodo_ids:
                    zenodo_ids.append(zid)
        for zid in zenodo_ids:
            z_url = f"https://zenodo.org/api/records/{zid}"
            if offline:
                validate_url_target(z_url, require_https=True, resolve_dns=False)
                records.append(
                    LicenseCheckRecord(
                        entry_id=eid,
                        source="zenodo",
                        target=zid,
                        catalog_spdx=cat_spdx,
                        upstream_spdx=None,
                        status="offline_valid",
                        ok=True,
                    )
                )
            else:
                try:
                    zdata = fetch(z_url, None)
                    meta = zdata.get("metadata") if isinstance(zdata, dict) else None
                    lic_obj = meta.get("license") if isinstance(meta, dict) else None
                    z_lic = lic_obj.get("id") if isinstance(lic_obj, dict) else (
                        str(lic_obj) if lic_obj is not None else None
                    )
                    ok, status = spdx_matches_upstream(cat_spdx, z_lic)
                    records.append(
                        LicenseCheckRecord(
                            entry_id=eid,
                            source="zenodo",
                            target=zid,
                            catalog_spdx=cat_spdx,
                            upstream_spdx=z_lic,
                            status=status,
                            ok=ok,
                        )
                    )
                except Exception as exc:
                    records.append(
                        LicenseCheckRecord(
                            entry_id=eid,
                            source="zenodo",
                            target=zid,
                            catalog_spdx=cat_spdx,
                            upstream_spdx=None,
                            status="error",
                            ok=False,
                            detail=str(exc),
                        )
                    )

        # 3. Harvard Dataverse check when Dataverse DOI is cited as license_evidence
        m_dv = _DATAVERSE_DOI_RE.search(ev_url)
        if m_dv:
            dv_doi = m_dv.group(1)
            dv_url = (
                f"https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:{dv_doi}"
            )
            if offline:
                validate_url_target(dv_url, require_https=True, resolve_dns=False)
                records.append(
                    LicenseCheckRecord(
                        entry_id=eid,
                        source="dataverse",
                        target=dv_doi,
                        catalog_spdx=cat_spdx,
                        upstream_spdx=None,
                        status="offline_valid",
                        ok=True,
                    )
                )
            else:
                try:
                    dv_data = fetch(dv_url, None)
                    latest = dv_data.get("data", {}).get("latestVersion", {})
                    lic_block = latest.get("license")
                    dv_lic = (
                        lic_block.get("rightsIdentifier") or lic_block.get("name")
                        if isinstance(lic_block, dict)
                        else None
                    )
                    ok, status = spdx_matches_upstream(cat_spdx, dv_lic)
                    records.append(
                        LicenseCheckRecord(
                            entry_id=eid,
                            source="dataverse",
                            target=dv_doi,
                            catalog_spdx=cat_spdx,
                            upstream_spdx=dv_lic,
                            status=status,
                            ok=ok,
                        )
                    )
                except Exception as exc:
                    records.append(
                        LicenseCheckRecord(
                            entry_id=eid,
                            source="dataverse",
                            target=dv_doi,
                            catalog_spdx=cat_spdx,
                            upstream_spdx=None,
                            status="error",
                            ok=False,
                            detail=str(exc),
                        )
                    )

        # 4. GitHub license API check when license_evidence cites a GitHub repository/LICENSE
        m_gh = _GITHUB_EVIDENCE_RE.match(ev_url)
        if m_gh:
            owner, repo, subpath = m_gh.group(1), m_gh.group(2), m_gh.group(3) or ""
            if repo.lower().endswith(".git"):
                repo = repo[:-4]
            owner_repo = f"{owner}/{repo}"
            gh_api_url = f"https://api.github.com/repos/{owner_repo}/license"

            # Custom non-code EULA PDFs hosted in a GitHub repo (e.g. FineBio_License_Agreement.pdf)
            # govern the dataset rather than the repo's root helper-script LICENSE file.
            if cat_spdx.startswith("LicenseRef-") and subpath.lower().endswith(".pdf"):
                records.append(
                    LicenseCheckRecord(
                        entry_id=eid,
                        source="github",
                        target=owner_repo,
                        catalog_spdx=cat_spdx,
                        upstream_spdx=None,
                        status="custom_licenseref",
                        ok=True,
                        detail=f"Custom EULA document cited: {subpath}",
                    )
                )
                continue

            if offline:
                validate_url_target(gh_api_url, require_https=True, resolve_dns=False)
                records.append(
                    LicenseCheckRecord(
                        entry_id=eid,
                        source="github",
                        target=owner_repo,
                        catalog_spdx=cat_spdx,
                        upstream_spdx=None,
                        status="offline_valid",
                        ok=True,
                    )
                )
                continue

            try:
                gdata = fetch(gh_api_url, gh_headers)
                lic_info = gdata.get("license") if isinstance(gdata, dict) else None
                gh_spdx = lic_info.get("spdx_id") if isinstance(lic_info, dict) else None
                # Legacy software entries explicitly marked NOASSERTION (osi_approved=False) remain conservative
                if entry["category"] == "software" and cat_spdx == "NOASSERTION" and not entry["osi_approved"]:
                    records.append(
                        LicenseCheckRecord(
                            entry_id=eid,
                            source="github",
                            target=owner_repo,
                            catalog_spdx=cat_spdx,
                            upstream_spdx=gh_spdx,
                            status="conservative_noassertion",
                            ok=True,
                            detail="Catalog retains conservative NOASSERTION posture for legacy software entry.",
                        )
                    )
                    continue
                effective_gh: str | list[str] | None = gh_spdx
                if gh_spdx in (None, "NOASSERTION") and isinstance(gdata, dict):
                    inferred = _infer_spdx_from_license_text(gdata.get("content"))
                    if inferred:
                        effective_gh = inferred[0] if len(inferred) == 1 else inferred
                ok, status = spdx_matches_upstream(cat_spdx, effective_gh)
                records.append(
                    LicenseCheckRecord(
                        entry_id=eid,
                        source="github",
                        target=owner_repo,
                        catalog_spdx=cat_spdx,
                        upstream_spdx=(
                            json.dumps(effective_gh)
                            if isinstance(effective_gh, list)
                            else effective_gh
                        ),
                        status=status,
                        ok=ok,
                    )
                )
            except urllib.error.HTTPError as exc:
                exc.close()
                if exc.code == 404:
                    # Fallback to README license check if repo declares license in README rather than root LICENSE
                    inferred_readme: list[str] = []
                    try:
                        rdata = fetch(f"https://api.github.com/repos/{owner_repo}/readme", gh_headers)
                        if isinstance(rdata, dict):
                            inferred_readme = _infer_spdx_from_license_text(rdata.get("content"))
                    except Exception:
                        inferred_readme = []
                    if inferred_readme:
                        ok, status = spdx_matches_upstream(cat_spdx, inferred_readme)
                        records.append(
                            LicenseCheckRecord(
                                entry_id=eid,
                                source="github",
                                target=owner_repo,
                                catalog_spdx=cat_spdx,
                                upstream_spdx=json.dumps(inferred_readme),
                                status=status,
                                ok=ok,
                                detail="Inferred from upstream README (no root LICENSE file).",
                            )
                        )
                    else:
                        ok = normalize_spdx_token(cat_spdx) == "noassertion" or cat_spdx.startswith("LicenseRef-")
                        records.append(
                            LicenseCheckRecord(
                                entry_id=eid,
                                source="github",
                                target=owner_repo,
                                catalog_spdx=cat_spdx,
                                upstream_spdx=None,
                                status="match" if ok else "mismatch",
                                ok=ok,
                                detail="No LICENSE file detected by GitHub API (HTTP 404).",
                            )
                        )
                else:
                    records.append(
                        LicenseCheckRecord(
                            entry_id=eid,
                            source="github",
                            target=owner_repo,
                            catalog_spdx=cat_spdx,
                            upstream_spdx=None,
                            status="error",
                            ok=False,
                            detail=f"HTTP {exc.code}: {exc.reason}",
                        )
                    )
            except Exception as exc:
                records.append(
                    LicenseCheckRecord(
                        entry_id=eid,
                        source="github",
                        target=owner_repo,
                        catalog_spdx=cat_spdx,
                        upstream_spdx=None,
                        status="error",
                        ok=False,
                        detail=str(exc),
                    )
                )

    mismatches = [r for r in records if r.status == "mismatch"]
    errors = [r for r in records if r.status == "error"]
    return {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "offline": offline,
        "total_checks": len(records),
        "mismatch_count": len(mismatches),
        "error_count": len(errors),
        "ok": len(mismatches) == 0 and len(errors) == 0,
        "results": [asdict(r) for r in records],
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare catalog SPDX declarations against Hugging Face, GitHub, Zenodo, and Dataverse APIs."
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=ROOT / "atlas.json",
        help="Path to atlas.json catalog.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Write structured JSON license audit report to this path.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Validate API endpoint URLs offline without making network calls.",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Exit 0 even if license mismatches or API errors occur.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    catalog = load_catalog(args.catalog, validate=True)
    report = check_catalog_licenses(catalog, offline=args.offline)

    for rec in report["results"]:
        flag = "OK" if rec["ok"] else "FAIL"
        print(
            f"{flag:4s} [{rec['source']:11s}] {rec['entry_id']:32s} "
            f"catalog={rec['catalog_spdx']:22s} upstream={rec['upstream_spdx']!r} ({rec['status']})"
        )

    print(
        f"Summary: {report['total_checks']} upstream license checks, "
        f"{report['mismatch_count']} mismatch(es), {report['error_count']} error(s)."
    )

    if args.json_out is not None:
        out_path = args.json_out.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Saved license report to {out_path}")

    if not report["ok"] and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
