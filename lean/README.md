# LabAtlasLean (Lean 4.36.0 License Lattice, Lineage Taint & Typed Lean-MCP Guards)

`LabAtlasLean` provides machine-checked L5 ecosystem governance, SPDX join-semilattice / lineage-contamination propagation, and typed hardware-MCP capability invariants for `lab-automation-atlas` in Lean 4 (`v4.36.0`), with zero `sorry` and zero custom `axiom` declarations.

## Covered Invariants and Theorems

1. **Bounded Distributive License Lattice ([LabAtlasLean.lean](LabAtlasLean.lean))**
   - `LicenseClass` ordered chain: `permissive (0) < shareAlike (1) < nonCommercial (2) < customTerms (3) < evalOnly (4)`.
   - `LicenseClass.conj` (`AND` / corpus derivation join) and `LicenseClass.disj` (`OR` / dual-license meet) with machine-checked commutativity, associativity, idempotence, absorption, `.permissive` bottom identity, `.evalOnly` absorptive top taint, `conj_lub` join-semilattice universal property, and monotonicity/homomorphism theorems for `commercialTrainOK` and `academicTrainOK`.
2. **Transitive Dataset-Derivation Lineage & Taint Propagation**
   - `effectiveLicense` over upstream parent lists and `LineageDAG` over arbitrary-depth derivation graphs.
   - `eval_ancestor_blocks_derived_training`, `untrainable_ancestor_blocks_derived_training`, and `dag_eval_ancestor_blocks_training`: any `.evalOnly` or `.customTerms` ancestor blocks downstream training regardless of declared child license.
3. **Registry Security, SPDX Governance & Contamination Firewall**
   - `AtlasResource`, `AtlasResourceOK`, `checkAtlasResource`, and `checkAtlasResource_ok_iff`.
   - `eval_only_blocked_from_training`, `custom_terms_blocked_from_all_training`, `http_or_private_ip_rejected`, and `non_permissive_blocked_from_commercial_training`.
4. **Typed `Lean-MCP` Hardware Capability Cards & Cryogenic Thermal Envelopes (Idea #09)**
   - `McpCapabilityCard` and `McpToolCall` using tenths of a microliter (`0.1 uL`) and signed tenths of degrees Celsius (`TenthC := Int` down to `-200.0 C`).
   - `untyped_or_epochless_card_rejected` and `out_of_envelope_mcp_call_intercepted`.

## Build and Verify

See [lakefile.toml](lakefile.toml) and [lean-toolchain](lean-toolchain):

```bash
cd lean
lake build
```
