"""Idea #09: Typed Lean-MCP Hardware Capability Card Compiler.

Inspired by di-omics/plr-mcp, K-Dense-AI/LabMCP, and Anthropic's Model Hardware Standard.
Compiles typed physical specifications (pipette [min, max] volume, dead-volume floor,
temperature limits, high-temperature evaporation seal coupling, mandatory deck_epoch,
HTTPS-only endpoint, and SPDX license posture) into closed JSON-Schema MCP tool
descriptors paired with executable precondition guards.
"""

from __future__ import annotations

import ipaddress
import urllib.parse
from dataclasses import dataclass
from typing import Any

SPDX_TO_LICENSE_CLASS: dict[str, str] = {
    "MIT": "permissive",
    "Apache-2.0": "permissive",
    "BSD-3-Clause": "permissive",
    "CC0-1.0": "permissive",
    "CC-BY-4.0": "permissive",
    "CC-BY-SA-4.0": "share_alike",
    "CC-BY-NC-4.0": "non_commercial",
    "LicenseRef-EvalOnly-Canary": "eval_only",
    "LicenseRef-VendorCustom": "custom_terms",
}


class McpCardCompilationError(ValueError):
    """Raised when a hardware specification or tool schema violates Lean-MCP card rules."""


@dataclass(frozen=True)
class HardwareCapabilitySpec:
    """Typed hardware specification for compiling a Lean-MCP capability card."""

    tool_name: str
    instrument_model: str
    https_endpoint: str
    spdx_license: str
    min_volume_ul: float
    max_volume_ul: float
    dead_volume_floor_ul: float
    min_temp_c: float
    max_temp_c: float
    high_temp_seal_threshold_c: float = 80.0
    required_deck_epoch: bool = True


@dataclass(frozen=True)
class CompiledMcpCapabilityCard:
    """Compiled MCP tool descriptor with JSON-Schema and fixed-point envelope metadata."""

    tool_name: str
    license_class: str
    commercial_train_ok: bool
    descriptor: dict[str, Any]
    completeness_score: float


@dataclass(frozen=True)
class McpCallDecision:
    """Result of evaluating a candidate MCP tool invocation."""

    allowed: bool
    rule_violated: str | None
    detail: str


def _is_https_and_public_host(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if host in {"localhost", "ip6-localhost"} or host.endswith(".local"):
        return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return True
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_unspecified
    )


def _to_tenth_ul(val_ul: float) -> int:
    return int(round(val_ul * 10.0))


def audit_mcp_tool_descriptor(descriptor: dict[str, Any]) -> tuple[float, list[str]]:
    """Score MCP tool descriptor completeness across 8 required Lean-MCP safety dimensions."""
    missing: list[str] = []
    schema = descriptor.get("inputSchema", {})
    props = schema.get("properties", {}) if isinstance(schema, dict) else {}
    required = set(schema.get("required", [])) if isinstance(schema, dict) else set()
    env = descriptor.get("x_lean_mcp_envelope", {})

    vol_prop = props.get("volume_ul", {})
    if not (
        isinstance(vol_prop, dict)
        and vol_prop.get("type") == "number"
        and "minimum" in vol_prop
        and "maximum" in vol_prop
    ):
        missing.append("typed_volume_min_max")

    temp_prop = props.get("temp_c", {})
    if not (
        isinstance(temp_prop, dict)
        and temp_prop.get("type") == "number"
        and "minimum" in temp_prop
        and "maximum" in temp_prop
    ):
        missing.append("typed_temperature_min_max")

    if schema.get("additionalProperties") is not False:
        missing.append("closed_additional_properties")

    epoch_prop = props.get("deck_epoch", {})
    if not (
        "deck_epoch" in required
        and isinstance(epoch_prop, dict)
        and epoch_prop.get("type") == "integer"
    ):
        missing.append("required_deck_epoch")

    if not (isinstance(env, dict) and "dead_volume_tenth_ul" in env):
        missing.append("dead_volume_floor_guard")

    if not (isinstance(env, dict) and "high_temp_seal_threshold_c" in env):
        missing.append("thermal_seal_coupling_guard")

    if not (
        isinstance(env, dict)
        and env.get("spdx_license") in SPDX_TO_LICENSE_CLASS
        and "license_class" in env
    ):
        missing.append("verified_spdx_license_posture")

    endpoint = env.get("https_endpoint", "") if isinstance(env, dict) else ""
    if not (isinstance(endpoint, str) and _is_https_and_public_host(endpoint)):
        missing.append("https_ssrf_endpoint_guard")

    passed = 8 - len(missing)
    return round(passed / 8.0, 4), missing


