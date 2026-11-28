import LabAtlasLean

/-!
# LabAtlasLean.Parity: Auto-Generated 260-Case Python-to-Lean `#guard` Suite

Generated deterministically by `python scripts/gen_lean_parity.py`. Do not edit by hand.
Covers boolean resource policy (`160` states), bounded license lattice (`25` `conj` + `25` `disj`),
and typed MCP capability-card call preconditions (`50` calls) — `260` `#guard` assertions total.
-/

namespace LabAtlasLean.Parity

open LabAtlasLean

/-! ## 1. `checkAtlasResource` Boolean Policy Exhaustive Truth Table (160 `#guard`s) -/

#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .permissive, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .permissive, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .permissive, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .permissive, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .shareAlike, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .shareAlike, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .shareAlike, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .shareAlike, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .nonCommercial, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .nonCommercial, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .nonCommercial, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .nonCommercial, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .customTerms, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .customTerms, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .customTerms, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .customTerms, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .evalOnly, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .evalOnly, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .evalOnly, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := false, licenseClass := .evalOnly, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .permissive, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .permissive, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .permissive, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .permissive, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .shareAlike, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .shareAlike, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .shareAlike, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .shareAlike, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .nonCommercial, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .nonCommercial, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .nonCommercial, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .nonCommercial, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .customTerms, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .customTerms, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .customTerms, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .customTerms, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .evalOnly, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .evalOnly, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .evalOnly, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := false, spdxKnown := true, licenseClass := .evalOnly, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .permissive, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .permissive, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .permissive, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .permissive, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .shareAlike, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .shareAlike, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .shareAlike, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .shareAlike, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .nonCommercial, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .nonCommercial, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .nonCommercial, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .nonCommercial, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .customTerms, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .customTerms, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .customTerms, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .customTerms, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .evalOnly, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .evalOnly, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .evalOnly, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := false, licenseClass := .evalOnly, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .permissive, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .permissive, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .permissive, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .permissive, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .shareAlike, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .shareAlike, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .shareAlike, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .shareAlike, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .nonCommercial, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .nonCommercial, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .nonCommercial, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .nonCommercial, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .customTerms, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .customTerms, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .customTerms, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .customTerms, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .evalOnly, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .evalOnly, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .evalOnly, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := false, noPrivateIp := true, spdxKnown := true, licenseClass := .evalOnly, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .permissive, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .permissive, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .permissive, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .permissive, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .shareAlike, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .shareAlike, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .shareAlike, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .shareAlike, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .nonCommercial, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .nonCommercial, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .nonCommercial, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .nonCommercial, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .customTerms, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .customTerms, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .customTerms, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .customTerms, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .evalOnly, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .evalOnly, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .evalOnly, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := false, licenseClass := .evalOnly, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .permissive, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .permissive, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .permissive, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .permissive, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .shareAlike, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .shareAlike, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .shareAlike, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .shareAlike, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .nonCommercial, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .nonCommercial, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .nonCommercial, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .nonCommercial, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .customTerms, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .customTerms, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .customTerms, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .customTerms, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .evalOnly, forTraining := false, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .evalOnly, forTraining := false, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .evalOnly, forTraining := true, commercial := false }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := false, spdxKnown := true, licenseClass := .evalOnly, forTraining := true, commercial := true }).map (·.rule)) == some "https_ssrf_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .permissive, forTraining := false, commercial := false }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .permissive, forTraining := false, commercial := true }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .permissive, forTraining := true, commercial := false }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .permissive, forTraining := true, commercial := true }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .shareAlike, forTraining := false, commercial := false }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .shareAlike, forTraining := false, commercial := true }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .shareAlike, forTraining := true, commercial := false }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .shareAlike, forTraining := true, commercial := true }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .nonCommercial, forTraining := false, commercial := false }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .nonCommercial, forTraining := false, commercial := true }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .nonCommercial, forTraining := true, commercial := false }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .nonCommercial, forTraining := true, commercial := true }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .customTerms, forTraining := false, commercial := false }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .customTerms, forTraining := false, commercial := true }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .customTerms, forTraining := true, commercial := false }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .customTerms, forTraining := true, commercial := true }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .evalOnly, forTraining := false, commercial := false }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .evalOnly, forTraining := false, commercial := true }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .evalOnly, forTraining := true, commercial := false }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := false, licenseClass := .evalOnly, forTraining := true, commercial := true }).map (·.rule)) == some "explicit_spdx_license"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .permissive, forTraining := false, commercial := false }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .permissive, forTraining := false, commercial := true }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .permissive, forTraining := true, commercial := false }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .permissive, forTraining := true, commercial := true }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .shareAlike, forTraining := false, commercial := false }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .shareAlike, forTraining := false, commercial := true }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .shareAlike, forTraining := true, commercial := false }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .shareAlike, forTraining := true, commercial := true }).map (·.rule)) == some "commercial_training_license_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .nonCommercial, forTraining := false, commercial := false }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .nonCommercial, forTraining := false, commercial := true }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .nonCommercial, forTraining := true, commercial := false }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .nonCommercial, forTraining := true, commercial := true }).map (·.rule)) == some "commercial_training_license_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .customTerms, forTraining := false, commercial := false }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .customTerms, forTraining := false, commercial := true }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .customTerms, forTraining := true, commercial := false }).map (·.rule)) == some "academic_training_license_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .customTerms, forTraining := true, commercial := true }).map (·.rule)) == some "academic_training_license_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .evalOnly, forTraining := false, commercial := false }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .evalOnly, forTraining := false, commercial := true }).map (·.rule)) == none
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .evalOnly, forTraining := true, commercial := false }).map (·.rule)) == some "eval_only_contamination_guard"
#guard ((checkAtlasResource { httpsOnly := true, noPrivateIp := true, spdxKnown := true, licenseClass := .evalOnly, forTraining := true, commercial := true }).map (·.rule)) == some "eval_only_contamination_guard"

