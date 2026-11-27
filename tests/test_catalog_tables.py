"""Tests for atlas.json schema, SPDX/OSI/assayfold metadata, compatibility matrix, CI, and README sync."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

from lab_atlas.catalog import (
    REPO_ROOT,
    RESOURCE_DIR,
    build_compatibility_matrix,
    load_catalog,
    load_schema,
    validate_catalog,
)
from lab_atlas.render import TABLE_HEADER, check_readme_sync


def test_atlas_json_schema_validation_and_additional_properties_forbid() -> None:
    """Issue #8: Validate atlas.json against Draft 2020-12 JSON Schema and stdlib validator."""
    catalog = load_catalog()
    schema = load_schema()

    jsonschema.Draft202012Validator(schema).validate(catalog)
    assert validate_catalog(catalog) == []
    assert len(catalog["entries"]) >= 50

    mutated = copy.deepcopy(catalog)
    mutated["entries"][0]["unexpected_field"] = "forbidden"
    assert validate_catalog(mutated)
    validator = jsonschema.Draft202012Validator(schema)
    assert list(validator.iter_errors(mutated))


def test_readme_and_package_resources_byte_for_byte_sync() -> None:
    """Issue #8: Ensure README.md and package resources stay synchronized with atlas.json."""
    catalog = load_catalog()
    readme_path = REPO_ROOT / "README.md"
    assert check_readme_sync(readme_path, catalog) is True

    root_atlas = (REPO_ROOT / "atlas.json").read_text(encoding="utf-8")
    pkg_atlas = (RESOURCE_DIR / "atlas.json").read_text(encoding="utf-8")
    assert root_atlas == pkg_atlas


def test_software_spdx_licenses_and_non_osi_flags() -> None:
    """Issue #9: Verify all 14 software entries have SPDX licenses, evidence URLs, and OSI flags."""
    catalog = load_catalog()
    software = [e for e in catalog["entries"] if e["category"] == "software"]
    assert len(software) == 14
    by_id = {e["id"]: e for e in software}

    assert by_id["opentrons-python-api-v2"]["spdx_license"] == "Apache-2.0"
    assert by_id["pylabrobot"]["spdx_license"] == "MIT"
    assert by_id["or-tools"]["spdx_license"] == "Apache-2.0"
    assert by_id["bluesky"]["spdx_license"] == "BSD-3-Clause"
    assert by_id["pyjobshop"]["spdx_license"] == "MIT"
    assert by_id["lerobot"]["spdx_license"] == "Apache-2.0"
    assert by_id["xdl-generation"]["osi_approved"] is False
    assert by_id["xdl-chemputer"]["osi_approved"] is False

    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "*(non-OSI)*" in readme_text
    assert f"`{len(catalog['entries'])}` typed entries" in readme_text


def test_dataset_spdx_commercial_and_contamination_alignment_with_assayfold() -> None:
    """Issues #10, #17, #19: SPDX licenses, commercial_use_ok, HF/DOI/counts, and eval_only guards."""
    catalog = load_catalog()
    datasets = {e["id"]: e for e in catalog["entries"] if e["category"] == "dataset"}

    assert datasets["protocols-io"]["spdx_license"] == "CC-BY-4.0"
    assert datasets["protocols-io"]["commercial_use_ok"] is True
    assert datasets["protocols-io"]["scraping_policy"] == "public_api_rate_limited"

    assert datasets["bio-protocol"]["spdx_license"] == "LicenseRef-Per-Article"
    assert datasets["bio-protocol"]["commercial_use_ok"] is False
    assert datasets["bio-protocol"]["scraping_policy"] == "no_bulk_scraping_per_article"

    assert datasets["wlp"]["spdx_license"] == "MIT"
    assert datasets["wlp"]["commercial_use_ok"] is True
    assert "train_commercial" in datasets["wlp"]["allowed_purposes"]
    assert "622" in (datasets["wlp"]["record_count"] or "")

    assert datasets["bioprobench"]["spdx_license"] == "CC-BY-NC-4.0"
    assert datasets["bioprobench"]["commercial_use_ok"] is False
    assert datasets["bioprobench"]["huggingface_id"] == "BioProBench/BioProBench"
    assert datasets["bioprobench"]["allowed_purposes"] == ["eval_only"]
    assert datasets["bioprobench"]["contamination_warning"]

    assert datasets["lab-bench"]["spdx_license"] == "CC-BY-SA-4.0"
    assert datasets["lab-bench"]["commercial_use_ok"] is True
    assert datasets["lab-bench"]["huggingface_id"] == "futurehouse/lab-bench"
    assert datasets["lab-bench"]["allowed_purposes"] == ["eval_only"]
    assert "canary" in (datasets["lab-bench"]["contamination_warning"] or "").lower()
    assert "1,967" in (datasets["lab-bench"]["record_count"] or "")

    assert datasets["bioplanner"]["allowed_purposes"] == ["eval_only"]
    assert datasets["bioplanner"]["doi"] == "10.48550/arXiv.2310.10632"


