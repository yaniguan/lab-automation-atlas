"""Tests for the Auto-Lab 15-repository wire node (autolab_wire.py) and lab-attrib registration."""

from __future__ import annotations

import pytest

import autolab_wire
from lab_atlas.catalog import load_catalog


def test_valid_platform_grounding_and_immutability() -> None:
    """Verify default and explicit L5 platform grounding without mutating the input packet."""
    original = {
        "target_platform": "opentrons_ot2",
        "resource_url": "https://github.com/yaniguan/stepbot",
        "license_class": "MIT",
        "for_training": True,
    }
    out = autolab_wire.process_packet(original)

    assert "schema_version" not in original
    assert autolab_wire.REPO_ID == "lab-automation-atlas"
    assert autolab_wire.LAYER == "L5"
    assert out["schema_version"] == "autolab-wire/v1"
    assert out["halted"] is False
    assert out["halt_reason"] is None

    grounding = out["platform_grounding"]
    assert grounding["platform"] == "opentrons_ot2"
    assert grounding["api_level"] == "2.16"
    assert grounding["max_deck_slots"] == 11
    assert grounding["license_ok"] is True
    assert grounding["registered_entries"] >= 59

    assert out["trace"][-1]["repo"] == "lab-automation-atlas"
    assert out["trace"][-1]["layer"] == "L5"
    assert out["trace"][-1]["status"] == "PASS"
    assert out["bottom_reasoning_traces"][-1]["invariant"] == "eval_only_blocked_from_training"


@pytest.mark.parametrize("bad_license", ["eval_only", "CC-BY-NC-2.0", "non_commercial"])
def test_eval_only_and_non_commercial_blocked_from_training(bad_license: str) -> None:
    """Verify Lean eval_only_blocked_from_training blocks restricted corpora when for_training=True."""
    blocked = autolab_wire.process_packet(
        {
            "resource_url": "https://github.com/Future-House/LAB-Bench",
            "license_class": bad_license,
            "for_training": True,
        }
    )
    assert blocked["halted"] is True
    assert blocked["halt_reason"] == "L5_ATLAS_LICENSE_OR_URL_BLOCK"
    assert blocked["platform_grounding"]["license_ok"] is False
    assert blocked["trace"][-1]["status"] == "BLOCK"
    assert blocked["bottom_reasoning_traces"][-1]["invariant"] == "eval_only_blocked_from_training"

    # Evaluation-only runs (for_training=False) remain allowed over valid HTTPS targets
    eval_run = autolab_wire.process_packet(
        {
            "resource_url": "https://github.com/Future-House/LAB-Bench",
            "license_class": "eval_only",
            "for_training": False,
        }
    )
    assert eval_run["halted"] is False
    assert eval_run["platform_grounding"]["license_ok"] is True


@pytest.mark.parametrize(
    "unsafe_url",
    [
        "http://github.com/yaniguan/stepbot",
        "ftp://mirror.example.org/protocol.yaml",
        "https://127.0.0.1:8080/internal",
        "https://localhost/admin",
    ],
)
def test_non_https_and_ssrf_urls_blocked(unsafe_url: str) -> None:
    """Verify non-HTTPS schemes and loopback/local SSRF targets trigger L5_ATLAS_LICENSE_OR_URL_BLOCK."""
    out = autolab_wire.process_packet(
        {
            "resource_url": unsafe_url,
            "license_class": "MIT",
            "for_training": False,
        }
    )
    assert out["halted"] is True
    assert out["halt_reason"] == "L5_ATLAS_LICENSE_OR_URL_BLOCK"
    assert out["platform_grounding"]["license_ok"] is False
    assert out["trace"][-1]["status"] == "BLOCK"


def test_halted_packet_passthrough() -> None:
    """Verify upstream halted packets pass through unchanged without overwriting halt_reason."""
    halted_in = {
        "halted": True,
        "halt_reason": "L6_ABSTAIN",
        "trace": [{"repo": "lab-decide", "layer": "L6", "status": "ABSTAIN", "summary": "OOD"}],
    }
    out = autolab_wire.process_packet(halted_in)
    assert out["halted"] is True
    assert out["halt_reason"] == "L6_ABSTAIN"
    assert len(out["trace"]) == 1
    assert "platform_grounding" not in out


