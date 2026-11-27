"""Auto-Lab 15-repository wire node (autolab-wire/v1) for lab-automation-atlas (Layer L5).

Dynamically grounds target hardware platforms from `atlas.json` (cached by `(path, st_mtime_ns)`),
enforces canonical HTTPS-only public-host SSRF safety (including non-canonical IPv4/IPv6 transition
rejection and optional DNS-pinned IP validation), and evaluates compound SPDX license expressions
(`AND`, `OR`, `WITH`) plus parent-lineage taint and catalog URL cross-matching under a strict
default-deny training policy in 1-to-1 parity with `LabAtlasLean.checkAtlasResource`.
"""

from __future__ import annotations

import copy
import re
import sys
import urllib.error
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

REPO_ID = "lab-automation-atlas"
LAYER = "L5"
SCHEMA_VERSION = "autolab-wire/v1"

REPO_DIR = Path(__file__).resolve().parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from lab_atlas.catalog import filter_entries, load_catalog, resolve_catalog_path  # noqa: E402
from lab_atlas.linkcheck import SecurityValidationError, validate_url_target  # noqa: E402
from lab_atlas.spdx import (  # noqa: E402
    PERMISSIVE_SPDX_ALLOWLIST,
    check_atlas_resource_policy,
    effective_license_class,
    evaluate_spdx_expression,
    license_conj,
)

# Permissive training license allowlist re-exported for downstream wire inspection
ALLOWED_TRAINING_SPDX_LICENSES: frozenset[str] = PERMISSIVE_SPDX_ALLOWLIST

_PLATFORM_ALIASES: dict[str, str] = {
    "ot2": "opentrons_ot2",
    "ot_2": "opentrons_ot2",
    "opentrons": "opentrons_ot2",
    "opentrons_ot2": "opentrons_ot2",
    "opentrons_ot_2": "opentrons_ot2",
    "flex": "opentrons_flex",
    "opentrons_flex": "opentrons_flex",
    "hamilton": "hamilton_star",
    "hamilton_star": "hamilton_star",
    "hamilton_vantage": "hamilton_vantage",
    "tecan": "tecan_fluent",
    "tecan_fluent": "tecan_fluent",
    "tecan_evo": "tecan_evo",
    "automata": "automata_linq",
    "automata_linq": "automata_linq",
    "biosero": "biosero_gbg",
    "biosero_gbg": "biosero_gbg",
    "green_button_go": "biosero_gbg",
    "ecl": "emerald_cloud_lab",
    "emerald": "emerald_cloud_lab",
    "emerald_cloud_lab": "emerald_cloud_lab",
    "strateos": "strateos_cloud_lab",
    "strateos_cloud_lab": "strateos_cloud_lab",
    "ginkgo": "ginkgo_rac",
    "ginkgo_bioworks": "ginkgo_rac",
    "ginkgo_rac": "ginkgo_rac",
    "sdl": "modular_sdl",
    "modular_sdl": "modular_sdl",
    "ros2": "modular_sdl",
    "wei": "modular_sdl",
    "chemputer": "chemputer",
    "xdl": "chemputer",
    "xdl_chemputer": "chemputer",
    "bluesky": "epics_beamline",
    "epics": "epics_beamline",
    "epics_beamline": "epics_beamline",
}

_PLATFORM_HW_KEYWORDS: dict[str, tuple[str, ...]] = {
    "opentrons_ot2": ("opentrons ot-2",),
    "opentrons_flex": ("opentrons flex",),
    "hamilton_star": ("hamilton star",),
    "hamilton_vantage": ("hamilton vantage",),
    "tecan_fluent": ("tecan fluent",),
    "tecan_evo": ("tecan evo",),
    "automata_linq": ("automata linq",),
    "biosero_gbg": ("multi-vendor workcells", "sila-2 instruments"),
    "emerald_cloud_lab": ("emerald cloud lab",),
    "strateos_cloud_lab": ("strateos cloud lab",),
    "ginkgo_rac": ("ginkgo rac",),
    "modular_sdl": ("modular sdl", "ros2 workcells"),
    "chemputer": ("chemputer",),
    "epics_beamline": ("epics beamlines",),
}

