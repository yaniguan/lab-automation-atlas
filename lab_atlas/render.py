"""Deterministic Markdown table and compatibility matrix renderer synchronized with atlas.json."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import build_compatibility_matrix

BEGIN_MARKER = "<!-- BEGIN GENERATED CATALOG -->"
END_MARKER = "<!-- END GENERATED CATALOG -->"

TABLE_HEADER = "| Name | Role / Type | Status | License | Commercial Use | Links |"
TABLE_DIVIDER = "|---|---|---|---|---|---|"


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _format_name_cell(entry: dict[str, Any]) -> str:
    name = _escape_cell(entry["name"])
    if entry["layer"]:
        return f"**{name}** (`{entry['layer']}`)"
    return name


def _format_role_cell(entry: dict[str, Any]) -> str:
    parts: list[str] = [_escape_cell(entry["role"]).rstrip(".") + "."]
    if entry["record_count"]:
        parts.append(f"Scale: {_escape_cell(entry['record_count'])}.")
    if entry["tasks"]:
        tasks_str = ", ".join(f"`{t}`" for t in entry["tasks"])
        parts.append(f"Tasks: {tasks_str}.")
    if entry["category"] in ("dataset", "chemistry_and_procurement"):
        purposes_str = ", ".join(f"`{p}`" for p in entry["allowed_purposes"])
        parts.append(f"Policy: {purposes_str} (`{entry['scraping_policy']}`).")
    if entry["contamination_warning"]:
        parts.append(f"**Contamination guard**: {_escape_cell(entry['contamination_warning'])}")
    return " ".join(parts)


def _format_license_cell(entry: dict[str, Any]) -> str:
    spdx = _escape_cell(entry["spdx_license"])
    ev = entry["license_evidence"]
    linked = f"[`{spdx}`]({ev})"
    if entry["category"] == "software" and not entry["osi_approved"]:
        return f"{linked} *(non-OSI)*"
    return linked


def _format_links_cell(entry: dict[str, Any]) -> str:
    rendered = [f"[{_escape_cell(item['label'])}]({item['url']})" for item in entry["links"]]
    return ", ".join(rendered)


def render_compatibility_markdown(catalog: dict[str, Any]) -> str:
    """Render the Hardware-to-SDK-to-IR compatibility matrix section."""
    matrix = build_compatibility_matrix(catalog)
    lines = [
        "## Hardware-to-SDK-to-IR compatibility matrix",
        "",
        "Generated from structured `supported_hardware`, `protocol_formats`, and `has_simulator` fields in [`atlas.json`](atlas.json):",
        "",
        "| Hardware Platform | Open-Source SDKs / Drivers | Protocol IRs / Standards | Offline Simulators | Auto-Lab Integrations |",
        "|---|---|---|---|---|",
    ]
    for row in matrix:
        sdks = ", ".join(row["open_sdks_and_drivers"]) if row["open_sdks_and_drivers"] else "—"
        irs = ", ".join(f"`{x}`" for x in row["protocol_irs"]) if row["protocol_irs"] else "—"
        sims = ", ".join(row["offline_simulators"]) if row["offline_simulators"] else "—"
        auto = ", ".join(f"`{x}`" for x in row["autolab_integrations"]) if row["autolab_integrations"] else "—"
        lines.append(
            f"| {_escape_cell(row['hardware_platform'])} | {_escape_cell(sdks)} | {irs} | {_escape_cell(sims)} | {auto} |"
        )
    return "\n".join(lines)


def render_catalog_markdown(catalog: dict[str, Any]) -> str:
    """Render all catalog sections and the compatibility matrix deterministically."""
    blocks: list[str] = []
    entries = catalog["entries"]

    for cat in catalog["categories"]:
        cat_id = cat["id"]
        cat_entries = [e for e in entries if e["category"] == cat_id]
        if not cat_entries:
            continue
        section_lines = [
            f"## {cat['title']}",
            "",
            cat["description"],
            "",
            TABLE_HEADER,
            TABLE_DIVIDER,
        ]
        for entry in cat_entries:
            name_cell = _format_name_cell(entry)
            role_cell = _format_role_cell(entry)
            status_cell = f"`{entry['maintenance_status']}`"
            lic_cell = _format_license_cell(entry)
            comm_cell = "yes" if entry["commercial_use_ok"] else "no"
            links_cell = _format_links_cell(entry)
            section_lines.append(
                f"| {name_cell} | {role_cell} | {status_cell} | {lic_cell} | {comm_cell} | {links_cell} |"
            )
        blocks.append("\n".join(section_lines))

    blocks.append(render_compatibility_markdown(catalog))
    return "\n\n".join(blocks)


def build_synced_readme_text(readme_text: str, catalog: dict[str, Any]) -> str:
    """Replace content between BEGIN_MARKER and END_MARKER in README.md."""
    start = readme_text.find(BEGIN_MARKER)
    end = readme_text.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise ValueError(
            f"README.md must contain '{BEGIN_MARKER}' followed by '{END_MARKER}'."
        )
    generated = render_catalog_markdown(catalog)
    replacement = f"{BEGIN_MARKER}\n\n{generated}\n\n{END_MARKER}"
    return readme_text[:start] + replacement + readme_text[end + len(END_MARKER) :]


def check_readme_sync(readme_path: Path, catalog: dict[str, Any]) -> bool:
    """Return True if README.md matches the catalog rendering byte-for-byte."""
    current = readme_path.read_text(encoding="utf-8")
    expected = build_synced_readme_text(current, catalog)
    return current == expected


def sync_readme(readme_path: Path, catalog: dict[str, Any]) -> bool:
    """Update README.md in place from catalog. Returns True if modified."""
    current = readme_path.read_text(encoding="utf-8")
    expected = build_synced_readme_text(current, catalog)
    if current == expected:
        return False
    readme_path.write_text(expected, encoding="utf-8")
    return True
