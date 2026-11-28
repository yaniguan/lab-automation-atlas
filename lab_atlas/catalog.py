"""Catalog loading, strict stdlib schema validation, filtering, and compatibility queries."""

from __future__ import annotations

import json
import re
import urllib.parse
from datetime import date
from pathlib import Path
from typing import Any

from .linkcheck import SecurityValidationError, validate_url_target
from .spdx import LicenseEvaluation, evaluate_spdx_expression, spdx_satisfies_filter

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
RESOURCE_DIR = PACKAGE_DIR / "resources"

ALLOWED_CATEGORIES = (
    "autolab_sibling",
    "hardware",
    "cloud_lab",
    "software",
    "chemistry_and_procurement",
    "dataset",
    "simulation_and_verification",
)
ALLOWED_LAYERS = ("Hub", "L0", "L1", "L2", "L3", "L4", "L5", "L6", None)
ALLOWED_STATUSES = (
    "active",
    "maintenance",
    "legacy",
    "archived",
    "commercial_restructured",
)
ALLOWED_PURPOSES = (
    "train_commercial",
    "train_academic",
    "eval_only",
    "rag_pointer_only",
    "tool_integration",
)
ALLOWED_SCRAPING_POLICIES = (
    "git_or_hf_download",
    "public_api_rate_limited",
    "no_bulk_scraping_per_article",
    "vendor_docs_pointer_only",
)
ALLOWED_MODALITIES = (
    "XRD",
    "Raman",
    "NMR",
    "LC-MS",
    "GC-MS",
    "UV-Vis",
    "FTIR",
    "fluorescence_plate_reader",
    "optical_imaging",
    "acoustic_monitoring",
    "SAXS_WAXS",
    "chemiresistive_gas_sensor",
)
ALLOWED_DECK_ARCHITECTURES = (
    "sbs_fixed_slots",
    "sbs_coordinate_grid",
    "carrier_rails",
    "modular_workcell",
    "flow_batch_reactor",
    "cloud_symbolic_facility",
    "beamline_station",
)

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_PLATFORM_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_HTTPS_RE = re.compile(r"^https://[^\s]+$")

_ROOT_KEYS = {"schema_version", "atlas_name", "last_verified", "categories", "entries"}
_CATEGORY_KEYS = {"id", "title", "description"}
_LINK_KEYS = {"label", "url"}
_ENTRY_KEYS = {
    "id",
    "name",
    "category",
    "role",
    "layer",
    "maintenance_status",
    "spdx_license",
    "osi_approved",
    "license_evidence",
    "commercial_use_ok",
    "links",
    "supported_hardware",
    "protocol_formats",
    "has_simulator",
    "allowed_purposes",
    "scraping_policy",
    "contamination_warning",
    "huggingface_id",
    "doi",
    "tasks",
    "record_count",
    "last_checked",
}
_OPTIONAL_ENTRY_KEYS = {"hardware_capabilities", "analytical_modalities"}
_ALL_ENTRY_KEYS = _ENTRY_KEYS | _OPTIONAL_ENTRY_KEYS

_HW_CAP_REQUIRED_KEYS = {"api_level", "max_deck_slots", "min_volume_ul"}
_HW_CAP_ALLOWED_KEYS = {
    "platform_id",
    "deck_architecture",
    "api_level",
    "max_deck_slots",
    "staging_slots",
    "min_volume_ul",
    "max_volume_ul",
    "dead_volume_floor_ul",
    "min_temp_c",
    "max_temp_c",
    "high_temp_seal_threshold_c",
    "profiles",
}
_HW_PROFILE_KEYS = {
    "platform_id",
    "instrument_model",
    "deck_architecture",
    "api_level",
    "max_deck_slots",
    "staging_slots",
    "min_volume_ul",
    "max_volume_ul",
    "dead_volume_floor_ul",
    "min_temp_c",
    "max_temp_c",
    "high_temp_seal_threshold_c",
}