/-! ## 2. `LicenseClass.conj` Join Truth Table (25 `#guard`s) -/

#guard (LicenseClass.conj .permissive .permissive) == .permissive
#guard (LicenseClass.conj .permissive .shareAlike) == .shareAlike
#guard (LicenseClass.conj .permissive .nonCommercial) == .nonCommercial
#guard (LicenseClass.conj .permissive .customTerms) == .customTerms
#guard (LicenseClass.conj .permissive .evalOnly) == .evalOnly
#guard (LicenseClass.conj .shareAlike .permissive) == .shareAlike
#guard (LicenseClass.conj .shareAlike .shareAlike) == .shareAlike
#guard (LicenseClass.conj .shareAlike .nonCommercial) == .nonCommercial
#guard (LicenseClass.conj .shareAlike .customTerms) == .customTerms
#guard (LicenseClass.conj .shareAlike .evalOnly) == .evalOnly
#guard (LicenseClass.conj .nonCommercial .permissive) == .nonCommercial
#guard (LicenseClass.conj .nonCommercial .shareAlike) == .nonCommercial
#guard (LicenseClass.conj .nonCommercial .nonCommercial) == .nonCommercial
#guard (LicenseClass.conj .nonCommercial .customTerms) == .customTerms
#guard (LicenseClass.conj .nonCommercial .evalOnly) == .evalOnly
#guard (LicenseClass.conj .customTerms .permissive) == .customTerms
#guard (LicenseClass.conj .customTerms .shareAlike) == .customTerms
#guard (LicenseClass.conj .customTerms .nonCommercial) == .customTerms
#guard (LicenseClass.conj .customTerms .customTerms) == .customTerms
#guard (LicenseClass.conj .customTerms .evalOnly) == .evalOnly
#guard (LicenseClass.conj .evalOnly .permissive) == .evalOnly
#guard (LicenseClass.conj .evalOnly .shareAlike) == .evalOnly
#guard (LicenseClass.conj .evalOnly .nonCommercial) == .evalOnly
#guard (LicenseClass.conj .evalOnly .customTerms) == .evalOnly
#guard (LicenseClass.conj .evalOnly .evalOnly) == .evalOnly