def test_complete_autolab_sibling_suite_and_layers() -> None:
    """Issue #11: Verify complete L0-L6 Auto-Lab repository suite is indexed."""
    catalog = load_catalog()
    siblings = {e["name"]: e for e in catalog["entries"] if e["category"] == "autolab_sibling"}
    expected_repos = {
        "auto-lab": "Hub",
        "lab-ask-why": "L6",
        "lab-decide": "L6",
        "YLM": "L6",
        "buy-or-make": "L5",
        "labshift": "L5",
        "lab-automation-atlas": "L5",
        "lab-rehearsal": "L4",
        "lab-verify": "L4",
        "lab-attrib": "L4",
        "WignerFlow": "L4",
        "labbench-posttrain": "L3",
        "twinstep": "L3",
        "labfill": "L3",
        "lab-ears": "L2",
        "assayfold": "L2",
        "ouroboros-ocsr": "L2",
        "stepbot": "L1",
        "lab-hands": "L1",
        "lab-feet": "L0",
        "equivariant-gpu-lab": "L0",
    }
    for name, expected_layer in expected_repos.items():
        assert name in siblings, f"Missing sibling repo {name}"
        assert siblings[name]["layer"] == expected_layer


def test_hardware_compatibility_matrix_and_maintenance_statuses() -> None:
    """Issues #12 & #13: Compatibility matrix and archived/legacy/restructured flags."""
    catalog = load_catalog()
    by_id = {e["id"]: e for e in catalog["entries"]}

    assert by_id["aquarium"]["maintenance_status"] == "archived"
    assert by_id["strateos"]["maintenance_status"] == "commercial_restructured"
    assert by_id["autoprotocol"]["maintenance_status"] == "legacy"
    assert by_id["xdl-generation"]["maintenance_status"] == "legacy"

    matrix = build_compatibility_matrix(catalog)
    by_platform = {r["hardware_platform"]: r for r in matrix}
    assert "PyLabRobot" in by_platform["Hamilton STAR / Vantage"]["open_sdks_and_drivers"]
    assert "SiLA 2" in by_platform["Hamilton STAR / Vantage"]["open_sdks_and_drivers"]
    assert "Opentrons Python API v2" in by_platform["Opentrons OT-2 / Flex"]["open_sdks_and_drivers"]
    assert "stepbot" in by_platform["Opentrons OT-2 / Flex"]["autolab_integrations"]


def test_standardized_headers_chemistry_and_l4_cross_references() -> None:
    """Issues #15, #16, #21: Standardized 6-column tables, chemistry ecosystem, and L4 cross-refs."""
    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert readme_text.count(TABLE_HEADER) == 7

    catalog = load_catalog()
    chem_ids = {e["id"] for e in catalog["entries"] if e["category"] == "chemistry_and_procurement"}
    assert {"open-reaction-database", "uspto-lowe", "aizynthfinder", "rdkit", "pubchem-pug-rest", "elabftw"} <= chem_ids

    sim_ids = {e["id"] for e in catalog["entries"] if e["category"] == "simulation_and_verification"}
    assert {"labutopia", "autobio", "matterix", "lean4-minif2f", "spider-2"} <= sim_ids


def test_workflow_and_gitignore_hygiene() -> None:
    """Issues #7 & #22: Verify links.yml triggers/permissions/timeouts and .gitignore patterns."""
    wf = (REPO_ROOT / ".github" / "workflows" / "links.yml").read_text(encoding="utf-8")
    assert "pull_request:" in wf
    assert "workflow_dispatch:" in wf
    assert "permissions:" in wf and "contents: read" in wf
    assert "timeout-minutes:" in wf
    assert "pytest" in wf
    assert "upload-artifact@v4" in wf
    assert "leanprover/lean-action@v1" in wf
    assert "scripts/verify_lean_parity.py" in wf

    gi = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (".venv/", "venv/", "*.py[cod]", "build/", "dist/", ".ruff_cache/", "/reports/"):
        assert pattern in gi