_CATALOG_CACHE: dict[Path, tuple[int, dict[str, Any]]] = {}


def resolve_catalog_path(path: str | Path | None = None) -> Path:
    """Resolve the canonical atlas.json path from explicit path, repo root, or package resources."""
    if path is not None:
        return Path(path).resolve()
    root_candidate = REPO_ROOT / "atlas.json"
    if root_candidate.is_file():
        return root_candidate
    resource_candidate = RESOURCE_DIR / "atlas.json"
    if resource_candidate.is_file():
        return resource_candidate
    raise FileNotFoundError("Could not locate atlas.json in repository root or package resources.")


def resolve_schema_path(path: str | Path | None = None) -> Path:
    """Resolve the canonical atlas.schema.json path."""
    if path is not None:
        return Path(path).resolve()
    root_candidate = REPO_ROOT / "schema" / "atlas.schema.json"
    if root_candidate.is_file():
        return root_candidate
    resource_candidate = RESOURCE_DIR / "atlas.schema.json"
    if resource_candidate.is_file():
        return resource_candidate
    raise FileNotFoundError("Could not locate atlas.schema.json.")


def load_catalog(path: str | Path | None = None, *, validate: bool = True) -> dict[str, Any]:
    """Load and optionally validate the machine-readable atlas catalog."""
    resolved = resolve_catalog_path(path)
    data = json.loads(resolved.read_text(encoding="utf-8"))
    if validate:
        errors = validate_catalog(data)
        if errors:
            raise ValueError(f"Invalid catalog {resolved}: {'; '.join(errors)}")
    return data


