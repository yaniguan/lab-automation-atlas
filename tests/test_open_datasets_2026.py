"""Tests for the 2024-2026 open wet-lab, spectroscopy, crystallography, acoustic, and embodied datasets."""

from __future__ import annotations

import copy
import json

import jsonschema
import pytest

import autolab_wire
from lab_atlas.catalog import (
    REPO_ROOT,
    RESOURCE_DIR,
    filter_entries,
    load_catalog,
    load_schema,
    validate_catalog,
)
from lab_atlas.cli import main as cli_main
from lab_atlas.render import check_readme_sync
from lab_atlas.spdx import evaluate_spdx_expression

NEW_2026_DATASET_SPECS: dict[str, tuple[str, bool, bool, list[str]]] = {
    "finebio": ("LicenseRef-FineBio-NonCommercial", False, False, ["eval_only"]),
    "chembench": ("MIT", True, True, ["eval_only"]),
    "bixbench": ("Apache-2.0", True, True, ["eval_only"]),
    "massspecgym": ("MIT", True, True, ["train_commercial", "train_academic", "eval_only"]),
    "multimodal-spectroscopic-dataset": (
        "CDLA-Sharing-1.0",
        False,
        True,
        ["train_academic", "eval_only"],
    ),
    "aqsoldb": ("CC0-1.0", False, True, ["train_commercial", "train_academic", "eval_only"]),
    "calisol-23": ("NOASSERTION", False, False, ["eval_only"]),
    "crystallography-open-database": (
        "CC0-1.0",
        False,
        True,
        ["train_commercial", "train_academic", "eval_only", "tool_integration"],
    ),
    "omat24": ("CC-BY-4.0", False, True, ["train_commercial", "train_academic", "eval_only"]),
    "dcase-task2-asd": ("CC-BY-NC-SA-4.0", False, False, ["train_academic", "eval_only"]),
    "droid": ("CC-BY-4.0", False, True, ["train_commercial", "train_academic", "eval_only"]),
    "bigsoldb-2": ("CC-BY-4.0", False, True, ["train_commercial", "train_academic", "eval_only"]),
    "bh-hte-ood": ("CC-BY-4.0", False, True, ["train_commercial", "train_academic", "eval_only"]),
    "paroutes": ("CC-BY-4.0", False, True, ["train_commercial", "train_academic", "eval_only"]),
    "orderly": ("CC-BY-4.0", False, True, ["train_commercial", "train_academic", "eval_only"]),
    "coconut-2": (
        "CC0-1.0",
        False,
        True,
        ["train_commercial", "train_academic", "eval_only", "tool_integration"],
    ),
    "opxrd": ("CC-BY-4.0", False, True, ["train_commercial", "train_academic", "eval_only"]),
    "alab-gpss": ("CC-BY-4.0", False, True, ["train_commercial", "train_academic", "eval_only"]),
    "ehrsql-2024": ("CC-BY-4.0", False, True, ["eval_only"]),
    "spider2": ("MIT", True, True, ["eval_only"]),
    "putnambench": ("Apache-2.0 AND MIT", True, True, ["eval_only"]),
    "uci-gas-sensor-drift": (
        "CC-BY-4.0",
        False,
        True,
        ["train_commercial", "train_academic", "eval_only"],
    ),
    "layered-depth": ("CC0-1.0", False, True, ["train_commercial", "train_academic", "eval_only"]),
}

NEW_FRONTIER_SOFTWARE_SPECS: dict[str, tuple[str, bool, bool]] = {
    "pyjobshop": ("MIT", True, True),
    "lerobot": ("Apache-2.0", True, True),
}


def test_open_datasets_2026_catalog_schema_and_sync() -> None:
    """Verify all 84 entries (including 23 added 2024-2026 datasets + PyJobShop/LeRobot) pass schema and sync."""
    catalog = load_catalog()
    schema = load_schema()

    jsonschema.Draft202012Validator(schema).validate(catalog)
    assert validate_catalog(catalog) == []
    assert len(catalog["entries"]) == 84
    assert check_readme_sync(REPO_ROOT / "README.md", catalog) is True
    assert (REPO_ROOT / "atlas.json").read_text(encoding="utf-8") == (
        RESOURCE_DIR / "atlas.json"
    ).read_text(encoding="utf-8")

    datasets = {e["id"]: e for e in catalog["entries"] if e["category"] == "dataset"}
    assert len(datasets) == 29

    software = {e["id"]: e for e in catalog["entries"] if e["category"] == "software"}
    assert len(software) == 14
    for sw_id, (sw_spdx, sw_osi, sw_comm) in NEW_FRONTIER_SOFTWARE_SPECS.items():
        assert sw_id in software, f"Missing expected frontier solver/stack {sw_id}"
        assert software[sw_id]["spdx_license"] == sw_spdx
        assert software[sw_id]["osi_approved"] is sw_osi
        assert software[sw_id]["commercial_use_ok"] is sw_comm

    for ds_id, (expected_spdx, expected_osi, expected_comm, expected_purposes) in NEW_2026_DATASET_SPECS.items():
        assert ds_id in datasets, f"Missing expected 2024-2026 dataset {ds_id}"
        entry = datasets[ds_id]
        assert entry["spdx_license"] == expected_spdx
        assert entry["osi_approved"] is expected_osi
        assert entry["commercial_use_ok"] is expected_comm
        assert entry["allowed_purposes"] == expected_purposes
        assert entry["record_count"]
        assert len(entry["tasks"]) >= 2
        assert len(entry["links"]) >= 1


