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


@pytest.mark.parametrize(
    "bad_mcp_endpoint",
    [
        "https://localhost./mcp",
        "https://api.localhost/mcp",
        "https://svc.internal/mcp",
        "https://user:secret@example.com/mcp",
        "https://[::127.0.0.1]/mcp",
        "https://[64:ff9b::127.0.0.1]/mcp",
        "https://[::ffff:0:127.0.0.1]/mcp",
        "https://127.1/mcp",
        "https://0177.0.0.1/mcp",
        "https://0x7f000001/mcp",
    ],
)
def test_issue_24_mcp_endpoint_ssrf_parity_with_linkcheck(bad_mcp_endpoint: str) -> None:
    """Issue #24: Ensure MCP endpoint validator shares full SSRF canonicalization parity with linkcheck."""
    from community_extensions.mcp_capability_cards import _is_https_and_public_host

    assert _is_https_and_public_host(bad_mcp_endpoint) is False
    with pytest.raises(McpCardCompilationError, match="https_ssrf_guard"):
        compile_mcp_capability_card(_sample_spec(https_endpoint=bad_mcp_endpoint))


def test_issue_25_and_28_compound_spdx_and_from_atlas_entry_cards() -> None:
    """Issues #25 & #28: Compile cards from compound SPDX expressions and verified atlas.json entries."""
    from lab_atlas.catalog import load_catalog

    dual_card = compile_mcp_capability_card(_sample_spec(spdx_license="MIT OR Apache-2.0"))
    assert dual_card.license_class == "permissive"
    assert dual_card.commercial_train_ok is True

    conj_card = compile_mcp_capability_card(_sample_spec(spdx_license="MIT AND BSD-3-Clause"))
    assert conj_card.license_class == "permissive"
    assert conj_card.commercial_train_ok is True

    with_card = compile_mcp_capability_card(
        _sample_spec(spdx_license="Apache-2.0 WITH LLVM-exception")
    )
    assert with_card.license_class == "permissive"

    tainted_card = compile_mcp_capability_card(_sample_spec(spdx_license="MIT AND CC-BY-NC-4.0"))
    assert tainted_card.license_class == "non_commercial"
    assert tainted_card.commercial_train_ok is False

    catalog = load_catalog()
    by_id = {e["id"]: e for e in catalog["entries"]}

    ot_flex_spec = HardwareCapabilitySpec.from_atlas_entry(
        by_id["opentrons"],
        profile_id="opentrons_flex",
        https_endpoint="https://flex.autolab.example/mcp/v1/pipette",
    )
    ot_flex_card = compile_mcp_capability_card(ot_flex_spec)
    assert ot_flex_card.completeness_score == 1.0
    assert ot_flex_spec.min_volume_ul == 1.0
    assert ot_flex_spec.max_volume_ul == 1000.0

    # Cryogenic / sub-zero thermal envelope (-80.0 C to 200.0 C) from emerald-cloud-lab entry
    ecl_spec = HardwareCapabilitySpec.from_atlas_entry(
        by_id["emerald-cloud-lab"],
        https_endpoint="https://ecl-gateway.autolab.example/mcp/v1/run",
    )
    ecl_card = compile_mcp_capability_card(ecl_spec)
    assert ecl_spec.min_temp_c == -80.0
    cryo_call = {
        "deck_epoch": 5,
        "volume_ul": 10.0,
        "src_well_volume_ul": 50.0,
        "dst_well_volume_ul": 0.0,
        "dst_well_capacity_ul": 200.0,
        "temp_c": -20.0,
        "plate_sealed": False,
    }
    assert validate_with_typed_lean_mcp_card(
        ecl_card, cryo_call, live_deck_epoch=5, commercial_context=False
    ).allowed is True

    # Below -200.0 C cryogenic floor must be rejected at card compile time
    with pytest.raises(McpCardCompilationError, match="well_formed_physical_bounds"):
        compile_mcp_capability_card(_sample_spec(min_temp_c=-250.0))