def test_issue_25_spdx_ast_filter_and_cross_category_eval_only_warning() -> None:
    """Issue #25: Verify compound SPDX filtering and cross-category eval_only contamination_warning check."""
    from lab_atlas.catalog import filter_entries
    from lab_atlas.spdx import SpdxParseError, parse_spdx_expression

    catalog = load_catalog()
    by_id = {e["id"]: e for e in catalog["entries"]}
    assert by_id["autobio"]["allowed_purposes"] == ["eval_only"]
    assert by_id["autobio"]["contamination_warning"]

    # Removing contamination_warning on simulation_and_verification eval_only entry must fail validation
    mutated = copy.deepcopy(catalog)
    autobio_mut = next(e for e in mutated["entries"] if e["id"] == "autobio")
    autobio_mut["contamination_warning"] = None
    errs = validate_catalog(mutated)
    assert any("autobio" in e and "contamination_warning" in e for e in errs)

    # Compound SPDX filter: `--license MIT` must reject NC-tainted `MIT AND CC-BY-NC-4.0` while keeping `MIT OR CC-BY-NC-4.0`
    synthetic = [
        dict(by_id["wlp"], id="pure-mit", spdx_license="MIT"),
        dict(by_id["wlp"], id="dual-mit-or-nc", spdx_license="MIT OR CC-BY-NC-4.0"),
        dict(by_id["wlp"], id="conj-mit-and-bsd", spdx_license="MIT AND BSD-3-Clause"),
        dict(by_id["wlp"], id="tainted-mit-and-nc", spdx_license="MIT AND CC-BY-NC-4.0"),
    ]
    matched_mit = {e["id"] for e in filter_entries(synthetic, spdx_license="MIT")}
    assert matched_mit == {"pure-mit", "dual-mit-or-nc", "conj-mit-and-bsd"}

    with pytest.raises(SpdxParseError):
        parse_spdx_expression("(MIT OR Apache-2.0")


def test_issue_28_hardware_capabilities_and_analytical_modalities_schema_invariants() -> None:
    """Issue #28: Verify hardware_capabilities bounds, analytical_modalities enum, and closed schema."""
    import pytest as _pytest

    from lab_atlas.catalog import filter_entries

    _ = _pytest
    catalog = load_catalog()
    schema = load_schema()
    validator = jsonschema.Draft202012Validator(schema)

    by_id = {e["id"]: e for e in catalog["entries"]}
    assert by_id["opentrons"]["hardware_capabilities"]["api_level"] == "2.16"
    assert by_id["opentrons"]["hardware_capabilities"]["max_deck_slots"] == 11
    assert by_id["opentrons"]["hardware_capabilities"]["min_volume_ul"] == 1.0
    assert "XRD" in by_id["lab-attrib"]["analytical_modalities"]
    assert "Raman" in by_id["emerald-cloud-lab"]["analytical_modalities"]
    assert "SAXS_WAXS" in by_id["bluesky"]["analytical_modalities"]

    raman_ids = {e["id"] for e in filter_entries(catalog["entries"], modality="Raman")}
    assert {"lab-attrib", "emerald-cloud-lab", "bluesky", "acceleration-consortium"} <= raman_ids

    sub_ul_ids = {e["id"] for e in filter_entries(catalog["entries"], min_volume_at_most=0.5)}
    assert {"hamilton", "tecan", "automata", "emerald-cloud-lab"} <= sub_ul_ids

    # Inverted volume bounds fail validate_catalog
    bad_vol = copy.deepcopy(catalog)
    ot = next(e for e in bad_vol["entries"] if e["id"] == "opentrons")
    ot["hardware_capabilities"]["min_volume_ul"] = 5000.0
    ot["hardware_capabilities"]["max_volume_ul"] = 10.0
    assert any("inverted volume bounds" in err for err in validate_catalog(bad_vol))

    # Unknown extra key inside hardware_capabilities fails both Draft202012Validator and validate_catalog
    bad_extra = copy.deepcopy(catalog)
    ot2 = next(e for e in bad_extra["entries"] if e["id"] == "opentrons")
    ot2["hardware_capabilities"]["undeclared_field"] = 42
    assert validate_catalog(bad_extra)
    assert list(validator.iter_errors(bad_extra))
