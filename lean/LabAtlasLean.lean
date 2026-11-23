/-!
# LabAtlasLean: Formal L5 Registry Security, License Contamination & Typed Lean-MCP Cards

Self-contained Lean 4.36.0 formalization for `lab-automation-atlas` (L5 Ecosystem & Hardware
Registry Layer). Models SPDX license classification, HTTPS/SSRF registry guards, benchmark
contamination firewalls (`evalOnly` blocked from training), and typed `Lean-MCP` hardware
capability card compilation and call-envelope checking (tenths of uL `0.1 uL` and integer
degrees Celsius).
-/
namespace LabAtlasLean

/-- License posture harmonized across `lab-automation-atlas` and downstream Auto-Lab gates. -/
inductive LicenseClass where
  | permissive      -- MIT, BSD-3-Clause, Apache-2.0, CC0, CC-BY-4.0
  | shareAlike      -- CC-BY-SA-4.0 (e.g., ORD, Spider, LAB-Bench)
  | nonCommercial   -- CC-BY-NC-*, academic non-commercial corpora
  | evalOnly        -- Benchmark canary corpora strictly forbidden in training
  | customTerms     -- Unpriced vendor feeds or unlicensed repositories
  deriving DecidableEq, Repr

/-- Whether a license class permits unrestricted commercial autonomous training/synthesis. -/
def LicenseClass.commercialTrainOK : LicenseClass → Bool
  | .permissive => true
  | _           => false

/-- Structured violation record reporting rule identifier and diagnostic detail. -/
structure RegimeViolation where
  rule   : String
  detail : String
  deriving DecidableEq, Repr

def firstViolation : List (Bool × RegimeViolation) → Option RegimeViolation
  | [] => none
  | (true, _) :: rest => firstViolation rest
  | (false, v) :: _ => some v

@[simp] theorem firstViolation_nil : firstViolation [] = none := rfl

@[simp] theorem firstViolation_cons (b : Bool) (v : RegimeViolation)
    (rest : List (Bool × RegimeViolation)) :
    firstViolation ((b, v) :: rest) = none ↔ b = true ∧ firstViolation rest = none := by
  cases b <;> simp [firstViolation]

theorem firstViolation_none_iff (checks : List (Bool × RegimeViolation)) :
    firstViolation checks = none ↔ ∀ p ∈ checks, p.1 = true := by
  induction checks with
  | nil => simp [firstViolation]
  | cons hd tl ih =>
    rcases hd with ⟨b, v⟩
    cases b with
    | false => simp [firstViolation]
    | true  => simp [firstViolation, ih]

/-! ## 1. Registry Security, SPDX Governance & Benchmark Contamination Gate -/

structure AtlasResource where
  httpsOnly    : Bool
  noPrivateIp  : Bool
  spdxKnown    : Bool
  licenseClass : LicenseClass
  forTraining  : Bool
  commercial   : Bool
  deriving DecidableEq, Repr

structure AtlasResourceOK (r : AtlasResource) : Prop where
  httpsSafe      : r.httpsOnly = true ∧ r.noPrivateIp = true
  spdxVerified   : r.spdxKnown = true
  noEvalLeakage  : ¬r.forTraining ∨ r.licenseClass ≠ .evalOnly
  commercialSafe : ¬(r.forTraining ∧ r.commercial) ∨ r.licenseClass.commercialTrainOK = true

def checkAtlasResource (r : AtlasResource) : Option RegimeViolation :=
  firstViolation
    [ (r.httpsOnly && r.noPrivateIp,
        { rule := "https_ssrf_guard",
          detail := "external resource URL must use HTTPS and must not target private/loopback IPs" }),
      (r.spdxKnown,
        { rule := "explicit_spdx_license",
          detail := "resource lacks a verified SPDX or explicit custom license record" }),
      (decide (¬r.forTraining ∨ r.licenseClass ≠ .evalOnly),
        { rule := "eval_only_contamination_guard",
          detail := "eval_only benchmark (e.g. LAB-Bench) cannot enter training pipelines" }),
      (decide (¬(r.forTraining ∧ r.commercial) ∨ r.licenseClass.commercialTrainOK = true),
        { rule := "commercial_training_license_guard",
          detail := "non-permissive or non-commercial corpus blocked from commercial training" }) ]

theorem checkAtlasResource_ok_iff (r : AtlasResource) :
    checkAtlasResource r = none ↔ AtlasResourceOK r := by
  unfold checkAtlasResource
  simp only [firstViolation_cons, firstViolation_nil, and_true, Bool.and_eq_true, decide_eq_true_eq]
  constructor
  · rintro ⟨h1, h2, h3, h4⟩; exact ⟨h1, h2, h3, h4⟩
  · rintro ⟨h1, h2, h3, h4⟩; exact ⟨h1, h2, h3, h4⟩