def test_lab_attrib_registered_in_atlas_json_and_readme() -> None:
    """Verify the 15th Auto-Lab sibling repository lab-attrib is registered in atlas.json and README.md."""
    catalog = load_catalog(autolab_wire.REPO_DIR / "atlas.json", validate=True)
    by_id = {entry["id"]: entry for entry in catalog["entries"]}
    assert "lab-attrib" in by_id

    attrib = by_id["lab-attrib"]
    assert attrib["name"] == "lab-attrib"
    assert attrib["category"] == "autolab_sibling"
    assert attrib["layer"] == "L4"
    assert attrib["spdx_license"] == "MIT"
    assert attrib["osi_approved"] is True
    assert attrib["commercial_use_ok"] is True
    assert any(link["url"] == "https://github.com/yaniguan/lab-attrib" for link in attrib["links"])

    readme_text = (autolab_wire.REPO_DIR / "README.md").read_text(encoding="utf-8")
    assert "**lab-attrib** (`L4`)" in readme_text
    assert "https://github.com/yaniguan/lab-attrib" in readme_text


@pytest.mark.parametrize(
    ("target_platform", "expected_api", "expected_slots", "expected_arch", "expected_member"),
    [
        ("opentrons_ot2", "2.16", 11, "sbs_fixed_slots", "stepbot"),
        ("opentrons_flex", "2.20", 12, "sbs_coordinate_grid", "opentrons"),
        ("hamilton_star", "VENUS-6", None, "carrier_rails", "pylabrobot"),
        ("tecan_fluent", "FluentControl-3.5", None, "carrier_rails", "sila-2"),
        ("chemputer", "XDL-2.0", None, "flow_batch_reactor", "xdl-chemputer"),
        ("emerald_cloud_lab", "SLL-v1", None, "cloud_symbolic_facility", "emerald-cloud-lab"),
    ],
)
def test_issue_27_dynamic_platform_grounding_per_target_platform(
    target_platform: str,
    expected_api: str,
    expected_slots: int | None,
    expected_arch: str,
    expected_member: str,
) -> None:
    """Issue #27: Resolve distinct deck geometry, API metadata, and catalog matches per target_platform."""
    out = autolab_wire.process_packet(
        {
            "target_platform": target_platform,
            "resource_url": "https://github.com/yaniguan/stepbot",
            "license_class": "MIT",
            "for_training": True,
        }
    )
    assert out["halted"] is False
    grounding = out["platform_grounding"]
    assert grounding["platform"] == target_platform
    assert grounding["api_level"] == expected_api
    assert grounding["max_deck_slots"] == expected_slots
    assert grounding["deck_architecture"] == expected_arch
    assert expected_member in grounding["matched_catalog_ids"]
    assert len(grounding["protocol_formats"]) >= 1
    assert grounding["has_simulator"] is True


def test_issue_27_unknown_platform_default_deny_and_modality_routing() -> None:
    """Issues #27 & #28: Block unknown platforms with L5_ATLAS_UNKNOWN_PLATFORM and route modalities."""
    bogus = autolab_wire.process_packet({"target_platform": "nonexistent_lunar_pipettor_v9"})
    assert bogus["halted"] is True
    assert bogus["halt_reason"] == "L5_ATLAS_UNKNOWN_PLATFORM"
    assert bogus["trace"][-1]["status"] == "BLOCK"
    assert bogus["platform_grounding"]["matched_catalog_ids"] == []
    assert bogus["platform_grounding"]["api_level"] is None
    assert bogus["platform_grounding"]["max_deck_slots"] is None

    routed = autolab_wire.process_packet(
        {
            "target_platform": "emerald_cloud_lab",
            "requested_modality": "Raman",
            "resource_url": "https://github.com/yaniguan/lab-attrib",
            "license_class": "MIT",
            "for_training": False,
        }
    )
    assert routed["halted"] is False
    capable = routed["platform_grounding"]["capable_modality_entries"]
    assert "emerald-cloud-lab" in capable
    assert "bluesky" in capable
    assert "lab-attrib" in capable


def test_issue_27_catalog_mtime_cache_avoids_redundant_disk_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Issue #27: Verify _build_indexed_atlas caches validated catalog across process_packet calls."""
    autolab_wire._INDEX_CACHE.clear()
    load_count = 0
    real_load = autolab_wire.load_catalog

    def _counting_load(*args, **kwargs):
        nonlocal load_count
        load_count += 1
        return real_load(*args, **kwargs)

    monkeypatch.setattr(autolab_wire, "load_catalog", _counting_load)

    autolab_wire.process_packet({"target_platform": "opentrons_ot2"})
    autolab_wire.process_packet({"target_platform": "opentrons_flex"})
    autolab_wire.process_packet({"target_platform": "hamilton_star"})
    assert load_count == 1