def test_open_datasets_2026_spdx_lattice_posture_alignment() -> None:
    """Verify SPDX evaluation matches permissive, share_alike, non_commercial, and custom_terms policies."""
    catalog = load_catalog()
    by_id = {e["id"]: e for e in catalog["entries"]}

    for permissive_id in (
        "massspecgym",
        "aqsoldb",
        "crystallography-open-database",
        "omat24",
        "droid",
    ):
        ev = evaluate_spdx_expression(
            by_id[permissive_id]["spdx_license"],
            allow_policy_aliases=False,
            require_uppercase_operators=True,
        )
        assert ev.spdx_known is True
        assert ev.license_class == "permissive"
        assert ev.commercial_train_ok is True
        assert ev.academic_train_ok is True

    msd_ev = evaluate_spdx_expression(by_id["multimodal-spectroscopic-dataset"]["spdx_license"])
    assert msd_ev.spdx_known is True
    assert msd_ev.license_class == "share_alike"
    assert msd_ev.academic_train_ok is True
    assert msd_ev.commercial_train_ok is False
    assert "train_commercial" not in by_id["multimodal-spectroscopic-dataset"]["allowed_purposes"]

    dcase_ev = evaluate_spdx_expression(by_id["dcase-task2-asd"]["spdx_license"])
    assert dcase_ev.spdx_known is True
    assert dcase_ev.license_class == "non_commercial"
    assert dcase_ev.academic_train_ok is True
    assert dcase_ev.commercial_train_ok is False
    assert "train_commercial" not in by_id["dcase-task2-asd"]["allowed_purposes"]

    finebio_ev = evaluate_spdx_expression(by_id["finebio"]["spdx_license"])
    assert finebio_ev.spdx_known is True
    assert finebio_ev.license_class == "custom_terms"
    assert finebio_ev.academic_train_ok is False
    assert finebio_ev.commercial_train_ok is False


@pytest.mark.parametrize(
    "eval_only_id",
    ["finebio", "chembench", "bixbench", "ehrsql-2024", "spider2", "putnambench"],
)
def test_open_datasets_2026_eval_only_contamination_warnings_required(eval_only_id: str) -> None:
    """Verify held-out 2024-2026 evaluation suites enforce non-empty contamination_warning invariants."""
    catalog = load_catalog()
    by_id = {e["id"]: e for e in catalog["entries"]}
    entry = by_id[eval_only_id]

    assert entry["allowed_purposes"] == ["eval_only"]
    assert entry["contamination_warning"]

    mutated = copy.deepcopy(catalog)
    target = next(e for e in mutated["entries"] if e["id"] == eval_only_id)
    target["contamination_warning"] = None
    errs = validate_catalog(mutated)
    assert any(eval_only_id in err and "contamination_warning" in err for err in errs)


@pytest.mark.parametrize(
    "eval_url",
    [
        "https://github.com/lamalab-org/chembench",
        "https://huggingface.co/datasets/jablonkagroup/ChemBench",
        "https://github.com/Future-House/BixBench",
        "https://huggingface.co/datasets/futurehouse/BixBench",
        "https://github.com/aistairc/FineBio",
        "https://github.com/glee4810/ehrsql-2024",
        "https://github.com/xlang-ai/Spider2",
        "https://huggingface.co/datasets/xlangai/spider2-lite",
        "https://github.com/trishullab/PutnamBench",
        "https://huggingface.co/datasets/amitayusht/PutnamBench",
    ],
)
def test_autolab_wire_blocks_2026_eval_only_benchmarks_from_training(eval_url: str) -> None:
    """Verify autolab_wire cross-matches new eval_only dataset URLs and blocks training even under MIT override."""
    blocked = autolab_wire.process_packet(
        {
            "target_platform": "opentrons_ot2",
            "resource_url": eval_url,
            "license_class": "MIT",
            "for_training": True,
            "commercial": False,
        }
    )
    assert blocked["halted"] is True
    assert blocked["halt_reason"] == "L5_ATLAS_LICENSE_OR_URL_BLOCK"
    assert blocked["platform_grounding"]["effective_license_class"] == "eval_only"
    assert blocked["platform_grounding"]["license_ok"] is False

    # Pure benchmark evaluation (for_training=False) remains allowed when SPDX is valid
    eval_pass = autolab_wire.process_packet(
        {
            "target_platform": "opentrons_ot2",
            "resource_url": eval_url,
            "license_class": "eval_only",
            "for_training": False,
            "commercial": True,
        }
    )
    assert eval_pass["halted"] is False
    assert eval_pass["platform_grounding"]["license_ok"] is True


