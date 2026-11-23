"""Tests for lab-automation-atlas community extensions (Idea #09) and LabAtlasLean parity."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from community_extensions.mcp_capability_cards import (  # noqa: E402
    HardwareCapabilitySpec,
    McpCardCompilationError,
    audit_mcp_tool_descriptor,
    build_prompt_only_schema,
    compile_mcp_capability_card,
    run_benchmark,
    validate_with_prompt_only_schema,
    validate_with_typed_lean_mcp_card,
)

CJK_RE = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]")


def _sample_spec(**overrides: object) -> HardwareCapabilitySpec:
    defaults: dict[str, object] = {
        "tool_name": "opentrons_flex_pipette",
        "instrument_model": "Opentrons Flex P1000",
        "https_endpoint": "https://flex.autolab.example/mcp/pipette",
        "spdx_license": "Apache-2.0",
        "min_volume_ul": 5.0,
        "max_volume_ul": 1000.0,
        "dead_volume_floor_ul": 10.0,
        "min_temp_c": 4.0,
        "max_temp_c": 98.0,
        "high_temp_seal_threshold_c": 80.0,
        "required_deck_epoch": True,
    }
    defaults.update(overrides)
    return HardwareCapabilitySpec(**defaults)  # type: ignore[arg-type]


def test_compiler_rejects_epochless_non_https_private_ip_and_unknown_spdx() -> None:
    with pytest.raises(McpCardCompilationError, match="mandatory_deck_epoch_field"):
        compile_mcp_capability_card(_sample_spec(required_deck_epoch=False))

    with pytest.raises(McpCardCompilationError, match="https_ssrf_guard"):
        compile_mcp_capability_card(_sample_spec(https_endpoint="http://flex.autolab.example/mcp"))

    with pytest.raises(McpCardCompilationError, match="https_ssrf_guard"):
        compile_mcp_capability_card(_sample_spec(https_endpoint="https://127.0.0.1:8443/mcp"))

    with pytest.raises(McpCardCompilationError, match="https_ssrf_guard"):
        compile_mcp_capability_card(_sample_spec(https_endpoint="https://192.168.1.50/mcp"))

    with pytest.raises(McpCardCompilationError, match="explicit_spdx_license"):
        compile_mcp_capability_card(_sample_spec(spdx_license="UNLICENSED-FOO"))

    with pytest.raises(McpCardCompilationError, match="well_formed_physical_bounds"):
        compile_mcp_capability_card(_sample_spec(min_volume_ul=500.0, max_volume_ul=50.0))


def test_audit_distinguishes_prompt_only_schema_from_typed_lean_mcp_card() -> None:
    spec = _sample_spec()
    prompt_desc = build_prompt_only_schema(spec)
    score_prompt, missing_prompt = audit_mcp_tool_descriptor(prompt_desc)
    assert score_prompt == 0.0
    assert len(missing_prompt) == 8

    card = compile_mcp_capability_card(spec)
    score_typed, missing_typed = audit_mcp_tool_descriptor(card.descriptor)
    assert score_typed == 1.0
    assert missing_typed == []


def test_runtime_guards_catch_stale_epoch_dead_volume_and_unsealed_pcr() -> None:
    card = compile_mcp_capability_card(_sample_spec())
    prompt_desc = build_prompt_only_schema(_sample_spec())

    # Dead-volume underflow: 95 uL aspirate from 100 uL well with 10 uL dead-volume floor
    underflow_call = {
        "deck_epoch": 4,
        "volume_ul": 95.0,
        "src_well_volume_ul": 100.0,
        "dst_well_volume_ul": 0.0,
        "dst_well_capacity_ul": 200.0,
        "temp_c": 25.0,
        "plate_sealed": False,
    }
    assert validate_with_prompt_only_schema(prompt_desc, underflow_call).allowed is True
    res_underflow = validate_with_typed_lean_mcp_card(card, underflow_call, live_deck_epoch=4)
    assert res_underflow.allowed is False
    assert res_underflow.rule_violated == "dead_volume_and_capacity_guard"

    # Unsealed 94 C denaturation
    unsealed_pcr = dict(underflow_call, volume_ul=50.0, temp_c=94.0, plate_sealed=False)
    res_pcr = validate_with_typed_lean_mcp_card(card, unsealed_pcr, live_deck_epoch=4)
    assert res_pcr.allowed is False
    assert res_pcr.rule_violated == "thermal_and_evaporation_seal_guard"

    # Stale epoch replay
    stale_call = dict(underflow_call, volume_ul=50.0, deck_epoch=3)
    res_stale = validate_with_typed_lean_mcp_card(card, stale_call, live_deck_epoch=4)
    assert res_stale.allowed is False
    assert res_stale.rule_violated == "fresh_deck_epoch"


def test_eval_only_and_non_commercial_blocked_in_training_and_commercial_modes() -> None:
    eval_card = compile_mcp_capability_card(_sample_spec(spdx_license="LicenseRef-EvalOnly-Canary"))
    valid_args = {
        "deck_epoch": 1,
        "volume_ul": 20.0,
        "src_well_volume_ul": 100.0,
        "dst_well_volume_ul": 10.0,
        "dst_well_capacity_ul": 200.0,
        "temp_c": 25.0,
        "plate_sealed": False,
    }
    dec = validate_with_typed_lean_mcp_card(
        eval_card,
        valid_args,
        live_deck_epoch=1,
        commercial_context=False,
        for_training=True,
    )
    assert dec.allowed is False
    assert dec.rule_violated == "eval_only_contamination_guard"


def test_idea_09_benchmark_50_calls_metrics() -> None:
    report = run_benchmark(num_calls=50, seed=2026)
    assert report["num_candidate_calls"] == 50
    assert report["in_envelope_valid_calls"] == 16
    assert report["out_of_envelope_unsafe_calls"] == 34

    p = report["prompt_only_schema"]
    t = report["typed_lean_mcp_card"]
    assert p["schema_completeness_score"] == 0.0
    assert p["out_of_envelope_intercepted"] == 2
    assert p["unsafe_slips_to_hardware"] == 32

    assert t["schema_completeness_score"] == 1.0
    assert t["out_of_envelope_intercepted"] == 34
    assert t["out_of_envelope_intercept_rate"] == 1.0
    assert t["unsafe_slips_to_hardware"] == 0
    assert t["false_positive_blocks"] == 0


def test_pure_english_and_lean_file_integrity() -> None:
    lean_file = REPO_ROOT / "lean" / "LabAtlasLean.lean"
    assert lean_file.exists()
    lean_src = lean_file.read_text(encoding="utf-8")
    assert "sorry" not in re.findall(r"\bsorry\b", lean_src)
    assert "axiom" not in re.findall(r"\baxiom\b", lean_src)

    checked_paths = [
        lean_file,
        REPO_ROOT / "lean" / "README.md",
        REPO_ROOT / "lean" / "lakefile.toml",
        REPO_ROOT / "community_extensions" / "__init__.py",
        REPO_ROOT / "community_extensions" / "mcp_capability_cards.py",
        Path(__file__).resolve(),
    ]
    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        assert CJK_RE.search(text) is None, f"CJK character found in {path}"