_CROSS_REF_LABELS: frozenset[str] = frozenset({"lab-rehearsal", "lab-verify", "Studio"})
_VALID_PLATFORM_SLUG_RE = re.compile(r"^[A-Za-z0-9]+(?:[ _-][A-Za-z0-9]+)*$")


@dataclass(frozen=True)
class _ResolvedPlatformRecord:
    platform_id: str
    instrument_model: str
    deck_architecture: str | None
    api_level: str | None
    max_deck_slots: int | None
    staging_slots: int
    min_volume_ul: float | None
    max_volume_ul: float | None
    dead_volume_floor_ul: float | None
    min_temp_c: float | None
    max_temp_c: float | None
    protocol_formats: list[str]
    has_simulator: bool
    matched_catalog_ids: list[str]
    analytical_modalities: list[str]


@dataclass
class _IndexedAtlas:
    mtime_ns: int
    catalog: dict[str, Any]
    platforms: dict[str, _ResolvedPlatformRecord]
    url_prefixes: list[tuple[str, dict[str, Any]]]


_INDEX_CACHE: dict[Path, _IndexedAtlas] = {}


def _normalize_slug(raw: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", raw.strip().lower()).strip("_")
    return _PLATFORM_ALIASES.get(cleaned, cleaned)


def _normalize_url_for_match(url: str) -> str:
    parsed = urllib.parse.urlsplit(url.strip())
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme.lower()}://{host}{path}"


def _build_indexed_atlas(catalog_path: Path) -> _IndexedAtlas:
    resolved = resolve_catalog_path(catalog_path)
    mtime_ns = resolved.stat().st_mtime_ns
    cached = _INDEX_CACHE.get(resolved)
    if cached is not None and cached.mtime_ns == mtime_ns:
        return cached

    catalog = load_catalog(resolved, validate=True)
    entries: list[dict[str, Any]] = catalog["entries"]

    # 1. Collect all hardware profiles from catalog entries
    raw_profiles: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for entry in entries:
        hw_cap = entry.get("hardware_capabilities")
        if not isinstance(hw_cap, dict):
            continue
        for prof in hw_cap.get("profiles") or []:
            if isinstance(prof, dict) and isinstance(prof.get("platform_id"), str):
                raw_profiles[prof["platform_id"]] = (prof, entry)

    platforms: dict[str, _ResolvedPlatformRecord] = {}
    for pid, (prof, owner_entry) in raw_profiles.items():
        keywords = _PLATFORM_HW_KEYWORDS.get(pid, (prof["instrument_model"].lower(), pid.replace("_", " ")))
        matched_entries: list[dict[str, Any]] = []
        for entry in entries:
            hw_lower = [h.lower() for h in entry["supported_hardware"]]
            if entry["id"] == owner_entry["id"] or any(
                any(kw in h for kw in keywords) for h in hw_lower
            ):
                matched_entries.append(entry)

        formats: list[str] = []
        modalities: list[str] = []
        matched_ids: list[str] = []
        has_sim = False
        for m_entry in matched_entries:
            matched_ids.append(m_entry["id"])
            if m_entry["has_simulator"] is True:
                has_sim = True
            for fmt in m_entry["protocol_formats"]:
                if fmt not in formats:
                    formats.append(fmt)
            for mod in m_entry.get("analytical_modalities") or []:
                if mod not in modalities:
                    modalities.append(mod)

        platforms[pid] = _ResolvedPlatformRecord(
            platform_id=pid,
            instrument_model=str(prof["instrument_model"]),
            deck_architecture=prof.get("deck_architecture"),
            api_level=prof.get("api_level"),
            max_deck_slots=prof.get("max_deck_slots"),
            staging_slots=int(prof.get("staging_slots", 0)),
            min_volume_ul=float(prof["min_volume_ul"]) if prof.get("min_volume_ul") is not None else None,
            max_volume_ul=float(prof["max_volume_ul"]) if prof.get("max_volume_ul") is not None else None,
            dead_volume_floor_ul=(
                float(prof["dead_volume_floor_ul"])
                if prof.get("dead_volume_floor_ul") is not None
                else None
            ),
            min_temp_c=float(prof["min_temp_c"]) if prof.get("min_temp_c") is not None else None,
            max_temp_c=float(prof["max_temp_c"]) if prof.get("max_temp_c") is not None else None,
            protocol_formats=formats,
            has_simulator=has_sim,
            matched_catalog_ids=matched_ids,
            analytical_modalities=modalities,
        )

    # 2. Build canonical URL prefix index for catalog contamination / license cross-matching
    url_prefixes: list[tuple[str, dict[str, Any]]] = []
    for entry in entries:
        candidates: list[str] = []
        for link in entry["links"]:
            if link["label"] in _CROSS_REF_LABELS:
                continue
            url_str = link["url"]
            # Avoid matching generic vendor root pages across unrelated paths unless exact/subpath
            candidates.append(_normalize_url_for_match(url_str))
        if entry.get("huggingface_id"):
            hf_id = entry["huggingface_id"]
            candidates.append(_normalize_url_for_match(f"https://huggingface.co/datasets/{hf_id}"))
            candidates.append(_normalize_url_for_match(f"https://huggingface.co/{hf_id}"))
        if entry.get("doi"):
            candidates.append(_normalize_url_for_match(f"https://doi.org/{entry['doi']}"))

        seen_norm: set[str] = set()
        for norm_u in candidates:
            if norm_u and norm_u not in seen_norm:
                seen_norm.add(norm_u)
                url_prefixes.append((norm_u, entry))

    # Sort longest prefix first so specific repository/dataset URLs match before broader domain roots
    url_prefixes.sort(key=lambda item: len(item[0]), reverse=True)

    indexed = _IndexedAtlas(
        mtime_ns=mtime_ns,
        catalog=catalog,
        platforms=platforms,
        url_prefixes=url_prefixes,
    )
    _INDEX_CACHE[resolved] = indexed
    return indexed