/-! ## 3. `LicenseClass.disj` Meet Truth Table (25 `#guard`s) -/

#guard (LicenseClass.disj .permissive .permissive) == .permissive
#guard (LicenseClass.disj .permissive .shareAlike) == .permissive
#guard (LicenseClass.disj .permissive .nonCommercial) == .permissive
#guard (LicenseClass.disj .permissive .customTerms) == .permissive
#guard (LicenseClass.disj .permissive .evalOnly) == .permissive
#guard (LicenseClass.disj .shareAlike .permissive) == .permissive
#guard (LicenseClass.disj .shareAlike .shareAlike) == .shareAlike
#guard (LicenseClass.disj .shareAlike .nonCommercial) == .shareAlike
#guard (LicenseClass.disj .shareAlike .customTerms) == .shareAlike
#guard (LicenseClass.disj .shareAlike .evalOnly) == .shareAlike
#guard (LicenseClass.disj .nonCommercial .permissive) == .permissive
#guard (LicenseClass.disj .nonCommercial .shareAlike) == .shareAlike
#guard (LicenseClass.disj .nonCommercial .nonCommercial) == .nonCommercial
#guard (LicenseClass.disj .nonCommercial .customTerms) == .nonCommercial
#guard (LicenseClass.disj .nonCommercial .evalOnly) == .nonCommercial
#guard (LicenseClass.disj .customTerms .permissive) == .permissive
#guard (LicenseClass.disj .customTerms .shareAlike) == .shareAlike
#guard (LicenseClass.disj .customTerms .nonCommercial) == .nonCommercial
#guard (LicenseClass.disj .customTerms .customTerms) == .customTerms
#guard (LicenseClass.disj .customTerms .evalOnly) == .customTerms
#guard (LicenseClass.disj .evalOnly .permissive) == .permissive
#guard (LicenseClass.disj .evalOnly .shareAlike) == .shareAlike
#guard (LicenseClass.disj .evalOnly .nonCommercial) == .nonCommercial
#guard (LicenseClass.disj .evalOnly .customTerms) == .customTerms
#guard (LicenseClass.disj .evalOnly .evalOnly) == .evalOnly

/-! ## 4. `checkMcpToolCall` 50-Call Benchmark Parity Suite (50 `#guard`s) -/

private def benchCard (lc : LicenseClass) : McpCapabilityCard :=
  { hasTypedNumericBounds := true, forbidsExtraProps := true, requiresDeckEpoch := true,
    spdxKnown := true, licenseClass := lc,
    minVolTenthUL := 10, maxVolTenthUL := 10000, deadVolTenthUL := 150,
    minTempC := 40, maxTempC := 980, sealTempThreshC := 800 }