def test_autolab_wire_commercial_vs_academic_gating_for_2026_datasets() -> None:
    """Verify wire node distinguishes permissive, share-alike (MSD), and non-commercial (DCASE) training."""
    for restricted_url in (
        "https://github.com/rxn4chemistry/multimodal-spectroscopic-dataset",
        "https://github.com/nttcslab/dcase2023_task2_baseline_ae",
    ):
        comm_blocked = autolab_wire.process_packet(
            {
                "resource_url": restricted_url,
                "license_class": "MIT",
                "for_training": True,
                "commercial": True,
            }
        )
        assert comm_blocked["halted"] is True
        assert comm_blocked["halt_reason"] == "L5_ATLAS_LICENSE_OR_URL_BLOCK"

        acad_ok = autolab_wire.process_packet(
            {
                "resource_url": restricted_url,
                "license_class": "MIT",
                "for_training": True,
                "commercial": False,
            }
        )
        assert acad_ok["halted"] is False
        assert acad_ok["platform_grounding"]["license_ok"] is True

    for permissive_url in (
        "https://huggingface.co/datasets/roman-bushuiev/MassSpecGym",
        "https://github.com/mcsorkun/AqSolDB",
        "https://www.crystallography.net/cod/",
        "https://huggingface.co/datasets/facebook/OMAT24",
        "https://droid-dataset.github.io/",
    ):
        comm_ok = autolab_wire.process_packet(
            {
                "resource_url": permissive_url,
                "license_class": "CC-BY-4.0",
                "for_training": True,
                "commercial": True,
            }
        )
        assert comm_ok["halted"] is False, f"Expected commercial training pass for {permissive_url}"
        assert comm_ok["platform_grounding"]["license_ok"] is True


def test_open_datasets_2026_analytical_modalities_and_cli_queries(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify modality indexing (LC-MS, NMR, FTIR, XRD, Raman, acoustic, optical) and CLI purpose filters."""
    catalog = load_catalog()
    entries = catalog["entries"]

    lcms_ids = {e["id"] for e in filter_entries(entries, category="dataset", modality="LC-MS")}
    assert {"massspecgym", "multimodal-spectroscopic-dataset", "chembench"} <= lcms_ids

    nmr_ids = {e["id"] for e in filter_entries(entries, category="dataset", modality="NMR")}
    assert {"multimodal-spectroscopic-dataset", "chembench"} <= nmr_ids

    xrd_ids = {e["id"] for e in filter_entries(entries, category="dataset", modality="XRD")}
    assert {"crystallography-open-database", "omat24", "chembench", "opxrd", "alab-gpss"} <= xrd_ids

    raman_ids = {e["id"] for e in filter_entries(entries, category="dataset", modality="Raman")}
    assert "crystallography-open-database" in raman_ids

    gas_ids = {
        e["id"]
        for e in filter_entries(entries, category="dataset", modality="chemiresistive_gas_sensor")
    }
    assert "uci-gas-sensor-drift" in gas_ids

    acoustic_ids = {
        e["id"] for e in filter_entries(entries, category="dataset", modality="acoustic_monitoring")
    }
    assert "dcase-task2-asd" in acoustic_ids

    optical_ids = {
        e["id"] for e in filter_entries(entries, category="dataset", modality="optical_imaging")
    }
    assert {"finebio", "droid", "layered-depth"} <= optical_ids

    rc = cli_main(["list", "--category", "dataset", "--purpose", "train_commercial", "--json"])
    assert rc == 0
    comm_trainable = {e["id"] for e in json.loads(capsys.readouterr().out)}
    assert {
        "massspecgym",
        "aqsoldb",
        "bigsoldb-2",
        "bh-hte-ood",
        "paroutes",
        "orderly",
        "coconut-2",
        "opxrd",
        "alab-gpss",
        "uci-gas-sensor-drift",
        "layered-depth",
        "crystallography-open-database",
        "omat24",
        "droid",
    } <= comm_trainable
    assert {
        "finebio",
        "chembench",
        "bixbench",
        "calisol-23",
        "ehrsql-2024",
        "spider2",
        "putnambench",
        "multimodal-spectroscopic-dataset",
        "dcase-task2-asd",
    }.isdisjoint(comm_trainable)