def test_issue_26_exhaustive_lean_python_lattice_and_truth_table_parity() -> None:
    """Issue #26: Verify algebraic lattice laws and all 160 checkAtlasResource states match LabAtlasLean."""
    import itertools

    from lab_atlas.spdx import (
        LICENSE_CLASSES_ORDERED,
        check_atlas_resource_policy,
        effective_license_class,
        is_academic_train_ok,
        is_commercial_train_ok,
        license_conj,
        license_disj,
    )

    # 1. Verify all 25 pairs and 125 triples for bounded distributive lattice & homomorphism laws
    for a, b in itertools.product(LICENSE_CLASSES_ORDERED, repeat=2):
        assert license_conj(a, b) == license_conj(b, a)
        assert license_disj(a, b) == license_disj(b, a)
        assert license_conj(a, a) == a
        assert license_disj(a, a) == a
        assert license_conj("permissive", a) == a
        assert license_conj("eval_only", a) == "eval_only"
        assert license_conj(a, license_disj(a, b)) == a
        assert license_disj(a, license_conj(a, b)) == a
        assert is_commercial_train_ok(license_conj(a, b)) == (
            is_commercial_train_ok(a) and is_commercial_train_ok(b)
        )
        assert is_academic_train_ok(license_conj(a, b)) == (
            is_academic_train_ok(a) and is_academic_train_ok(b)
        )
        assert is_commercial_train_ok(license_disj(a, b)) == (
            is_commercial_train_ok(a) or is_commercial_train_ok(b)
        )
        assert is_academic_train_ok(license_disj(a, b)) == (
            is_academic_train_ok(a) or is_academic_train_ok(b)
        )

    for a, b, c in itertools.product(LICENSE_CLASSES_ORDERED, repeat=3):
        assert license_conj(license_conj(a, b), c) == license_conj(a, license_conj(b, c))
        assert license_disj(license_disj(a, b), c) == license_disj(a, license_disj(b, c))
        if "eval_only" in (a, b):
            assert effective_license_class([a, b], c) == "eval_only"

    # 2. Exhaustively check all 2 * 2 * 2 * 5 * 2 * 2 = 160 states against LabAtlasLean.checkAtlasResource
    states_checked = 0
    for https_only, no_priv_ip, spdx_known, lic_cls, for_training, commercial in itertools.product(
        (False, True),
        (False, True),
        (False, True),
        LICENSE_CLASSES_ORDERED,
        (False, True),
        (False, True),
    ):
        states_checked += 1
        py_rule = check_atlas_resource_policy(
            https_only=https_only,
            no_private_ip=no_priv_ip,
            spdx_known=spdx_known,
            license_class=lic_cls,
            for_training=for_training,
            commercial=commercial,
        )

        # Reference specification directly mirroring LabAtlasLean.checkAtlasResource rule order
        if not (https_only and no_priv_ip):
            lean_expected = "https_ssrf_guard"
        elif not spdx_known:
            lean_expected = "explicit_spdx_license"
        elif for_training and lic_cls == "eval_only":
            lean_expected = "eval_only_contamination_guard"
        elif for_training and lic_cls in ("custom_terms", "eval_only"):
            lean_expected = "academic_training_license_guard"
        elif for_training and commercial and lic_cls != "permissive":
            lean_expected = "commercial_training_license_guard"
        else:
            lean_expected = None

        assert py_rule == lean_expected

    assert states_checked == 160

    # Specifically confirm custom_terms is rejected in academic training on MCP runtime guard as well
    custom_card = compile_mcp_capability_card(
        _sample_spec(spdx_license="LicenseRef-VendorCustom")
    )
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
        custom_card,
        valid_args,
        live_deck_epoch=1,
        commercial_context=False,
        for_training=True,
    )
    assert dec.allowed is False
    assert dec.rule_violated == "academic_training_license_guard"


def test_lean_436_axiom_audit_and_100plus_eval_differential_parity() -> None:
    """Verify lean/README.md documents no custom axioms and run live lake env lean #eval parity if installed."""
    from scripts.verify_lean_parity import (
        ALLOWED_LEAN_AXIOMS,
        discover_lean_theorems,
        resolve_lake_binary,
        verify_lean_axioms_and_parity,
    )

    lean_readme = (REPO_ROOT / "lean" / "README.md").read_text(encoding="utf-8")
    assert "no custom axioms" in lean_readme.lower()

    theorems = discover_lean_theorems(REPO_ROOT / "lean" / "LabAtlasLean.lean")
    assert len(theorems) >= 48
    assert "LabAtlasLean.LicenseClass.conj_lub" in theorems
    assert "LabAtlasLean.dag_eval_ancestor_blocks_training" in theorems

    try:
        lake_bin = resolve_lake_binary()
    except FileNotFoundError:
        pytest.skip("Lean 4 `lake` binary not installed in this environment (verified in lean-proofs CI job)")

    summary = verify_lean_axioms_and_parity(lake_bin=lake_bin, run_build=False, min_cases=100)
    assert int(summary["theorems_verified"]) >= 48  # type: ignore[arg-type]
    assert int(summary["parity_cases_total"]) >= 300  # type: ignore[arg-type]
    assert set(summary["axioms_observed"]).issubset(ALLOWED_LEAN_AXIOMS)  # type: ignore[arg-type]