def compile_mcp_capability_card(spec: HardwareCapabilitySpec) -> CompiledMcpCapabilityCard:
    """Compile a typed HardwareCapabilitySpec into a closed Lean-MCP JSON-Schema card."""
    if not spec.tool_name or not spec.tool_name.strip():
        raise McpCardCompilationError("tool_name must be non-empty")
    if not _is_https_and_public_host(spec.https_endpoint):
        raise McpCardCompilationError(
            "https_ssrf_guard: endpoint must use HTTPS and not target private/loopback IPs"
        )
    if spec.spdx_license not in SPDX_TO_LICENSE_CLASS:
        raise McpCardCompilationError(
            f"explicit_spdx_license: unknown SPDX identifier {spec.spdx_license!r}"
        )
    if not spec.required_deck_epoch:
        raise McpCardCompilationError(
            "mandatory_deck_epoch_field: required_deck_epoch must be True"
        )

    min_v_10 = _to_tenth_ul(spec.min_volume_ul)
    max_v_10 = _to_tenth_ul(spec.max_volume_ul)
    dead_v_10 = _to_tenth_ul(spec.dead_volume_floor_ul)
    if min_v_10 <= 0 or min_v_10 > max_v_10 or dead_v_10 < 0:
        raise McpCardCompilationError(
            "well_formed_physical_bounds: invalid volume or dead-volume bounds"
        )
    if spec.min_temp_c > spec.max_temp_c or spec.high_temp_seal_threshold_c < spec.min_temp_c:
        raise McpCardCompilationError(
            "well_formed_physical_bounds: invalid thermal envelope bounds"
        )

    license_class = SPDX_TO_LICENSE_CLASS[spec.spdx_license]
    commercial_ok = license_class == "permissive"

    descriptor: dict[str, Any] = {
        "name": spec.tool_name,
        "description": (
            f"Typed Lean-MCP hardware capability card for {spec.instrument_model} "
            f"({spec.min_volume_ul}-{spec.max_volume_ul} uL, dead-volume >= "
            f"{spec.dead_volume_floor_ul} uL, {spec.min_temp_c}-{spec.max_temp_c} C)."
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "deck_epoch",
                "volume_ul",
                "src_well_volume_ul",
                "dst_well_volume_ul",
                "dst_well_capacity_ul",
                "temp_c",
                "plate_sealed",
            ],
            "properties": {
                "deck_epoch": {"type": "integer", "minimum": 0},
                "volume_ul": {
                    "type": "number",
                    "minimum": spec.min_volume_ul,
                    "maximum": spec.max_volume_ul,
                },
                "src_well_volume_ul": {"type": "number", "minimum": 0.0},
                "dst_well_volume_ul": {"type": "number", "minimum": 0.0},
                "dst_well_capacity_ul": {"type": "number", "exclusiveMinimum": 0.0},
                "temp_c": {
                    "type": "number",
                    "minimum": spec.min_temp_c,
                    "maximum": spec.max_temp_c,
                },
                "plate_sealed": {"type": "boolean"},
            },
        },
        "x_lean_mcp_envelope": {
            "instrument_model": spec.instrument_model,
            "https_endpoint": spec.https_endpoint,
            "spdx_license": spec.spdx_license,
            "license_class": license_class,
            "commercial_train_ok": commercial_ok,
            "min_vol_tenth_ul": min_v_10,
            "max_vol_tenth_ul": max_v_10,
            "dead_volume_tenth_ul": dead_v_10,
            "min_temp_c": spec.min_temp_c,
            "max_temp_c": spec.max_temp_c,
            "high_temp_seal_threshold_c": spec.high_temp_seal_threshold_c,
            "required_deck_epoch": True,
        },
    }

    completeness, missing = audit_mcp_tool_descriptor(descriptor)
    if missing:
        raise McpCardCompilationError(f"internal card audit failed: {missing}")

    return CompiledMcpCapabilityCard(
        tool_name=spec.tool_name,
        license_class=license_class,
        commercial_train_ok=commercial_ok,
        descriptor=descriptor,
        completeness_score=completeness,
    )