/-- Hard boundary theorem: `evalOnly` benchmarks are provably blocked from all training pipelines. -/
theorem eval_only_blocked_from_training (r : AtlasResource)
    (htr : r.forTraining = true) (hev : r.licenseClass = .evalOnly) :
    checkAtlasResource r ≠ none := by
  intro hok
  unfold checkAtlasResource at hok
  simp only [firstViolation_cons, firstViolation_nil, and_true, decide_eq_true_eq] at hok
  rcases hok with ⟨_, _, h3, _⟩
  simp [htr, hev] at h3

/-- Hard boundary theorem: Non-HTTPS or private-IP targets are always blocked (SSRF guard). -/
theorem http_or_private_ip_rejected (r : AtlasResource)
    (hbad : r.httpsOnly = false ∨ r.noPrivateIp = false) :
    checkAtlasResource r ≠ none := by
  intro hok
  have hs := ((checkAtlasResource_ok_iff r).mp hok).httpsSafe
  rcases hbad with hh | hip
  · rw [hh] at hs; simp at hs
  · rw [hip] at hs; simp at hs

/-- Hard boundary theorem: Non-permissive corpora cannot enter commercial training. -/
theorem non_permissive_blocked_from_commercial_training (r : AtlasResource)
    (htr : r.forTraining = true) (hcom : r.commercial = true)
    (hnp : r.licenseClass ≠ .permissive) :
    checkAtlasResource r ≠ none := by
  intro hok
  have hc := ((checkAtlasResource_ok_iff r).mp hok).commercialSafe
  cases hlic : r.licenseClass <;> simp [htr, hcom, hlic, LicenseClass.commercialTrainOK] at hc hnp

/-! ## 2. Idea #09: Typed `Lean-MCP` Hardware Capability Card & Envelope Gate -/

/-- Typed hardware capability specification compiled into a strict JSON-Schema MCP tool card.
    Volumes are represented in tenths of a microliter (`0.1 uL`). -/
structure McpCapabilityCard where
  hasTypedNumericBounds : Bool
  forbidsExtraProps     : Bool
  requiresDeckEpoch     : Bool
  spdxKnown             : Bool
  licenseClass          : LicenseClass
  minVolTenthUL         : Nat
  maxVolTenthUL         : Nat
  deadVolTenthUL        : Nat
  minTempC              : Nat
  maxTempC              : Nat
  sealTempThreshC       : Nat
  deriving DecidableEq, Repr

/-- Compile-time validity check rejecting prompt-only or untyped MCP tool descriptors. -/
def checkMcpCardSpec (c : McpCapabilityCard) : Option RegimeViolation :=
  firstViolation
    [ (c.hasTypedNumericBounds && c.forbidsExtraProps,
        { rule := "typed_closed_json_schema",
          detail := "prompt-only or open schema rejected; explicit numeric bounds and additionalProperties=false required" }),
      (c.requiresDeckEpoch,
        { rule := "mandatory_deck_epoch_field",
          detail := "MCP hardware card must require deck_epoch to prevent stale-state replay" }),
      (c.spdxKnown,
        { rule := "explicit_spdx_license",
          detail := "MCP driver card lacks an explicit SPDX license classification" }),
      (decide (0 < c.minVolTenthUL ∧ c.minVolTenthUL ≤ c.maxVolTenthUL ∧
               c.minTempC ≤ c.maxTempC ∧ c.minTempC ≤ c.sealTempThreshC),
        { rule := "well_formed_physical_bounds",
          detail := "MCP capability card has inverted or zero physical volume/temperature intervals" }) ]

/-- Runtime call arguments checked against a compiled `McpCapabilityCard`. -/
structure McpToolCall where
  tokenEpoch          : Nat
  liveDeckEpoch       : Nat
  volTenthUL          : Nat
  srcWellVolTenthUL   : Nat
  dstWellVolTenthUL   : Nat
  dstWellCapTenthUL   : Nat
  tempC               : Nat
  plateSealed         : Bool
  hasUnknownExtraArgs : Bool
  commercialContext   : Bool
  deriving DecidableEq, Repr

/-- Executable precondition guard for every incoming MCP hardware tool invocation. -/
def checkMcpToolCall (c : McpCapabilityCard) (call : McpToolCall) : Option RegimeViolation :=
  match checkMcpCardSpec c with
  | some v => some v
  | none =>
    firstViolation
      [ (!call.hasUnknownExtraArgs,
          { rule := "no_unknown_mcp_arguments",
            detail := "MCP tool call contains undeclared hallucinated parameters" }),
        (decide (call.tokenEpoch == call.liveDeckEpoch),
          { rule := "fresh_deck_epoch",
            detail := "MCP call deck_epoch does not match live physical deck state" }),
        (decide (c.minVolTenthUL ≤ call.volTenthUL ∧ call.volTenthUL ≤ c.maxVolTenthUL),
          { rule := "volume_envelope_bounds",
            detail := "requested volume_ul falls outside hardware [min, max] pipette envelope" }),
        (decide (c.deadVolTenthUL + call.volTenthUL ≤ call.srcWellVolTenthUL ∧
                 call.dstWellVolTenthUL + call.volTenthUL ≤ call.dstWellCapTenthUL),
          { rule := "dead_volume_and_capacity_guard",
            detail := "aspiration underflows dead-volume floor or dispense overflows destination well" }),
        (decide (c.minTempC ≤ call.tempC ∧ call.tempC ≤ c.maxTempC ∧
                 (call.tempC < c.sealTempThreshC ∨ call.plateSealed = true)),
          { rule := "thermal_and_evaporation_seal_guard",
            detail := "temperature outside envelope or >= seal threshold on an unsealed plate" }),
        (decide (!call.commercialContext ∨ c.licenseClass.commercialTrainOK = true),
          { rule := "driver_commercial_license_guard",
            detail := "MCP hardware driver license does not permit commercial autonomous execution" }) ]

