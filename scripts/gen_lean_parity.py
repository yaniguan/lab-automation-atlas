"""Generate Lean 4.36.0 compile-time `#guard` parity witnesses from Python policy & MCP card code.

Enumerates:
1. All 160 `AtlasResource` boolean/license states (`2^5 * 5 = 160` `#guard`s) from
   `lab_atlas.spdx.check_atlas_resource_policy`.
2. All 25 `LicenseClass.conj` pairs (`25` `#guard`s) from `lab_atlas.spdx.license_conj`.
3. All 25 `LicenseClass.disj` pairs (`25` `#guard`s) from `lab_atlas.spdx.license_disj`.
4. All 50 candidate MCP capability-card tool calls (`50` `#guard`s) from
   `community_extensions.mcp_capability_cards` converted into tenths of a microliter and
   signed tenths of degrees Celsius.

Total: `260` `#guard` lines written to `lean/LabAtlasLean/Parity.lean` and compiled by `lake build`.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from community_extensions.mcp_capability_cards import (  # noqa: E402
    HardwareCapabilitySpec,
    _generate_50_candidate_calls,
    _is_json_number,
    _to_tenth_c,
    _to_tenth_ul,
    compile_mcp_capability_card,
    validate_with_typed_lean_mcp_card,
)
from lab_atlas.catalog import load_catalog  # noqa: E402
from lab_atlas.spdx import (  # noqa: E402
    LICENSE_CLASSES_ORDERED,
    check_atlas_resource_policy,
    license_conj,
    license_disj,
)

PARITY_LEAN_PATH = ROOT / "lean" / "LabAtlasLean" / "Parity.lean"

_PY_TO_LEAN_LIC: dict[str, str] = {
    "permissive": ".permissive",
    "share_alike": ".shareAlike",
    "non_commercial": ".nonCommercial",
    "custom_terms": ".customTerms",
    "eval_only": ".evalOnly",
}


def _lean_bool(val: bool) -> str:
    return "true" if val else "false"


def _lean_int(val: int) -> str:
    return f"({val})" if val < 0 else str(val)


def _lean_opt_str(val: str | None) -> str:
    if val is None:
        return "none"
    escaped = val.replace("\\", "\\\\").replace('"', '\\"')
    return f'some "{escaped}"'


def render_lean_parity_guards() -> str:
    """Render deterministic `lean/LabAtlasLean/Parity.lean` with 260 `#guard` assertions."""
    lines: list[str] = [
        "import LabAtlasLean",
        "",
        "/-!",
        "# LabAtlasLean.Parity: Auto-Generated 260-Case Python-to-Lean `#guard` Suite",
        "",
        "Generated deterministically by `python scripts/gen_lean_parity.py`. Do not edit by hand.",
        "Covers boolean resource policy (`160` states), bounded license lattice (`25` `conj` + `25` `disj`),",
        "and typed MCP capability-card call preconditions (`50` calls) — `260` `#guard` assertions total.",
        "-/",
        "",
        "namespace LabAtlasLean.Parity",
        "",
        "open LabAtlasLean",
        "",
        "/-! ## 1. `checkAtlasResource` Boolean Policy Exhaustive Truth Table (160 `#guard`s) -/",
        "",
    ]

    # 1. 160 AtlasResource states
    for h, np, sk, lc, ft, cm in itertools.product(
        (False, True),
        (False, True),
        (False, True),
        LICENSE_CLASSES_ORDERED,
        (False, True),
        (False, True),
    ):
        py_rule = check_atlas_resource_policy(
            https_only=h,
            no_private_ip=np,
            spdx_known=sk,
            license_class=lc,
            for_training=ft,
            commercial=cm,
        )
        rec = (
            f"{{ httpsOnly := {_lean_bool(h)}, noPrivateIp := {_lean_bool(np)}, "
            f"spdxKnown := {_lean_bool(sk)}, licenseClass := {_PY_TO_LEAN_LIC[lc]}, "
            f"forTraining := {_lean_bool(ft)}, commercial := {_lean_bool(cm)} }}"
        )
        lines.append(
            f"#guard ((checkAtlasResource {rec}).map (·.rule)) == {_lean_opt_str(py_rule)}"
        )

    lines.extend(
        [
            "",
            "/-! ## 2. `LicenseClass.conj` Join Truth Table (25 `#guard`s) -/",
            "",
        ]
    )
    for a, b in itertools.product(LICENSE_CLASSES_ORDERED, repeat=2):
        py_cj = license_conj(a, b)
        lines.append(
            f"#guard (LicenseClass.conj {_PY_TO_LEAN_LIC[a]} {_PY_TO_LEAN_LIC[b]}) == {_PY_TO_LEAN_LIC[py_cj]}"
        )

    lines.extend(
        [
            "",
            "/-! ## 3. `LicenseClass.disj` Meet Truth Table (25 `#guard`s) -/",
            "",
        ]
    )
    for a, b in itertools.product(LICENSE_CLASSES_ORDERED, repeat=2):
        py_dj = license_disj(a, b)
        lines.append(
            f"#guard (LicenseClass.disj {_PY_TO_LEAN_LIC[a]} {_PY_TO_LEAN_LIC[b]}) == {_PY_TO_LEAN_LIC[py_dj]}"
        )

    # 4. 50 MCP benchmark calls
    catalog = load_catalog(ROOT / "atlas.json", validate=False)
    hamilton_entry = next(e for e in catalog["entries"] if e["id"] == "hamilton")
    base_spec = HardwareCapabilitySpec.from_atlas_entry(
        hamilton_entry,
        profile_id="hamilton_star",
        tool_name="hamilton_star_transfer_and_incubate",
        https_endpoint="https://workcell-gateway.autolab.example/mcp/v1/star",
        spdx_license="MIT",
    )
    base_card = compile_mcp_capability_card(base_spec)
    env = base_card.descriptor["x_lean_mcp_envelope"]
    declared_keys = set(base_card.descriptor["inputSchema"]["properties"].keys())
    required_keys = list(base_card.descriptor["inputSchema"]["required"])

    lines.extend(
        [
            "",
            "/-! ## 4. `checkMcpToolCall` 50-Call Benchmark Parity Suite (50 `#guard`s) -/",
            "",
            "private def benchCard (lc : LicenseClass) : McpCapabilityCard :=",
            "  { hasTypedNumericBounds := true, forbidsExtraProps := true, requiresDeckEpoch := true,",
            "    spdxKnown := true, licenseClass := lc,",
            f"    minVolTenthUL := {env['min_vol_tenth_ul']}, maxVolTenthUL := {env['max_vol_tenth_ul']}, "
            f"deadVolTenthUL := {env['dead_volume_tenth_ul']},",
            f"    minTempC := {_lean_int(env['min_temp_tenth_c'])}, "
            f"maxTempC := {_lean_int(env['max_temp_tenth_c'])}, "
            f"sealTempThreshC := {_lean_int(env['high_temp_seal_threshold_tenth_c'])} }}",
            "",
        ]
    )

    candidates = _generate_50_candidate_calls()
    live_epoch = 12
    for call_args, _is_safe, spdx_code, _cat in candidates:
        card = (
            base_card
            if spdx_code == "MIT"
            else compile_mcp_capability_card(
                HardwareCapabilitySpec(
                    tool_name=base_spec.tool_name,
                    instrument_model=base_spec.instrument_model,
                    https_endpoint=base_spec.https_endpoint,
                    spdx_license=spdx_code,
                    min_volume_ul=base_spec.min_volume_ul,
                    max_volume_ul=base_spec.max_volume_ul,
                    dead_volume_floor_ul=base_spec.dead_volume_floor_ul,
                    min_temp_c=base_spec.min_temp_c,
                    max_temp_c=base_spec.max_temp_c,
                    high_temp_seal_threshold_c=base_spec.high_temp_seal_threshold_c,
                    required_deck_epoch=True,
                )
            )
        )
        for_training = spdx_code == "LicenseRef-EvalOnly-Canary"
        py_dec = validate_with_typed_lean_mcp_card(
            card,
            call_args,
            live_deck_epoch=live_epoch,
            commercial_context=True,
            for_training=for_training,
        )

        has_unknown = bool(set(call_args.keys()) - declared_keys)
        has_all_req = all(k in call_args for k in required_keys)
        epoch_raw: Any = call_args.get("deck_epoch")
        epoch_ok = isinstance(epoch_raw, int) and not isinstance(epoch_raw, bool) and epoch_raw >= 0
        nums_ok = all(
            _is_json_number(call_args.get(k))
            for k in (
                "volume_ul",
                "src_well_volume_ul",
                "dst_well_volume_ul",
                "dst_well_capacity_ul",
                "temp_c",
            )
        )
        sealed_raw = call_args.get("plate_sealed")
        bool_ok = isinstance(sealed_raw, bool)
        valid_json_types = has_all_req and epoch_ok and nums_ok and bool_ok

        tok_ep = int(epoch_raw) if epoch_ok else 0
        vol_10 = _to_tenth_ul(float(call_args["volume_ul"])) if _is_json_number(call_args.get("volume_ul")) else 0
        src_10 = (
            _to_tenth_ul(float(call_args["src_well_volume_ul"]))
            if _is_json_number(call_args.get("src_well_volume_ul"))
            else 0
        )
        dst_10 = (
            _to_tenth_ul(float(call_args["dst_well_volume_ul"]))
            if _is_json_number(call_args.get("dst_well_volume_ul"))
            else 0
        )
        cap_10 = (
            _to_tenth_ul(float(call_args["dst_well_capacity_ul"]))
            if _is_json_number(call_args.get("dst_well_capacity_ul"))
            else 0
        )
        temp_10 = _to_tenth_c(float(call_args["temp_c"])) if _is_json_number(call_args.get("temp_c")) else 0
        plate_sealed = bool(sealed_raw) if bool_ok else False

        call_rec = (
            f"{{ tokenEpoch := {tok_ep}, liveDeckEpoch := {live_epoch}, "
            f"volTenthUL := {_lean_int(vol_10)}, srcWellVolTenthUL := {_lean_int(src_10)}, "
            f"dstWellVolTenthUL := {_lean_int(dst_10)}, dstWellCapTenthUL := {_lean_int(cap_10)}, "
            f"tempC := {_lean_int(temp_10)}, plateSealed := {_lean_bool(plate_sealed)}, "
            f"hasUnknownExtraArgs := {_lean_bool(has_unknown)}, commercialContext := true, "
            f"validJsonTypes := {_lean_bool(valid_json_types)}, forTraining := {_lean_bool(for_training)} }}"
        )
        lean_lc = _PY_TO_LEAN_LIC[card.license_class]
        lines.append(
            f"#guard ((checkMcpToolCall (benchCard {lean_lc}) {call_rec}).map (·.rule)) == {_lean_opt_str(py_dec.rule_violated)}"
        )

    lines.extend(["", "end LabAtlasLean.Parity", ""])
    rendered = "\n".join(lines)
    guard_count = sum(1 for ln in lines if ln.startswith("#guard "))
    if guard_count != 260:
        raise AssertionError(f"Expected 260 #guard lines, generated {guard_count}")
    return rendered


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate or verify lean/LabAtlasLean/Parity.lean (260 #guard parity suite)."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify lean/LabAtlasLean/Parity.lean matches Python policy & MCP card code byte-for-byte.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PARITY_LEAN_PATH,
        help="Output path for generated Lean parity module.",
    )
    args = parser.parse_args(argv)

    expected = render_lean_parity_guards()
    out_path = args.output.resolve()

    if args.check:
        if not out_path.is_file():
            print(f"DRIFT: missing {out_path}", file=sys.stderr)
            return 1
        current = out_path.read_text(encoding="utf-8")
        if current != expected:
            print(
                f"DRIFT: {out_path} differs from Python policy/MCP generator. "
                "Run `python scripts/gen_lean_parity.py`.",
                file=sys.stderr,
            )
            return 1
        print(f"OK: {out_path} matches Python policy & MCP card generator (260 #guard lines).")
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(expected, encoding="utf-8")
    print(f"Wrote 260 #guard parity assertions to {out_path}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