def _match_catalog_entries_by_url(url: str, indexed: _IndexedAtlas) -> list[dict[str, Any]]:
    norm_target = _normalize_url_for_match(url)
    matched: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for prefix, entry in indexed.url_prefixes:
        if norm_target == prefix or norm_target.startswith(prefix + "/"):
            eid = entry["id"]
            if eid not in seen_ids:
                seen_ids.add(eid)
                matched.append(entry)
    return matched


def _match_catalog_entry_by_url(url: str, indexed: _IndexedAtlas) -> dict[str, Any] | None:
    matches = _match_catalog_entries_by_url(url, indexed)
    return matches[0] if matches else None


def _is_https_ssrf_safe(
    url: object,
    *,
    resolve_dns: bool = False,
    resolver: Callable[..., Any] | None = None,
    pinned_ips: dict[tuple[str, int], list[str]] | None = None,
) -> bool:
    """Verify HTTPS-only scheme and canonical public hostname/IP SSRF bounds."""
    if not isinstance(url, str) or not url.startswith("https://"):
        return False
    try:
        validate_url_target(
            url,
            require_https=True,
            resolve_dns=resolve_dns,
            resolver=resolver,
            pinned_ips=pinned_ips,
        )
    except (SecurityValidationError, urllib.error.URLError):
        return False
    return True


