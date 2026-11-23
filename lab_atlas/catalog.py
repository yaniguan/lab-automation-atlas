"""Catalog loading, strict stdlib schema validation, filtering, and compatibility queries."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

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

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
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


def load_schema(path: str | Path | None = None) -> dict[str, Any]:
    """Load the JSON Schema definition for atlas.json."""
    resolved = resolve_schema_path(path)
    return json.loads(resolved.read_text(encoding="utf-8"))


def _is_bool(val: Any) -> bool:
    return isinstance(val, bool)


def _is_nonempty_str(val: Any, min_len: int = 1) -> bool:
    return isinstance(val, str) and len(val.strip()) >= min_len


def validate_catalog(catalog: dict[str, Any]) -> list[str]:
    """Validate catalog structure, enums, HTTPS URLs, and uniqueness with zero third-party deps."""
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
    if not isinstance(catalog["last_verified"], str) or not _DATE_RE.match(catalog["last_verified"]):
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
    for idx, entry in enumerate(entries):
        prefix = f"entries[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object.")
            continue
        miss = _ENTRY_KEYS - set(entry.keys())
        extra = set(entry.keys()) - _ENTRY_KEYS
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
        if not _is_nonempty_str(entry["spdx_license"], 2):
            errors.append(f"{prefix}.spdx_license must be >= 2 chars.")
        if not _is_bool(entry["osi_approved"]):
            errors.append(f"{prefix}.osi_approved must be boolean.")
        if not isinstance(entry["license_evidence"], str) or not _HTTPS_RE.match(entry["license_evidence"]):
            errors.append(f"{prefix}.license_evidence must be an https:// URL.")
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
                if not isinstance(link["url"], str) or not _HTTPS_RE.match(link["url"]):
                    errors.append(f"{prefix}.links[{lidx}].url must be an https:// URL, got {link['url']!r}.")

        for list_field in ("supported_hardware", "protocol_formats", "tasks"):
            val = entry[list_field]
            if not isinstance(val, list) or not all(_is_nonempty_str(x, 1) for x in val):
                errors.append(f"{prefix}.{list_field} must be a list of non-empty strings.")

        if entry["has_simulator"] is not None and not _is_bool(entry["has_simulator"]):
            errors.append(f"{prefix}.has_simulator must be boolean or null.")

        purposes = entry["allowed_purposes"]
        if not isinstance(purposes, list) or len(purposes) < 1 or any(p not in ALLOWED_PURPOSES for p in purposes):
            errors.append(f"{prefix}.allowed_purposes invalid: {purposes!r}")

        if entry["scraping_policy"] not in ALLOWED_SCRAPING_POLICIES:
            errors.append(f"{prefix}.scraping_policy invalid: {entry['scraping_policy']!r}")

        for nullable_str in ("contamination_warning", "huggingface_id", "doi", "record_count"):
            val = entry[nullable_str]
            if val is not None and not _is_nonempty_str(val, 1):
                errors.append(f"{prefix}.{nullable_str} must be non-empty string or null.")

        if not isinstance(entry["last_checked"], str) or not _DATE_RE.match(entry["last_checked"]):
            errors.append(f"{prefix}.last_checked invalid date: {entry['last_checked']!r}")

        # Policy invariant: held-out evaluation benchmarks in dataset category must declare contamination_warning
        if entry["category"] == "dataset" and entry["allowed_purposes"] == ["eval_only"]:
            if not entry["contamination_warning"]:
                errors.append(f"{prefix} is eval_only dataset but lacks contamination_warning.")

    return errors


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
    query: str | None = None,
) -> list[dict[str, Any]]:
    """Filter catalog entries across structured L5 planning and governance dimensions."""
    result: list[dict[str, Any]] = []
    q_norm = query.strip().lower() if query else None
    hw_norm = hardware.strip().lower() if hardware else None
    fmt_norm = protocol_format.strip().lower() if protocol_format else None
    lic_norm = spdx_license.strip().lower() if spdx_license else None

    for entry in entries:
        if category is not None and entry["category"] != category:
            continue
        if layer is not None and (entry["layer"] or "").upper() != layer.upper():
            continue
        if lic_norm is not None and lic_norm not in entry["spdx_license"].lower():
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
        for entry in entries:
            if entry["category"] not in ("software", "autolab_sibling", "cloud_lab"):
                continue
            hw_joined = " ".join(entry["supported_hardware"]).lower()
            if not any(kw in hw_joined for kw in keywords):
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