def build_prompt_only_schema(spec: HardwareCapabilitySpec) -> dict[str, Any]:
    """Construct a typical untyped prompt-only MCP tool descriptor for baseline comparison."""
    return {
        "name": spec.tool_name,
        "description": (
            f"Operate {spec.instrument_model}. Please keep volume_ul between "
            f"{spec.min_volume_ul} and {spec.max_volume_ul} uL, leave {spec.dead_volume_floor_ul} uL "
            f"dead volume, and seal plates at >= {spec.high_temp_seal_threshold_c} C."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": True,
            "required": ["volume_ul", "temp_c"],
            "properties": {
                "volume_ul": {"type": "number"},
                "temp_c": {"type": "number"},
            },
        },
    }


def _is_json_number(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def validate_with_prompt_only_schema(
    prompt_descriptor: dict[str, Any],
    call_args: dict[str, Any],
) -> McpCallDecision:
    """Validate an MCP call using only an untyped prompt-only JSON schema."""
    props = prompt_descriptor["inputSchema"]["properties"]
    required = prompt_descriptor["inputSchema"]["required"]
    for req_key in required:
        if req_key not in call_args:
            return McpCallDecision(False, "missing_required_field", f"missing {req_key}")
    for key, spec in props.items():
        if key in call_args and spec.get("type") == "number":
            if not _is_json_number(call_args[key]):
                return McpCallDecision(False, "json_type_mismatch", f"{key} must be a number")
    return McpCallDecision(True, None, "accepted_by_prompt_only_schema")


def validate_with_typed_lean_mcp_card(
    card: CompiledMcpCapabilityCard,
    call_args: dict[str, Any],
    *,
    live_deck_epoch: int,
    commercial_context: bool = True,
    for_training: bool = False,
) -> McpCallDecision:
    """Exact runtime precondition guard mirroring LabAtlasLean.checkMcpToolCall."""
    schema = card.descriptor["inputSchema"]
    props = schema["properties"]
    required = schema["required"]
    env = card.descriptor["x_lean_mcp_envelope"]

    unknown_keys = set(call_args.keys()) - set(props.keys())
    if unknown_keys:
        return McpCallDecision(
            False,
            "no_unknown_mcp_arguments",
            f"undeclared parameters rejected: {sorted(unknown_keys)}",
        )

    for req_key in required:
        if req_key not in call_args:
            return McpCallDecision(
                False, "missing_required_field", f"missing required field {req_key}"
            )

    epoch = call_args["deck_epoch"]
    if not (isinstance(epoch, int) and not isinstance(epoch, bool) and epoch >= 0):
        return McpCallDecision(False, "json_type_mismatch", "deck_epoch must be non-negative int")

    for num_key in (
        "volume_ul",
        "src_well_volume_ul",
        "dst_well_volume_ul",
        "dst_well_capacity_ul",
        "temp_c",
    ):
        if not _is_json_number(call_args[num_key]):
            return McpCallDecision(False, "json_type_mismatch", f"{num_key} must be numeric")

    if not isinstance(call_args["plate_sealed"], bool):
        return McpCallDecision(False, "json_type_mismatch", "plate_sealed must be boolean")

    if epoch != live_deck_epoch:
        return McpCallDecision(
            False,
            "fresh_deck_epoch",
            f"token deck_epoch={epoch} != live_deck_epoch={live_deck_epoch}",
        )

    vol_10 = _to_tenth_ul(float(call_args["volume_ul"]))
    src_10 = _to_tenth_ul(float(call_args["src_well_volume_ul"]))
    dst_10 = _to_tenth_ul(float(call_args["dst_well_volume_ul"]))
    cap_10 = _to_tenth_ul(float(call_args["dst_well_capacity_ul"]))
    temp_c = float(call_args["temp_c"])

    if not (env["min_vol_tenth_ul"] <= vol_10 <= env["max_vol_tenth_ul"]):
        return McpCallDecision(
            False,
            "volume_envelope_bounds",
            "volume_ul outside hardware pipette [min, max] bounds",
        )

    if env["dead_volume_tenth_ul"] + vol_10 > src_10 or dst_10 + vol_10 > cap_10:
        return McpCallDecision(
            False,
            "dead_volume_and_capacity_guard",
            "aspiration breaches dead-volume reserve or dispense overflows destination capacity",
        )

    if not (env["min_temp_c"] <= temp_c <= env["max_temp_c"]):
        return McpCallDecision(
            False, "thermal_and_evaporation_seal_guard", "temp_c outside thermal limits"
        )
    if temp_c >= env["high_temp_seal_threshold_c"] and not call_args["plate_sealed"]:
        return McpCallDecision(
            False,
            "thermal_and_evaporation_seal_guard",
            "high-temperature step requires plate_sealed=True",
        )

    if for_training and card.license_class == "eval_only":
        return McpCallDecision(
            False,
            "eval_only_contamination_guard",
            "eval_only resource blocked from training pipeline",
        )
    if commercial_context and not card.commercial_train_ok:
        return McpCallDecision(
            False,
            "driver_commercial_license_guard",
            f"license class {card.license_class} blocked in commercial autonomous execution",
        )

    return McpCallDecision(True, None, "verified_by_typed_lean_mcp_card")


def _generate_50_candidate_calls() -> list[tuple[dict[str, Any], bool, str, str]]:
    """Build 50 deterministic MCP calls (16 valid in-envelope + 34 unsafe out-of-envelope).

    Returns tuples of (call_args, is_safe, spdx_override, category).
    """
    candidates: list[tuple[dict[str, Any], bool, str, str]] = []

    # 16 valid in-envelope calls (including sealed 95 C PCR & exact safe margins)
    for i in range(16):
        high_temp = i % 4 == 0
        vol = 10.0 + i * 15.0
        candidates.append(
            (
                {
                    "deck_epoch": 12,
                    "volume_ul": vol,
                    "src_well_volume_ul": vol + 35.0,
                    "dst_well_volume_ul": 20.0,
                    "dst_well_capacity_ul": 350.0,
                    "temp_c": 92.0 if high_temp else 37.0,
                    "plate_sealed": True if high_temp else False,
                },
                True,
                "MIT",
                "valid_in_envelope",
            )
        )

    # 6 sub-minimum or negative volume calls (e.g. 0.2 uL on a 1.0 uL channel, or -5.0 uL)
    for v in (-10.0, -0.5, 0.0, 0.1, 0.4, 0.8):
        candidates.append(
            (
                {
                    "deck_epoch": 12,
                    "volume_ul": v,
                    "src_well_volume_ul": 100.0,
                    "dst_well_volume_ul": 10.0,
                    "dst_well_capacity_ul": 300.0,
                    "temp_c": 25.0,
                    "plate_sealed": False,
                },
                False,
                "MIT",
                "volume_under_min",
            )
        )

    # 5 barrel overflow calls (> 1000.0 uL max)
    for v in (1005.0, 1100.0, 1250.0, 1500.0, 2000.0):
        candidates.append(
            (
                {
                    "deck_epoch": 12,
                    "volume_ul": v,
                    "src_well_volume_ul": 2500.0,
                    "dst_well_volume_ul": 0.0,
                    "dst_well_capacity_ul": 3000.0,
                    "temp_c": 25.0,
                    "plate_sealed": False,
                },
                False,
                "MIT",
                "volume_over_max",
            )
        )

    # 6 dead-volume aspiration underflows or destination well overfills
    for i in range(6):
        if i < 4:
            # Aspirating 80 uL from 90 uL well when dead_volume_floor is 15 uL (needs >= 95 uL)
            call = {
                "deck_epoch": 12,
                "volume_ul": 80.0,
                "src_well_volume_ul": 82.0 + i * 2.0,
                "dst_well_volume_ul": 10.0,
                "dst_well_capacity_ul": 300.0,
                "temp_c": 25.0,
                "plate_sealed": False,
            }
        else:
            # Dispensing 150 uL into 220/300 uL well (overflows 300 uL cap)
            call = {
                "deck_epoch": 12,
                "volume_ul": 150.0,
                "src_well_volume_ul": 250.0,
                "dst_well_volume_ul": 180.0 + i * 10.0,
                "dst_well_capacity_ul": 300.0,
                "temp_c": 25.0,
                "plate_sealed": False,
            }
        candidates.append((call, False, "MIT", "dead_volume_or_overfill"))

    # 5 unsealed high-temperature (>= 80 C) calls or out-of-range temperatures
    for temp in (80.0, 85.0, 95.0, 98.0, 120.0):
        candidates.append(
            (
                {
                    "deck_epoch": 12,
                    "volume_ul": 50.0,
                    "src_well_volume_ul": 120.0,
                    "dst_well_volume_ul": 20.0,
                    "dst_well_capacity_ul": 300.0,
                    "temp_c": temp,
                    "plate_sealed": False,
                },
                False,
                "MIT",
                "thermal_or_unsealed_evaporation",
            )
        )

    # 5 stale deck_epoch replay calls
    for stale_ep in (0, 8, 10, 11, 13):
        candidates.append(
            (
                {
                    "deck_epoch": stale_ep,
                    "volume_ul": 50.0,
                    "src_well_volume_ul": 120.0,
                    "dst_well_volume_ul": 20.0,
                    "dst_well_capacity_ul": 300.0,
                    "temp_c": 37.0,
                    "plate_sealed": False,
                },
                False,
                "MIT",
                "stale_deck_epoch_replay",
            )
        )

    # 3 hallucinated extra-argument calls (e.g. "force_override": True)
    for extra_key in ("bypass_aspirate_check", "force_ gantry_speed_pct", "ignore_seal"):
        candidates.append(
            (
                {
                    "deck_epoch": 12,
                    "volume_ul": 50.0,
                    "src_well_volume_ul": 120.0,
                    "dst_well_volume_ul": 20.0,
                    "dst_well_capacity_ul": 300.0,
                    "temp_c": 37.0,
                    "plate_sealed": False,
                    extra_key.replace(" ", ""): True,
                },
                False,
                "MIT",
                "hallucinated_extra_arg",
            )
        )

    # 2 license-restricted / eval-only calls in commercial autonomous mode
    for bad_spdx in ("LicenseRef-EvalOnly-Canary", "CC-BY-NC-4.0"):
        candidates.append(
            (
                {
                    "deck_epoch": 12,
                    "volume_ul": 50.0,
                    "src_well_volume_ul": 120.0,
                    "dst_well_volume_ul": 20.0,
                    "dst_well_capacity_ul": 300.0,
                    "temp_c": 37.0,
                    "plate_sealed": False,
                },
                False,
                bad_spdx,
                "license_or_eval_contamination",
            )
        )

    # 2 raw JSON type confusion calls (caught by both schemas)
    for bad_val in ("50uL", None):
        candidates.append(
            (
                {
                    "deck_epoch": 12,
                    "volume_ul": bad_val,
                    "src_well_volume_ul": 120.0,
                    "dst_well_volume_ul": 20.0,
                    "dst_well_capacity_ul": 300.0,
                    "temp_c": 37.0,
                    "plate_sealed": False,
                },
                False,
                "MIT",
                "json_type_confusion",
            )
        )

    assert len(candidates) == 50
    return candidates


def run_benchmark(num_calls: int = 50, seed: int = 2026) -> dict[str, Any]:
    """Compare prompt_only_schema vs typed_lean_mcp_card over 50 candidate MCP calls."""
    _ = seed  # Deterministic canonical 50-call suite; seed retained for uniform API
    base_spec = HardwareCapabilitySpec(
        tool_name="hamilton_star_transfer_and_incubate",
        instrument_model="Hamilton Microlab STAR 1000uL Core",
        https_endpoint="https://workcell-gateway.autolab.example/mcp/v1/star",
        spdx_license="MIT",
        min_volume_ul=1.0,
        max_volume_ul=1000.0,
        dead_volume_floor_ul=15.0,
        min_temp_c=4.0,
        max_temp_c=98.0,
        high_temp_seal_threshold_c=80.0,
        required_deck_epoch=True,
    )
    prompt_schema = build_prompt_only_schema(base_spec)
    prompt_completeness, prompt_missing = audit_mcp_tool_descriptor(prompt_schema)
    base_card = compile_mcp_capability_card(base_spec)

    all_candidates = _generate_50_candidate_calls()[:num_calls]
    valid_total = sum(1 for _, is_safe, _, _ in all_candidates if is_safe)
    unsafe_total = sum(1 for _, is_safe, _, _ in all_candidates if not is_safe)

    prompt_intercepted = 0
    prompt_false_blocks = 0
    typed_intercepted = 0
    typed_false_blocks = 0

    for call_args, is_safe, spdx_code, _ in all_candidates:
        p_dec = validate_with_prompt_only_schema(prompt_schema, call_args)
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
        t_dec = validate_with_typed_lean_mcp_card(
            card,
            call_args,
            live_deck_epoch=12,
            commercial_context=True,
            for_training=(spdx_code == "LicenseRef-EvalOnly-Canary"),
        )

        if is_safe:
            if not p_dec.allowed:
                prompt_false_blocks += 1
            if not t_dec.allowed:
                typed_false_blocks += 1
        else:
            if not p_dec.allowed:
                prompt_intercepted += 1
            if not t_dec.allowed:
                typed_intercepted += 1

    return {
        "benchmark": "idea_09_mcp_capability_cards",
        "num_candidate_calls": len(all_candidates),
        "in_envelope_valid_calls": valid_total,
        "out_of_envelope_unsafe_calls": unsafe_total,
        "prompt_only_schema": {
            "schema_completeness_score": prompt_completeness,
            "missing_safety_dimensions": len(prompt_missing),
            "out_of_envelope_intercepted": prompt_intercepted,
            "out_of_envelope_intercept_rate": round(prompt_intercepted / unsafe_total, 4),
            "unsafe_slips_to_hardware": unsafe_total - prompt_intercepted,
            "false_positive_blocks": prompt_false_blocks,
        },
        "typed_lean_mcp_card": {
            "schema_completeness_score": base_card.completeness_score,
            "missing_safety_dimensions": 0,
            "out_of_envelope_intercepted": typed_intercepted,
            "out_of_envelope_intercept_rate": round(typed_intercepted / unsafe_total, 4),
            "unsafe_slips_to_hardware": unsafe_total - typed_intercepted,
            "false_positive_blocks": typed_false_blocks,
        },
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_benchmark(), indent=2))