@pytest.mark.parametrize(
    ("expr", "commercial", "expected_halted"),
    [
        ("MIT AND CC-BY-NC-4.0", True, True),
        ("MIT AND CC-BY-NC-4.0", False, False),
        ("MIT OR CC-BY-NC-4.0", True, False),
        ("Apache-2.0 WITH LLVM-exception", True, False),
        ("MIT WITH Unknown-Restrictive-Exception", False, True),
        ("MIT AND BSD-3-Clause AND CC0-1.0", True, False),
        ("(MIT OR GPL-3.0-only) AND Apache-2.0", True, False),
        ("MIT AND AGPL-3.0-only", True, True),
        ("NOASSERTION", False, True),
        ("LicenseRef-Per-Article", False, True),
        ("LicenseRef-Proprietary", False, True),
        ("UnknownMadeUpLicense-1.0", False, True),
        ("MIT AND", False, True),
    ],
)
def test_issue_25_compound_spdx_and_default_deny_training_policy(
    expr: str, commercial: bool, expected_halted: bool
) -> None:
    """Issue #25: Evaluate compound SPDX expressions and default-deny unknown/custom terms in training."""
    res = autolab_wire.process_packet(
        {
            "resource_url": "https://github.com/chaitanya2334/WLP-Dataset",
            "license_class": expr,
            "for_training": True,
            "commercial": commercial,
        }
    )
    assert res["halted"] is expected_halted
    if expected_halted:
        assert res["halt_reason"] == "L5_ATLAS_LICENSE_OR_URL_BLOCK"
        assert res["platform_grounding"]["license_ok"] is False
    else:
        assert res["platform_grounding"]["license_ok"] is True


def test_issue_25_and_26_catalog_url_cross_match_and_lineage_taint_blocking() -> None:
    """Issues #25 & #26: Block catalog eval_only/rag_pointer_only URLs and tainted parent_licenses."""
    # LAB-Bench has spdx_license="CC-BY-SA-4.0" and allowed_purposes=["eval_only"]: must block even with commercial=False or MIT override!
    for url in (
        "https://github.com/Future-House/LAB-Bench",
        "https://huggingface.co/datasets/futurehouse/lab-bench",
        "https://huggingface.co/datasets/BioProBench/BioProBench",
        "https://github.com/bioplanner/bioplanner",
        "https://github.com/autobio-bench/AutoBio",
        "https://bio-protocol.org/en/bpdetail",
    ):
        res = autolab_wire.process_packet(
            {
                "resource_url": url,
                "license_class": "MIT",
                "for_training": True,
                "commercial": False,
            }
        )
        assert res["halted"] is True, f"Expected {url} to be blocked from training"
        assert res["halt_reason"] == "L5_ATLAS_LICENSE_OR_URL_BLOCK"

    # Derived corpus declaring MIT own license but carrying eval_only or custom_terms ancestor in parent_licenses
    derived_eval = autolab_wire.process_packet(
        {
            "resource_url": "https://github.com/yaniguan/twinstep",
            "license_class": "MIT",
            "parent_licenses": ["MIT", "LicenseRef-EvalOnly-Canary"],
            "for_training": True,
            "commercial": False,
        }
    )
    assert derived_eval["halted"] is True
    assert derived_eval["platform_grounding"]["effective_license_class"] == "eval_only"


@pytest.mark.parametrize(
    "obfuscated_ssrf_url",
    [
        "https://127.1/internal-config",
        "https://0177.0.0.1/internal-config",
        "https://0x7f000001/internal-config",
        "https://2130706433/internal-config",
        "https://localhost./mcp",
        "https://svc.internal/mcp",
        "https://[::ffff:0:127.0.0.1]/mcp",
        "https://[64:ff9b::127.0.0.1]/mcp",
        "https://user:secret@example.com/mcp",
    ],
)
def test_issue_24_wire_blocks_noncanonical_ssrf_urls_offline_and_with_dns_pinning(
    obfuscated_ssrf_url: str,
) -> None:
    """Issue #24: Block non-canonical IPv4/IPv6 SSRF vectors on the wire and support optional DNS pinning."""
    out = autolab_wire.process_packet(
        {
            "resource_url": obfuscated_ssrf_url,
            "license_class": "MIT",
            "for_training": False,
        }
    )
    assert out["halted"] is True
    assert out["halt_reason"] == "L5_ATLAS_LICENSE_OR_URL_BLOCK"

    pinned_ok = autolab_wire.process_packet(
        {
            "resource_url": "https://github.com/yaniguan/stepbot",
            "license_class": "MIT",
            "for_training": False,
            "resolve_dns": True,
        },
        resolver=lambda host, port, type=0: [(2, 1, 6, "", ("93.184.216.34", port))],
    )
    assert pinned_ok["halted"] is False
    assert pinned_ok["platform_grounding"]["pinned_ips"]["github.com:443"] == ["93.184.216.34"]