def process_packet(
    packet: dict[str, Any],
    *,
    catalog_path: str | Path | None = None,
    resolver: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Validate L5 platform grounding, HTTPS SSRF bounds, and default-deny SPDX training posture."""
    if not isinstance(packet, dict):
        raise TypeError(f"autolab_wire packet must be a dict, got {type(packet).__name__}")

    out: dict[str, Any] = copy.deepcopy(packet)
    out.setdefault("schema_version", SCHEMA_VERSION)
    out.setdefault("halted", False)
    out.setdefault("halt_reason", None)
    out.setdefault("trace", [])
    out.setdefault("bottom_reasoning_traces", [])

    if out["halted"] is True:
        return out

    malformed_fields: list[str] = []
    if not isinstance(out["halted"], bool):
        malformed_fields.append("halted")
    if not isinstance(out["trace"], list):
        out["trace"] = []
        malformed_fields.append("trace")
    if not isinstance(out["bottom_reasoning_traces"], list):
        out["bottom_reasoning_traces"] = []
        malformed_fields.append("bottom_reasoning_traces")

    indexed = _build_indexed_atlas(Path(catalog_path) if catalog_path else (REPO_DIR / "atlas.json"))
    entries = indexed.catalog["entries"]
    len_entries = len(entries)

    has_platform_key = "target_platform" in out
    raw_platform = out.get("target_platform", "opentrons_ot2")
    if isinstance(raw_platform, str):
        stripped_platform = raw_platform.strip()
        if stripped_platform and _VALID_PLATFORM_SLUG_RE.match(stripped_platform):
            target_platform = stripped_platform
            norm_platform = _normalize_slug(stripped_platform)
            platform_record = indexed.platforms.get(norm_platform)
        else:
            target_platform = stripped_platform
            norm_platform = ""
            platform_record = None
    else:
        target_platform = repr(raw_platform) if has_platform_key else ""
        norm_platform = ""
        platform_record = None

    resource_url = out.get("resource_url", "https://github.com/yaniguan/stepbot")

    raw_for_training = out.get("for_training", True)
    if isinstance(raw_for_training, bool):
        for_training = raw_for_training
    else:
        for_training = True
        malformed_fields.append("for_training")

    raw_commercial = out.get("commercial", True)
    if isinstance(raw_commercial, bool):
        commercial = raw_commercial
    else:
        commercial = True
        malformed_fields.append("commercial")

    raw_resolve_dns = out.get("resolve_dns", False)
    if isinstance(raw_resolve_dns, bool):
        resolve_dns = raw_resolve_dns
    else:
        resolve_dns = False
        malformed_fields.append("resolve_dns")

    pinned_ips: dict[tuple[str, int], list[str]] = {}
    url_safe = _is_https_ssrf_safe(
        resource_url,
        resolve_dns=resolve_dns,
        resolver=resolver,
        pinned_ips=pinned_ips if resolve_dns else None,
    )

    # 1. Evaluate caller-supplied SPDX expression strictly (fail-closed on non-string or blank)
    raw_license = out.get("license_class", "MIT")
    if isinstance(raw_license, str) and raw_license.strip():
        license_expr = raw_license.strip()
        own_eval = evaluate_spdx_expression(license_expr, allow_policy_aliases=True)
        spdx_known = own_eval.spdx_known
        eff_class = own_eval.license_class
    else:
        license_expr = repr(raw_license)
        spdx_known = False
        eff_class = "custom_terms"
        malformed_fields.append("license_class")

    # 2. Fold upstream parent licenses strictly if derived corpus lineage key is provided
    parent_classes: list[str] = []
    if "parent_licenses" in out:
        raw_parents = out["parent_licenses"]
        if isinstance(raw_parents, list):
            for p_expr in raw_parents:
                if isinstance(p_expr, str) and p_expr.strip():
                    p_eval = evaluate_spdx_expression(p_expr.strip(), allow_policy_aliases=True)
                    if not p_eval.spdx_known:
                        spdx_known = False
                    parent_classes.append(p_eval.license_class)
                else:
                    spdx_known = False
                    parent_classes.append("custom_terms")
                    malformed_fields.append("parent_licenses")
        else:
            spdx_known = False
            eff_class = license_conj(eff_class, "custom_terms")
            malformed_fields.append("parent_licenses")
    if parent_classes:
        eff_class = effective_license_class(parent_classes, eff_class)

    if malformed_fields:
        spdx_known = False
        eff_class = license_conj(eff_class, "custom_terms")

    # 3. Cross-match normalized resource_url against all matching verified atlas.json governance records
    matched_entries = (
        _match_catalog_entries_by_url(resource_url, indexed)
        if isinstance(resource_url, str) and url_safe
        else []
    )
    for matched_entry in matched_entries:
        cat_eval = evaluate_spdx_expression(matched_entry["spdx_license"], allow_policy_aliases=False)
        eff_class = license_conj(eff_class, cat_eval.license_class)
        purposes = matched_entry["allowed_purposes"]
        has_train_purpose = ("train_commercial" in purposes) or ("train_academic" in purposes)
        if purposes == ["eval_only"]:
            eff_class = license_conj(eff_class, "eval_only")
        elif "rag_pointer_only" in purposes and not has_train_purpose:
            eff_class = license_conj(eff_class, "custom_terms")
        if for_training and commercial and matched_entry["commercial_use_ok"] is False:
            eff_class = license_conj(eff_class, "non_commercial")

    # 4. Mirror LabAtlasLean.checkAtlasResource (with strict fail-closed malformed field reporting)
    if malformed_fields:
        policy_violation: str | None = f"malformed_packet_fields({','.join(sorted(set(malformed_fields)))})"
    else:
        policy_violation = check_atlas_resource_policy(
            https_only=url_safe,
            no_private_ip=url_safe,
            spdx_known=spdx_known,
            license_class=eff_class,
            for_training=for_training,
            commercial=commercial,
        )
    license_and_url_ok = policy_violation is None

    if not license_and_url_ok:
        out["halted"] = True
        out["halt_reason"] = "L5_ATLAS_LICENSE_OR_URL_BLOCK"
    elif platform_record is None:
        out["halted"] = True
        out["halt_reason"] = "L5_ATLAS_UNKNOWN_PLATFORM"

    requested_modality = out.get("requested_modality") or out.get("orthogonal_modality")
    capable_modality_ids: list[str] | None = None
    if isinstance(requested_modality, str) and requested_modality.strip():
        capable_modality_ids = [
            e["id"] for e in filter_entries(entries, modality=requested_modality.strip())
        ]

    if platform_record is not None:
        grounding: dict[str, Any] = {
            "platform": target_platform,
            "resolved_platform_id": platform_record.platform_id,
            "instrument_model": platform_record.instrument_model,
            "deck_architecture": platform_record.deck_architecture,
            "api_level": platform_record.api_level,
            "max_deck_slots": platform_record.max_deck_slots,
            "staging_slots": platform_record.staging_slots,
            "min_volume_ul": platform_record.min_volume_ul,
            "max_volume_ul": platform_record.max_volume_ul,
            "protocol_formats": list(platform_record.protocol_formats),
            "has_simulator": platform_record.has_simulator,
            "matched_catalog_ids": list(platform_record.matched_catalog_ids),
            "analytical_modalities": list(platform_record.analytical_modalities),
            "effective_license_class": eff_class,
            "license_ok": license_and_url_ok,
            "registered_entries": len_entries,
        }
    else:
        grounding = {
            "platform": target_platform,
            "resolved_platform_id": None,
            "instrument_model": None,
            "deck_architecture": None,
            "api_level": None,
            "max_deck_slots": None,
            "staging_slots": 0,
            "min_volume_ul": None,
            "max_volume_ul": None,
            "protocol_formats": [],
            "has_simulator": False,
            "matched_catalog_ids": [],
            "analytical_modalities": [],
            "effective_license_class": eff_class,
            "license_ok": license_and_url_ok,
            "registered_entries": len_entries,
        }

    if capable_modality_ids is not None:
        grounding["capable_modality_entries"] = capable_modality_ids
    if resolve_dns and pinned_ips:
        grounding["pinned_ips"] = {f"{h}:{p}": ips for (h, p), ips in pinned_ips.items()}

    out["platform_grounding"] = grounding

    status = "BLOCK" if out["halted"] else "PASS"
    if not license_and_url_ok:
        summary = (
            f"Blocked resource_url={resource_url!r}, license_class={license_expr!r} "
            f"(effective={eff_class!r}, rule={policy_violation}, for_training={for_training}, commercial={commercial})."
        )
    elif platform_record is None:
        summary = (
            f"Blocked unknown target_platform={target_platform!r} (0 matching hardware/cloud-lab profiles "
            f"across {len_entries} verified atlas records)."
        )
    else:
        slots_desc = (
            f"{platform_record.max_deck_slots} deck slots"
            if platform_record.max_deck_slots is not None
            else f"{platform_record.deck_architecture}"
        )
        summary = (
            f"Grounded {target_platform} ({platform_record.instrument_model}, API {platform_record.api_level}, "
            f"{slots_desc}, {len(platform_record.matched_catalog_ids)} matching catalog entries) "
            f"across {len_entries} verified atlas records."
        )

    out["trace"].append(
        {
            "repo": REPO_ID,
            "layer": LAYER,
            "status": status,
            "summary": summary,
        }
    )
    out["bottom_reasoning_traces"].append(
        {
            "repo": REPO_ID,
            "layer": LAYER,
            "invariant": "eval_only_blocked_from_training",
            "first_principles": (
                "Held-out evaluation benchmarks, unverified custom terms, and non-commercial corpora "
                "(including compound SPDX AND/lineage derivations) cannot enter autonomous training "
                "pipelines, target platforms must resolve to verified L5 capability profiles, and "
                "external registry URLs must satisfy canonical HTTPS-only public-host SSRF guards."
            ),
        }
    )
    return out