def load_catalog_cached(path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate atlas.json with `(resolved_path, st_mtime_ns)` caching."""
    resolved = resolve_catalog_path(path)
    mtime_ns = resolved.stat().st_mtime_ns
    cached = _CATALOG_CACHE.get(resolved)
    if cached is not None and cached[0] == mtime_ns:
        return cached[1]
    data = load_catalog(resolved, validate=True)
    _CATALOG_CACHE[resolved] = (mtime_ns, data)
    return data


def load_schema(path: str | Path | None = None) -> dict[str, Any]:
    """Load the JSON Schema definition for atlas.json."""
    resolved = resolve_schema_path(path)
    return json.loads(resolved.read_text(encoding="utf-8"))


def _is_bool(val: Any) -> bool:
    return isinstance(val, bool)


def _is_int(val: Any) -> bool:
    return isinstance(val, int) and not isinstance(val, bool)


def _is_num(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def _is_nonempty_str(val: Any, min_len: int = 1) -> bool:
    return isinstance(val, str) and len(val.strip()) >= min_len


def _is_valid_iso_date(val: Any) -> bool:
    if not isinstance(val, str) or not _DATE_RE.match(val):
        return False
    try:
        date.fromisoformat(val)
    except ValueError:
        return False
    return True


def is_generic_or_bare_arxiv_license_evidence(url: str) -> bool:
    """Return True when `url` points to a generic license deed or bare arXiv paper page."""
    if not isinstance(url, str) or not url.strip():
        return False
    parsed = urllib.parse.urlsplit(url.strip())
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    path_low = parsed.path.lower()
    if host == "creativecommons.org" and (
        path_low == "/licenses"
        or path_low.startswith("/licenses/")
        or path_low == "/publicdomain"
        or path_low.startswith("/publicdomain/")
    ):
        return True
    if host == "spdx.org" and (path_low == "/licenses" or path_low.startswith("/licenses/")):
        return True
    if host == "opensource.org" and (
        path_low == "/licenses"
        or path_low.startswith("/licenses/")
        or path_low == "/license"
        or path_low.startswith("/license/")
    ):
        return True
    if host in ("arxiv.org", "export.arxiv.org") and (
        path_low == "/abs"
        or path_low.startswith("/abs/")
        or path_low == "/pdf"
        or path_low.startswith("/pdf/")
    ):
        return True
    return False


def _is_valid_https_url(val: Any) -> bool:
    if not isinstance(val, str) or not _HTTPS_RE.match(val):
        return False
    try:
        validate_url_target(val, require_https=True, resolve_dns=False)
    except SecurityValidationError:
        return False
    return True


def _validate_hw_envelope_bounds(
    obj: dict[str, Any],
    prefix: str,
    *,
    strict_non_null: bool,
    errors: list[str],
) -> None:
    if "platform_id" in obj and obj["platform_id"] is not None:
        pid = obj["platform_id"]
        if not isinstance(pid, str) or not _PLATFORM_ID_RE.match(pid):
            errors.append(f"{prefix}.platform_id invalid slug: {pid!r}")

    if "instrument_model" in obj:
        if not _is_nonempty_str(obj["instrument_model"], 1):
            errors.append(f"{prefix}.instrument_model must be non-empty string.")

    if "deck_architecture" in obj and obj["deck_architecture"] is not None:
        if obj["deck_architecture"] not in ALLOWED_DECK_ARCHITECTURES:
            errors.append(f"{prefix}.deck_architecture invalid: {obj['deck_architecture']!r}")

    api_level = obj.get("api_level")
    if api_level is not None and not _is_nonempty_str(api_level, 1):
        errors.append(f"{prefix}.api_level must be non-empty string or null.")

    slots = obj.get("max_deck_slots")
    if slots is not None and (not _is_int(slots) or slots < 1):
        errors.append(f"{prefix}.max_deck_slots must be integer >= 1 or null.")

    if "staging_slots" in obj:
        st_slots = obj["staging_slots"]
        if not _is_int(st_slots) or st_slots < 0:
            errors.append(f"{prefix}.staging_slots must be integer >= 0.")

    min_v = obj.get("min_volume_ul")
    max_v = obj.get("max_volume_ul")
    dead_v = obj.get("dead_volume_floor_ul")
    min_t = obj.get("min_temp_c")
    max_t = obj.get("max_temp_c")
    seal_t = obj.get("high_temp_seal_threshold_c")

    if strict_non_null:
        for req_num in (
            "min_volume_ul",
            "max_volume_ul",
            "dead_volume_floor_ul",
            "min_temp_c",
            "max_temp_c",
            "high_temp_seal_threshold_c",
        ):
            if not _is_num(obj.get(req_num)):
                errors.append(f"{prefix}.{req_num} must be a number.")

    if min_v is not None:
        if not _is_num(min_v) or float(min_v) <= 0.0:
            errors.append(f"{prefix}.min_volume_ul must be > 0.")
    if max_v is not None:
        if not _is_num(max_v) or float(max_v) <= 0.0:
            errors.append(f"{prefix}.max_volume_ul must be > 0.")
    if _is_num(min_v) and _is_num(max_v) and float(min_v) > float(max_v):
        errors.append(f"{prefix} inverted volume bounds: min_volume_ul > max_volume_ul.")

    if dead_v is not None and (not _is_num(dead_v) or float(dead_v) < 0.0):
        errors.append(f"{prefix}.dead_volume_floor_ul must be >= 0.")

    if min_t is not None and (not _is_num(min_t) or float(min_t) < -200.0):
        errors.append(f"{prefix}.min_temp_c must be >= -200.0 C.")
    if max_t is not None and (not _is_num(max_t) or float(max_t) > 500.0):
        errors.append(f"{prefix}.max_temp_c must be <= 500.0 C.")
    if _is_num(min_t) and _is_num(max_t) and float(min_t) > float(max_t):
        errors.append(f"{prefix} inverted thermal bounds: min_temp_c > max_temp_c.")
    if seal_t is not None:
        if not _is_num(seal_t) or float(seal_t) < -200.0:
            errors.append(f"{prefix}.high_temp_seal_threshold_c must be >= -200.0 C.")
        elif _is_num(min_t) and float(seal_t) < float(min_t):
            errors.append(
                f"{prefix}.high_temp_seal_threshold_c must be >= min_temp_c."
            )


def validate_catalog(catalog: dict[str, Any]) -> list[str]:
    """Validate catalog structure, SPDX expressions, capabilities, HTTPS URLs, and uniqueness."""
    errors: list[str] = []
    if not isinstance(catalog, dict):
        return ["Root catalog must be a JSON object."]

    missing_root = _ROOT_KEYS - set(catalog.keys())
    extra_root = set(catalog.keys()) - _ROOT_KEYS
    if missing_root:
        errors.append(f"Missing root keys: {sorted(missing_root)}")
    if extra_root:
        errors.append(f"Unexpected root keys (additionalProperties=false): {sorted(extra_root)}")
    if errors:
        return errors

    if catalog["schema_version"] != "1.0.0":
        errors.append(f"schema_version must be '1.0.0', got {catalog['schema_version']!r}")
    if catalog["atlas_name"] != "lab-automation-atlas":
        errors.append(f"atlas_name must be 'lab-automation-atlas', got {catalog['atlas_name']!r}")
    if not _is_valid_iso_date(catalog["last_verified"]):
        errors.append(f"Invalid last_verified date: {catalog['last_verified']!r}")

    categories = catalog["categories"]
    if not isinstance(categories, list) or len(categories) < 5:
        errors.append("categories must be a list of at least 5 category descriptors.")
        defined_cats: set[str] = set()
    else:
        defined_cats = set()
        for idx, cat in enumerate(categories):
            if not isinstance(cat, dict):
                errors.append(f"categories[{idx}] must be an object.")
                continue
            extra = set(cat.keys()) - _CATEGORY_KEYS
            miss = _CATEGORY_KEYS - set(cat.keys())
            if miss or extra:
                errors.append(f"categories[{idx}] invalid keys (missing={sorted(miss)}, extra={sorted(extra)}).")
                continue
            if cat["id"] not in ALLOWED_CATEGORIES:
                errors.append(f"categories[{idx}].id {cat['id']!r} not in {ALLOWED_CATEGORIES}.")
            if cat["id"] in defined_cats:
                errors.append(f"Duplicate category id {cat['id']!r}.")
            defined_cats.add(cat["id"])
            if not _is_nonempty_str(cat["title"], 3):
                errors.append(f"categories[{idx}].title must be >= 3 chars.")
            if not _is_nonempty_str(cat["description"], 10):
                errors.append(f"categories[{idx}].description must be >= 10 chars.")

    entries = catalog["entries"]
    if not isinstance(entries, list) or len(entries) < 30:
        errors.append("entries must be a list of at least 30 catalog entries.")
        return errors

    seen_ids: set[str] = set()
    seen_profile_ids: set[str] = set()

    for idx, entry in enumerate(entries):
        prefix = f"entries[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object.")
            continue
        miss = _ENTRY_KEYS - set(entry.keys())
        extra = set(entry.keys()) - _ALL_ENTRY_KEYS
        if miss:
            errors.append(f"{prefix} missing required keys: {sorted(miss)}")
            continue
        if extra:
            errors.append(f"{prefix} has unexpected keys (additionalProperties=false): {sorted(extra)}")
            continue

        eid = entry["id"]
        if not isinstance(eid, str) or not _ID_RE.match(eid):
            errors.append(f"{prefix}.id invalid slug: {eid!r}")
        elif eid in seen_ids:
            errors.append(f"Duplicate entry id: {eid!r}")
        else:
            seen_ids.add(eid)
            prefix = f"entry[{eid}]"

        if not _is_nonempty_str(entry["name"], 1):
            errors.append(f"{prefix}.name must be non-empty string.")
        if entry["category"] not in ALLOWED_CATEGORIES or (defined_cats and entry["category"] not in defined_cats):
            errors.append(f"{prefix}.category invalid: {entry['category']!r}")
        if not _is_nonempty_str(entry["role"], 5):
            errors.append(f"{prefix}.role must be >= 5 chars.")
        if entry["layer"] not in ALLOWED_LAYERS:
            errors.append(f"{prefix}.layer invalid: {entry['layer']!r}")
        if entry["maintenance_status"] not in ALLOWED_STATUSES:
            errors.append(f"{prefix}.maintenance_status invalid: {entry['maintenance_status']!r}")

        spdx_eval: LicenseEvaluation | None = None
        if not _is_nonempty_str(entry["spdx_license"], 2):
            errors.append(f"{prefix}.spdx_license must be >= 2 chars.")
        else:
            spdx_eval = evaluate_spdx_expression(
                entry["spdx_license"],
                allow_policy_aliases=False,
                require_uppercase_operators=True,
            )
            if not spdx_eval.spdx_known:
                errors.append(
                    f"{prefix}.spdx_license invalid or unrecognized SPDX expression: {entry['spdx_license']!r}"
                )

        if not _is_bool(entry["osi_approved"]):
            errors.append(f"{prefix}.osi_approved must be boolean.")
        if not _is_valid_https_url(entry["license_evidence"]):
            errors.append(f"{prefix}.license_evidence must be a safe public https:// URL.")
        elif entry["category"] in ("dataset", "chemistry_and_procurement") and is_generic_or_bare_arxiv_license_evidence(
            entry["license_evidence"]
        ):
            errors.append(
                f"{prefix}.license_evidence must cite an upstream source rather than a generic license deed or bare arXiv page: {entry['license_evidence']!r}"
            )
        if not _is_bool(entry["commercial_use_ok"]):
            errors.append(f"{prefix}.commercial_use_ok must be boolean.")

        links = entry["links"]
        if not isinstance(links, list) or len(links) < 1:
            errors.append(f"{prefix}.links must be a non-empty list.")
        else:
            for lidx, link in enumerate(links):
                if not isinstance(link, dict) or set(link.keys()) != _LINK_KEYS:
                    errors.append(f"{prefix}.links[{lidx}] must have exact keys ('label', 'url').")
                    continue
                if not _is_nonempty_str(link["label"], 1):
                    errors.append(f"{prefix}.links[{lidx}].label must be non-empty.")
                if not _is_valid_https_url(link["url"]):
                    errors.append(
                        f"{prefix}.links[{lidx}].url must be a safe public https:// URL, got {link['url']!r}."
                    )

        for list_field in ("supported_hardware", "protocol_formats", "tasks"):
            val = entry[list_field]
            if not isinstance(val, list) or not all(_is_nonempty_str(x, 1) for x in val):
                errors.append(f"{prefix}.{list_field} must be a list of non-empty strings.")

        if entry["has_simulator"] is not None and not _is_bool(entry["has_simulator"]):
            errors.append(f"{prefix}.has_simulator must be boolean or null.")

        if "hardware_capabilities" in entry and entry["hardware_capabilities"] is not None:
            hw_cap = entry["hardware_capabilities"]
            if not isinstance(hw_cap, dict):
                errors.append(f"{prefix}.hardware_capabilities must be an object or null.")
            else:
                miss_hw = _HW_CAP_REQUIRED_KEYS - set(hw_cap.keys())
                extra_hw = set(hw_cap.keys()) - _HW_CAP_ALLOWED_KEYS
                if miss_hw:
                    errors.append(f"{prefix}.hardware_capabilities missing required keys: {sorted(miss_hw)}")
                if extra_hw:
                    errors.append(
                        f"{prefix}.hardware_capabilities has unexpected keys (additionalProperties=false): {sorted(extra_hw)}"
                    )
                _validate_hw_envelope_bounds(
                    hw_cap,
                    f"{prefix}.hardware_capabilities",
                    strict_non_null=False,
                    errors=errors,
                )
                if "profiles" in hw_cap:
                    profs = hw_cap["profiles"]
                    if not isinstance(profs, list) or len(profs) < 1:
                        errors.append(f"{prefix}.hardware_capabilities.profiles must be a non-empty list.")
                    else:
                        for pidx, prof in enumerate(profs):
                            p_prefix = f"{prefix}.hardware_capabilities.profiles[{pidx}]"
                            if not isinstance(prof, dict):
                                errors.append(f"{p_prefix} must be an object.")
                                continue
                            pmiss = _HW_PROFILE_KEYS - set(prof.keys())
                            pextra = set(prof.keys()) - _HW_PROFILE_KEYS
                            if pmiss or pextra:
                                errors.append(
                                    f"{p_prefix} invalid keys (missing={sorted(pmiss)}, extra={sorted(pextra)})."
                                )
                                continue
                            _validate_hw_envelope_bounds(
                                prof,
                                p_prefix,
                                strict_non_null=True,
                                errors=errors,
                            )
                            pid = prof["platform_id"]
                            if isinstance(pid, str) and pid in seen_profile_ids:
                                errors.append(f"Duplicate hardware profile platform_id: {pid!r}")
                            elif isinstance(pid, str):
                                seen_profile_ids.add(pid)

        if "analytical_modalities" in entry:
            mods = entry["analytical_modalities"]
            if not isinstance(mods, list):
                errors.append(f"{prefix}.analytical_modalities must be a list.")
            else:
                if len(mods) != len(set(mods)):
                    errors.append(f"{prefix}.analytical_modalities must not contain duplicates.")
                for mod in mods:
                    if mod not in ALLOWED_MODALITIES:
                        errors.append(
                            f"{prefix}.analytical_modalities invalid modality {mod!r} (allowed={ALLOWED_MODALITIES})."
                        )

        purposes = entry["allowed_purposes"]
        if (
            not isinstance(purposes, list)
            or len(purposes) < 1
            or len(purposes) != len(set(purposes))
            or any(p not in ALLOWED_PURPOSES for p in purposes)
        ):
            errors.append(f"{prefix}.allowed_purposes invalid: {purposes!r}")
        elif (
            entry["category"] in ("dataset", "chemistry_and_procurement")
            and spdx_eval is not None
            and spdx_eval.spdx_known
        ):
            if "train_commercial" in purposes and not spdx_eval.commercial_train_ok:
                errors.append(
                    f"{prefix}.allowed_purposes includes 'train_commercial' but SPDX license "
                    f"{entry['spdx_license']!r} (class={spdx_eval.license_class!r}) does not permit commercial training."
                )
            if "train_academic" in purposes and not spdx_eval.academic_train_ok:
                errors.append(
                    f"{prefix}.allowed_purposes includes 'train_academic' but SPDX license "
                    f"{entry['spdx_license']!r} (class={spdx_eval.license_class!r}) does not permit academic training."
                )

        if (
            entry["category"] in ("dataset", "chemistry_and_procurement")
            and _is_bool(entry["commercial_use_ok"])
            and entry["commercial_use_ok"] is True
            and spdx_eval is not None
            and spdx_eval.spdx_known
            and spdx_eval.license_class in ("non_commercial", "custom_terms", "eval_only")
        ):
            errors.append(
                f"{prefix}.commercial_use_ok cannot be true when SPDX license "
                f"{entry['spdx_license']!r} resolves to {spdx_eval.license_class!r}."
            )

        if entry["scraping_policy"] not in ALLOWED_SCRAPING_POLICIES:
            errors.append(f"{prefix}.scraping_policy invalid: {entry['scraping_policy']!r}")

        for nullable_str in ("contamination_warning", "huggingface_id", "doi", "record_count"):
            val = entry[nullable_str]
            if val is not None and not _is_nonempty_str(val, 1):
                errors.append(f"{prefix}.{nullable_str} must be non-empty string or null.")

        if not _is_valid_iso_date(entry["last_checked"]):
            errors.append(f"{prefix}.last_checked invalid date: {entry['last_checked']!r}")

        # Policy invariant: held-out evaluation benchmarks across ALL categories must declare contamination_warning
        if entry["allowed_purposes"] == ["eval_only"]:
            if not entry["contamination_warning"]:
                errors.append(f"{prefix} is eval_only but lacks contamination_warning.")

    return errors


def _entry_volume_satisfies(
    entry: dict[str, Any],
    *,
    min_volume_at_most: float | None,
    max_volume_at_least: float | None,
) -> bool:
    hw_cap = entry.get("hardware_capabilities")
    if not isinstance(hw_cap, dict):
        return False
    candidates: list[dict[str, Any]] = [hw_cap]
    if isinstance(hw_cap.get("profiles"), list):
        candidates.extend(p for p in hw_cap["profiles"] if isinstance(p, dict))

    for cand in candidates:
        c_min = cand.get("min_volume_ul")
        c_max = cand.get("max_volume_ul")
        if min_volume_at_most is not None:
            if not _is_num(c_min) or float(c_min) > min_volume_at_most:
                continue
        if max_volume_at_least is not None:
            if not _is_num(c_max) or float(c_max) < max_volume_at_least:
                continue
        return True
    return False


def filter_entries(
    entries: list[dict[str, Any]],
    *,
    category: str | None = None,
    layer: str | None = None,
    spdx_license: str | None = None,
    commercial_ok: bool | None = None,
    osi_approved: bool | None = None,
    status: str | None = None,
    hardware: str | None = None,
    protocol_format: str | None = None,
    allowed_purpose: str | None = None,
    has_simulator: bool | None = None,
    modality: str | None = None,
    min_volume_at_most: float | None = None,
    max_volume_at_least: float | None = None,
    query: str | None = None,
) -> list[dict[str, Any]]:
    """Filter catalog entries across structured L5 planning, capability, and governance dimensions."""
    result: list[dict[str, Any]] = []
    q_norm = query.strip().lower() if query else None
    hw_norm = hardware.strip().lower() if hardware else None
    fmt_norm = protocol_format.strip().lower() if protocol_format else None
    mod_norm = modality.strip().lower() if modality else None

    for entry in entries:
        if category is not None and entry["category"] != category:
            continue
        if layer is not None and (entry["layer"] or "").upper() != layer.upper():
            continue
        if spdx_license is not None and not spdx_satisfies_filter(entry["spdx_license"], spdx_license):
            continue
        if commercial_ok is not None and entry["commercial_use_ok"] is not commercial_ok:
            continue
        if osi_approved is not None and entry["osi_approved"] is not osi_approved:
            continue
        if status is not None and entry["maintenance_status"] != status:
            continue
        if hw_norm is not None:
            if not any(hw_norm in hw.lower() for hw in entry["supported_hardware"]):
                continue
        if fmt_norm is not None:
            if not any(fmt_norm in fmt.lower() for fmt in entry["protocol_formats"]):
                continue
        if allowed_purpose is not None and allowed_purpose not in entry["allowed_purposes"]:
            continue
        if has_simulator is not None and entry["has_simulator"] is not has_simulator:
            continue
        if mod_norm is not None:
            entry_mods = entry.get("analytical_modalities") or []
            if not any(m.lower() == mod_norm for m in entry_mods):
                continue
        if min_volume_at_most is not None or max_volume_at_least is not None:
            if not _entry_volume_satisfies(
                entry,
                min_volume_at_most=min_volume_at_most,
                max_volume_at_least=max_volume_at_least,
            ):
                continue
        if q_norm is not None:
            haystack = " ".join(
                [
                    entry["id"],
                    entry["name"],
                    entry["role"],
                    entry["spdx_license"],
                    " ".join(entry["supported_hardware"]),
                    " ".join(entry["protocol_formats"]),
                    " ".join(entry["tasks"]),
                    " ".join(entry.get("analytical_modalities") or []),
                ]
            ).lower()
            if q_norm not in haystack:
                continue
        result.append(entry)
    return result


def build_compatibility_matrix(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    """Build hardware-to-SDK-to-IR compatibility mappings from structured catalog metadata."""
    entries = catalog["entries"]
    targets = [
        ("Opentrons OT-2 / Flex", ("opentrons",)),
        ("Hamilton STAR / Vantage", ("hamilton",)),
        ("Tecan EVO / Fluent", ("tecan",)),
        ("Cloud Labs (ECL / Strateos)", ("strateos", "emerald", "cloud")),
        ("Chemputer Modular Synthesis", ("chemputer",)),
        ("Modular SDL / Beamlines (ROS2, EPICS)", ("ros2", "epics", "modular sdl")),
    ]
    rows: list[dict[str, Any]] = []
    for platform_label, keywords in targets:
        sdks: list[str] = []
        irs: list[str] = []
        simulators: list[str] = []
        autolab_links: list[str] = []
        modalities: list[str] = []
        for entry in entries:
            hw_joined = " ".join(entry["supported_hardware"]).lower()
            if not any(kw in hw_joined for kw in keywords):
                continue
            for mod in entry.get("analytical_modalities") or []:
                if mod not in modalities:
                    modalities.append(mod)
            if entry["category"] not in ("software", "autolab_sibling", "cloud_lab"):
                continue
            if entry["category"] == "autolab_sibling":
                autolab_links.append(entry["name"])
            else:
                sdks.append(entry["name"])
            for fmt in entry["protocol_formats"]:
                if fmt not in irs:
                    irs.append(fmt)
            if entry["has_simulator"] is True:
                simulators.append(entry["name"])
        rows.append(
            {
                "hardware_platform": platform_label,
                "open_sdks_and_drivers": sdks,
                "protocol_irs": irs,
                "offline_simulators": simulators,
                "autolab_integrations": autolab_links,
                "analytical_modalities": modalities,
            }
        )
    return rows


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def dump_catalog_yaml(data: Any, indent: int = 0) -> str:
    """Serialize catalog dictionary/list to deterministic, valid YAML using stdlib only."""
    pad = " " * indent
    lines: list[str] = []
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, (dict, list)) and val:
                lines.append(f"{pad}{key}:")
                lines.append(dump_catalog_yaml(val, indent + 2))
            elif isinstance(val, list) and not val:
                lines.append(f"{pad}{key}: []")
            elif isinstance(val, dict) and not val:
                lines.append(f"{pad}{key}: {{}}")
            else:
                lines.append(f"{pad}{key}: {_yaml_scalar(val)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item:
                items = list(item.items())
                first_k, first_v = items[0]
                if isinstance(first_v, (dict, list)) and first_v:
                    lines.append(f"{pad}- {first_k}:")
                    lines.append(dump_catalog_yaml(first_v, indent + 4))
                elif isinstance(first_v, list) and not first_v:
                    lines.append(f"{pad}- {first_k}: []")
                else:
                    lines.append(f"{pad}- {first_k}: {_yaml_scalar(first_v)}")
                for k, v in items[1:]:
                    if isinstance(v, (dict, list)) and v:
                        lines.append(f"{pad}  {k}:")
                        lines.append(dump_catalog_yaml(v, indent + 4))
                    elif isinstance(v, list) and not v:
                        lines.append(f"{pad}  {k}: []")
                    else:
                        lines.append(f"{pad}  {k}: {_yaml_scalar(v)}")
            else:
                lines.append(f"{pad}- {_yaml_scalar(item)}")
    else:
        lines.append(f"{pad}{_yaml_scalar(data)}")
    return "\n".join(lines)
