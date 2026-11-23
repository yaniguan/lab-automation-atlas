# LabAtlasLean (Lean 4.36.0 Registry & Typed Lean-MCP Guards)

`LabAtlasLean` provides machine-checked L5 ecosystem governance and typed hardware-MCP capability invariants for `lab-automation-atlas` in Lean 4 (`v4.36.0`), with zero `sorry` and zero custom `axiom` declarations.

## Covered Invariants and Theorems

1. **Registry Security, SPDX Governance & Contamination Firewall ([LabAtlasLean.lean](LabAtlasLean.lean))**
   - `LicenseClass`, `AtlasResource`, `AtlasResourceOK`, and executable checker `checkAtlasResource`.
   - `checkAtlasResource_ok_iff`: soundness and completeness equivalence.
   - `eval_only_blocked_from_training`: blocks `evalOnly` benchmarks from entering training pipelines.
   - `http_or_private_ip_rejected`: enforces HTTPS-only and blocks private/loopback IP SSRF targets.
   - `non_permissive_blocked_from_commercial_training`: enforces permissive SPDX compliance in commercial training.
2. **Typed `Lean-MCP` Hardware Capability Cards (Idea #09)**
   - `McpCapabilityCard`, `McpToolCall`, `checkMcpCardSpec`, `checkMcpToolCall`.
   - `untyped_or_epochless_card_rejected`: rejects prompt-only schemas and epochless hardware wrappers.
   - `out_of_envelope_mcp_call_intercepted`: blocks stale `deck_epoch` replays, dead-volume underflows, and unsealed high-temperature operations.

## Build and Verify

See [lakefile.toml](lakefile.toml) and [lean-toolchain](lean-toolchain):

```bash
cd lean
lake build
```