/-- Prompt-only schemas (`hasTypedNumericBounds = false`) or cards missing `requiresDeckEpoch` are rejected. -/
theorem untyped_or_epochless_card_rejected (c : McpCapabilityCard)
    (hbad : c.hasTypedNumericBounds = false ∨ c.forbidsExtraProps = false ∨ c.requiresDeckEpoch = false) :
    checkMcpCardSpec c ≠ none := by
  intro hok
  unfold checkMcpCardSpec at hok
  simp only [firstViolation_cons, firstViolation_nil, and_true, Bool.and_eq_true] at hok
  rcases hok with ⟨⟨ht, hf⟩, he, _, _⟩
  rcases hbad with h1 | h2 | h3
  · rw [h1] at ht; contradiction
  · rw [h2] at hf; contradiction
  · rw [h3] at he; contradiction

/-- Out-of-envelope calls (stale epoch, dead-volume underflow, or unsealed high-temp) are intercepted. -/
theorem out_of_envelope_mcp_call_intercepted (c : McpCapabilityCard) (call : McpToolCall)
    (hviol : call.tokenEpoch ≠ call.liveDeckEpoch ∨
             call.srcWellVolTenthUL < c.deadVolTenthUL + call.volTenthUL ∨
             (c.sealTempThreshC ≤ call.tempC ∧ call.plateSealed = false)) :
    checkMcpToolCall c call ≠ none := by
  intro hok
  unfold checkMcpToolCall at hok
  cases hcard : checkMcpCardSpec c with
  | some v => simp [hcard] at hok
  | none =>
    simp only [hcard, firstViolation_cons, firstViolation_nil, and_true,
               decide_eq_true_eq, beq_iff_eq] at hok
    rcases hok with ⟨_, hep, _, ⟨hdead, _⟩, ⟨_, _, hseal⟩, _⟩
    rcases hviol with he | hd | ⟨ht, hps⟩
    · exact he hep
    · omega
    · rcases hseal with hlt | hpst
      · omega
      · rw [hps] at hpst; contradiction

/-! ## Compile-Time `#guard` Verification Witnesses -/

#guard (checkAtlasResource
         { httpsOnly := true, noPrivateIp := true, spdxKnown := true,
           licenseClass := .permissive, forTraining := true, commercial := true }).isNone == true

#guard (checkAtlasResource
         { httpsOnly := true, noPrivateIp := true, spdxKnown := true,
           licenseClass := .evalOnly, forTraining := true, commercial := false }).isSome == true

#guard (checkAtlasResource
         { httpsOnly := false, noPrivateIp := true, spdxKnown := true,
           licenseClass := .permissive, forTraining := false, commercial := false }).isSome == true

private def sampleHamiltonCard : McpCapabilityCard :=
  { hasTypedNumericBounds := true, forbidsExtraProps := true, requiresDeckEpoch := true,
    spdxKnown := true, licenseClass := .permissive,
    minVolTenthUL := 10, maxVolTenthUL := 10000, deadVolTenthUL := 150,
    minTempC := 4, maxTempC := 98, sealTempThreshC := 80 }

#guard (checkMcpCardSpec sampleHamiltonCard).isNone == true

#guard (checkMcpCardSpec { sampleHamiltonCard with hasTypedNumericBounds := false }).isSome == true

#guard (checkMcpToolCall sampleHamiltonCard
         { tokenEpoch := 7, liveDeckEpoch := 7, volTenthUL := 500,
           srcWellVolTenthUL := 1000, dstWellVolTenthUL := 200, dstWellCapTenthUL := 2000,
           tempC := 37, plateSealed := false, hasUnknownExtraArgs := false,
           commercialContext := true }).isNone == true

#guard (checkMcpToolCall sampleHamiltonCard
         { tokenEpoch := 6, liveDeckEpoch := 7, volTenthUL := 500,
           srcWellVolTenthUL := 1000, dstWellVolTenthUL := 200, dstWellCapTenthUL := 2000,
           tempC := 37, plateSealed := false, hasUnknownExtraArgs := false,
           commercialContext := true }).isSome == true

#guard (checkMcpToolCall sampleHamiltonCard
         { tokenEpoch := 7, liveDeckEpoch := 7, volTenthUL := 500,
           srcWellVolTenthUL := 600, dstWellVolTenthUL := 200, dstWellCapTenthUL := 2000,
           tempC := 37, plateSealed := false, hasUnknownExtraArgs := false,
           commercialContext := true }).isSome == true

end LabAtlasLean