#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 100, srcWellVolTenthUL := 450, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 920, plateSealed := true, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 250, srcWellVolTenthUL := 600, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 400, srcWellVolTenthUL := 750, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 550, srcWellVolTenthUL := 900, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 700, srcWellVolTenthUL := 1050, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 920, plateSealed := true, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 850, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 1000, srcWellVolTenthUL := 1350, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 1150, srcWellVolTenthUL := 1500, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 1300, srcWellVolTenthUL := 1650, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 920, plateSealed := true, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 1450, srcWellVolTenthUL := 1800, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 1600, srcWellVolTenthUL := 1950, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 1750, srcWellVolTenthUL := 2100, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 1900, srcWellVolTenthUL := 2250, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 920, plateSealed := true, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 2050, srcWellVolTenthUL := 2400, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 2200, srcWellVolTenthUL := 2550, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 2350, srcWellVolTenthUL := 2700, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3500, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == none
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := (-100), srcWellVolTenthUL := 1000, dstWellVolTenthUL := 100, dstWellCapTenthUL := 3000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "volume_envelope_bounds"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := (-5), srcWellVolTenthUL := 1000, dstWellVolTenthUL := 100, dstWellCapTenthUL := 3000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "volume_envelope_bounds"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 0, srcWellVolTenthUL := 1000, dstWellVolTenthUL := 100, dstWellCapTenthUL := 3000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "volume_envelope_bounds"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 1, srcWellVolTenthUL := 1000, dstWellVolTenthUL := 100, dstWellCapTenthUL := 3000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "volume_envelope_bounds"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 4, srcWellVolTenthUL := 1000, dstWellVolTenthUL := 100, dstWellCapTenthUL := 3000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "volume_envelope_bounds"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 8, srcWellVolTenthUL := 1000, dstWellVolTenthUL := 100, dstWellCapTenthUL := 3000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "volume_envelope_bounds"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 10050, srcWellVolTenthUL := 25000, dstWellVolTenthUL := 0, dstWellCapTenthUL := 30000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "volume_envelope_bounds"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 11000, srcWellVolTenthUL := 25000, dstWellVolTenthUL := 0, dstWellCapTenthUL := 30000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "volume_envelope_bounds"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 12500, srcWellVolTenthUL := 25000, dstWellVolTenthUL := 0, dstWellCapTenthUL := 30000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "volume_envelope_bounds"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 15000, srcWellVolTenthUL := 25000, dstWellVolTenthUL := 0, dstWellCapTenthUL := 30000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "volume_envelope_bounds"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 20000, srcWellVolTenthUL := 25000, dstWellVolTenthUL := 0, dstWellCapTenthUL := 30000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "volume_envelope_bounds"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 800, srcWellVolTenthUL := 820, dstWellVolTenthUL := 100, dstWellCapTenthUL := 3000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "dead_volume_and_capacity_guard"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 800, srcWellVolTenthUL := 840, dstWellVolTenthUL := 100, dstWellCapTenthUL := 3000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "dead_volume_and_capacity_guard"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 800, srcWellVolTenthUL := 860, dstWellVolTenthUL := 100, dstWellCapTenthUL := 3000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "dead_volume_and_capacity_guard"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 800, srcWellVolTenthUL := 880, dstWellVolTenthUL := 100, dstWellCapTenthUL := 3000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "dead_volume_and_capacity_guard"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 1500, srcWellVolTenthUL := 2500, dstWellVolTenthUL := 2200, dstWellCapTenthUL := 3000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "dead_volume_and_capacity_guard"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 1500, srcWellVolTenthUL := 2500, dstWellVolTenthUL := 2300, dstWellCapTenthUL := 3000, tempC := 250, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "dead_volume_and_capacity_guard"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 800, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "thermal_and_evaporation_seal_guard"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 850, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "thermal_and_evaporation_seal_guard"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 950, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "thermal_and_evaporation_seal_guard"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 980, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "thermal_and_evaporation_seal_guard"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 1200, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "thermal_and_evaporation_seal_guard"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 0, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "fresh_deck_epoch"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 8, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "fresh_deck_epoch"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 10, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "fresh_deck_epoch"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 11, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "fresh_deck_epoch"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 13, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "fresh_deck_epoch"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 370, plateSealed := false, hasUnknownExtraArgs := true, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "no_unknown_mcp_arguments"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 370, plateSealed := false, hasUnknownExtraArgs := true, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "no_unknown_mcp_arguments"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 370, plateSealed := false, hasUnknownExtraArgs := true, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "no_unknown_mcp_arguments"
#guard ((checkMcpToolCall (benchCard .evalOnly) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := true }).map (·.rule)) == some "eval_only_contamination_guard"
#guard ((checkMcpToolCall (benchCard .nonCommercial) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 500, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := true, forTraining := false }).map (·.rule)) == some "driver_commercial_license_guard"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 0, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := false, forTraining := false }).map (·.rule)) == some "json_type_mismatch"
#guard ((checkMcpToolCall (benchCard .permissive) { tokenEpoch := 12, liveDeckEpoch := 12, volTenthUL := 0, srcWellVolTenthUL := 1200, dstWellVolTenthUL := 200, dstWellCapTenthUL := 3000, tempC := 370, plateSealed := false, hasUnknownExtraArgs := false, commercialContext := true, validJsonTypes := false, forTraining := false }).map (·.rule)) == some "json_type_mismatch"

end LabAtlasLean.Parity
