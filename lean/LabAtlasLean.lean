/-!
# LabAtlasLean: Formal L5 Registry Security, License Lattice, Lineage Taint & Typed Lean-MCP Cards

Self-contained Lean 4.36.0 formalization for `lab-automation-atlas` (L5 Ecosystem & Hardware
Registry Layer). Models:
1. Bounded distributive license lattice (`LicenseClass.conj` for SPDX `AND` / multi-corpus
   derivation and `LicenseClass.disj` for SPDX `OR` / dual-license choice) with `.permissive`
   bottom and absorptive `.evalOnly` top.
2. Transitive dataset-derivation taint propagation across parent lists (`effectiveLicense`) and
   arbitrary-depth derivation DAGs (`LineageDAG`), proving that any `.evalOnly` or non-trainable
   `.customTerms` ancestor blocks downstream training.
3. HTTPS/SSRF registry guards and default-deny training gates (`customTerms` and `evalOnly`
   rejected across both commercial and academic training).
4. Typed `Lean-MCP` hardware capability card compilation and call-envelope checking in fixed-point
   tenths of a microliter (`0.1 uL`) and signed tenths of degrees Celsius (`TenthC := Int`,
   supporting cryogenic/cold-block envelopes down to `-200.0 C`).
-/
namespace LabAtlasLean

/-- Signed fixed-point temperature in tenths of degrees Celsius (`-800` = `-80.0 C`, `370` = `37.0 C`). -/
abbrev TenthC := Int

/-- Minimum representable laboratory thermal bound (`-200.0 C` = `-2000` tenths C, above `0 K`). -/
def minCryoFloorTenthC : TenthC := -2000

/-- License posture harmonized across `lab-automation-atlas` and downstream Auto-Lab gates.
    Ordered by restrictiveness:
    `permissive (0) < shareAlike (1) < nonCommercial (2) < customTerms (3) < evalOnly (4)`. -/
inductive LicenseClass where
  | permissive      -- MIT, BSD-3-Clause, Apache-2.0, CC0-1.0, CC-BY-4.0
  | shareAlike      -- CC-BY-SA-4.0, AGPL-3.0-only, GPL-*
  | nonCommercial   -- CC-BY-NC-*, academic non-commercial corpora
  | evalOnly        -- Benchmark canary corpora strictly forbidden in training (absorptive top)
  | customTerms     -- NOASSERTION, LicenseRef-Per-Article, LicenseRef-Proprietary, unknown SPDX
  deriving DecidableEq, Repr

/-- Monotone restrictiveness rank (`0` least restrictive .. `4` absorptive contamination top). -/
def LicenseClass.rank : LicenseClass → Nat
  | .permissive    => 0
  | .shareAlike    => 1
  | .nonCommercial => 2
  | .customTerms   => 3
  | .evalOnly      => 4

/-- Restrictiveness partial/total order (`a ≤ b` means `b` is at least as restrictive as `a`). -/
def LicenseClass.le (a b : LicenseClass) : Prop := a.rank ≤ b.rank

instance : LE LicenseClass := ⟨LicenseClass.le⟩

instance (a b : LicenseClass) : Decidable (a ≤ b) :=
  inferInstanceAs (Decidable (a.rank ≤ b.rank))

/-- Whether a license class permits unrestricted commercial autonomous training/synthesis. -/
def LicenseClass.commercialTrainOK : LicenseClass → Bool
  | .permissive => true
  | _           => false

/-- Whether a license class permits academic (non-commercial) training.
    Default-deny: `.customTerms` (`NOASSERTION`, `LicenseRef-*`) and `.evalOnly` are rejected. -/
def LicenseClass.academicTrainOK : LicenseClass → Bool
  | .permissive    => true
  | .shareAlike    => true
  | .nonCommercial => true
  | .customTerms   => false
  | .evalOnly      => false

/-- Join (`⊔`) in the restrictiveness lattice: SPDX `AND` and multi-parent dataset derivation. -/
def LicenseClass.conj (a b : LicenseClass) : LicenseClass :=
  if b.rank ≤ a.rank then a else b

/-- Meet (`⊓`) in the restrictiveness lattice: SPDX `OR` dual-license election. -/
def LicenseClass.disj (a b : LicenseClass) : LicenseClass :=
  if a.rank ≤ b.rank then a else b

/-! ## 1. Bounded Distributive License Lattice & Join-Semilattice Theorems -/

theorem LicenseClass.rank_injective {a b : LicenseClass} (h : a.rank = b.rank) : a = b := by
  cases a <;> cases b <;> simp [LicenseClass.rank] at h <;> rfl

theorem LicenseClass.le_refl (a : LicenseClass) : a ≤ a := Nat.le_refl a.rank

theorem LicenseClass.le_trans {a b c : LicenseClass} (hab : a ≤ b) (hbc : b ≤ c) : a ≤ c :=
  Nat.le_trans hab hbc

theorem LicenseClass.le_antisymm {a b : LicenseClass} (hab : a ≤ b) (hba : b ≤ a) : a = b :=
  LicenseClass.rank_injective (Nat.le_antisymm hab hba)

/-- `.permissive` is the least restrictive bottom element (`⊥`). -/
theorem LicenseClass.permissive_le (a : LicenseClass) : LicenseClass.permissive ≤ a :=
  Nat.zero_le a.rank

/-- `.evalOnly` is the most restrictive top element (`⊤`). -/
theorem LicenseClass.le_evalOnly (a : LicenseClass) : a ≤ LicenseClass.evalOnly := by
  cases a <;> decide

@[simp] theorem LicenseClass.conj_comm (a b : LicenseClass) : a.conj b = b.conj a := by
  cases a <;> cases b <;> rfl

@[simp] theorem LicenseClass.conj_assoc (a b c : LicenseClass) :
    (a.conj b).conj c = a.conj (b.conj c) := by
  cases a <;> cases b <;> cases c <;> rfl

@[simp] theorem LicenseClass.conj_idem (a : LicenseClass) : a.conj a = a := by
  cases a <;> rfl

@[simp] theorem LicenseClass.permissive_conj (a : LicenseClass) :
    LicenseClass.permissive.conj a = a := by
  cases a <;> rfl

@[simp] theorem LicenseClass.conj_permissive (a : LicenseClass) :
    a.conj .permissive = a := by
  cases a <;> rfl

/-- Absorptive contamination taint: `.evalOnly` dominates any conjunction on the left. -/
@[simp] theorem LicenseClass.evalOnly_conj (a : LicenseClass) :
    LicenseClass.evalOnly.conj a = .evalOnly := by
  cases a <;> rfl

/-- Absorptive contamination taint: `.evalOnly` dominates any conjunction on the right. -/
@[simp] theorem LicenseClass.conj_evalOnly (a : LicenseClass) :
    a.conj .evalOnly = .evalOnly := by
  cases a <;> rfl

theorem LicenseClass.le_conj_left (a b : LicenseClass) : a ≤ a.conj b := by
  cases a <;> cases b <;> decide

theorem LicenseClass.le_conj_right (a b : LicenseClass) : b ≤ a.conj b := by
  cases a <;> cases b <;> decide

/-- Least-upper-bound universal property confirming `(LicenseClass, ≤, conj)` is a join-semilattice. -/
theorem LicenseClass.conj_lub {a b c : LicenseClass} (hac : a ≤ c) (hbc : b ≤ c) :
    a.conj b ≤ c := by
  cases a <;> cases b <;> cases c <;> revert hac hbc <;> decide

@[simp] theorem LicenseClass.disj_comm (a b : LicenseClass) : a.disj b = b.disj a := by
  cases a <;> cases b <;> rfl

@[simp] theorem LicenseClass.disj_assoc (a b c : LicenseClass) :
    (a.disj b).disj c = a.disj (b.disj c) := by
  cases a <;> cases b <;> cases c <;> rfl

@[simp] theorem LicenseClass.disj_idem (a : LicenseClass) : a.disj a = a := by
  cases a <;> rfl

@[simp] theorem LicenseClass.conj_disj_absorb (a b : LicenseClass) :
    a.conj (a.disj b) = a := by
  cases a <;> cases b <;> rfl

@[simp] theorem LicenseClass.disj_conj_absorb (a b : LicenseClass) :
    a.disj (a.conj b) = a := by
  cases a <;> cases b <;> rfl

/-- Monotonicity (antitonicity in restrictiveness) of `commercialTrainOK`. -/
theorem LicenseClass.commercialTrainOK_antitone {a b : LicenseClass} (hle : a ≤ b) :
    b.commercialTrainOK = true → a.commercialTrainOK = true := by
  cases a <;> cases b <;> revert hle <;> decide

/-- Monotonicity (antitonicity in restrictiveness) of `academicTrainOK`. -/
theorem LicenseClass.academicTrainOK_antitone {a b : LicenseClass} (hle : a ≤ b) :
    b.academicTrainOK = true → a.academicTrainOK = true := by
  cases a <;> cases b <;> revert hle <;> decide

theorem LicenseClass.commercialTrainOK_imp_academicTrainOK (a : LicenseClass) :
    a.commercialTrainOK = true → a.academicTrainOK = true := by
  cases a <;> decide

@[simp] theorem LicenseClass.commercialTrainOK_conj (a b : LicenseClass) :
    (a.conj b).commercialTrainOK = (a.commercialTrainOK && b.commercialTrainOK) := by
  cases a <;> cases b <;> rfl

@[simp] theorem LicenseClass.academicTrainOK_conj (a b : LicenseClass) :
    (a.conj b).academicTrainOK = (a.academicTrainOK && b.academicTrainOK) := by
  cases a <;> cases b <;> rfl

@[simp] theorem LicenseClass.commercialTrainOK_disj (a b : LicenseClass) :
    (a.disj b).commercialTrainOK = (a.commercialTrainOK || b.commercialTrainOK) := by
  cases a <;> cases b <;> rfl

@[simp] theorem LicenseClass.academicTrainOK_disj (a b : LicenseClass) :
    (a.disj b).academicTrainOK = (a.academicTrainOK || b.academicTrainOK) := by
  cases a <;> cases b <;> rfl

/-! ## 2. Transitive Dataset-Derivation Lineage & Taint Propagation -/

/-- Effective license posture of a corpus with declared `own` license derived from `parents`. -/
def effectiveLicense (parents : List LicenseClass) (own : LicenseClass) : LicenseClass :=
  parents.foldl LicenseClass.conj own

theorem own_le_effectiveLicense (parents : List LicenseClass) (own : LicenseClass) :
    own ≤ effectiveLicense parents own := by
  induction parents generalizing own with
  | nil => exact LicenseClass.le_refl own
  | cons hd tl ih =>
    exact LicenseClass.le_trans (LicenseClass.le_conj_left own hd) (ih (own.conj hd))

theorem parent_le_effectiveLicense (parents : List LicenseClass) (own p : LicenseClass)
    (hp : p ∈ parents) : p ≤ effectiveLicense parents own := by
  induction parents generalizing own with
  | nil => nomatch hp
  | cons hd tl ih =>
    rcases List.mem_cons.mp hp with rfl | htl
    · exact LicenseClass.le_trans (LicenseClass.le_conj_right own p)
        (own_le_effectiveLicense tl (own.conj p))
    · exact ih (own.conj hd) htl

/-- Any `.evalOnly` parent taints `effectiveLicense` to `.evalOnly` regardless of child `own` license. -/
theorem evalOnly_mem_imp_effectiveLicense_evalOnly (parents : List LicenseClass)
    (own : LicenseClass) (hev : LicenseClass.evalOnly ∈ parents) :
    effectiveLicense parents own = .evalOnly := by
  apply LicenseClass.le_antisymm (LicenseClass.le_evalOnly _)
  exact parent_le_effectiveLicense parents own .evalOnly hev

/-- Multi-hop dataset derivation lineage tree/DAG witness. -/
inductive LineageDAG where
  | leaf (lic : LicenseClass)
  | derived (own : LicenseClass) (parents : List LineageDAG)
  deriving Repr

mutual
  /-- Compute transitive effective license across an arbitrary-depth derivation DAG. -/
  def LineageDAG.effective : LineageDAG → LicenseClass
    | .leaf lic => lic
    | .derived own parents => LineageDAG.effectiveList parents own

  def LineageDAG.effectiveList : List LineageDAG → LicenseClass → LicenseClass
    | [], acc => acc
    | p :: ps, acc => LineageDAG.effectiveList ps (acc.conj p.effective)
end

mutual
  /-- Flatten all ancestor and self license declarations in a `LineageDAG`. -/
  def LineageDAG.allLicenses : LineageDAG → List LicenseClass
    | .leaf lic => [lic]
    | .derived own parents => own :: LineageDAG.allLicensesList parents

  def LineageDAG.allLicensesList : List LineageDAG → List LicenseClass
    | [] => []
    | p :: ps => p.allLicenses ++ LineageDAG.allLicensesList ps
end

theorem LineageDAG.acc_le_effectiveList (ps : List LineageDAG) (acc : LicenseClass) :
    acc ≤ LineageDAG.effectiveList ps acc := by
  induction ps generalizing acc with
  | nil => exact LicenseClass.le_refl acc
  | cons p rest ih =>
    simp only [LineageDAG.effectiveList]
    exact LicenseClass.le_trans (LicenseClass.le_conj_left acc p.effective)
      (ih (acc.conj p.effective))

mutual
  theorem LineageDAG.ancestor_le_effective :
      (d : LineageDAG) → (c : LicenseClass) → c ∈ d.allLicenses → c ≤ d.effective
    | .leaf lic, c, hc => by
        simp [LineageDAG.allLicenses, LineageDAG.effective] at hc ⊢
        subst hc
        exact LicenseClass.le_refl _
    | .derived own parents, c, hc => by
        simp only [LineageDAG.allLicenses, LineageDAG.effective, List.mem_cons] at hc ⊢
        rcases hc with rfl | hrest
        · exact LineageDAG.acc_le_effectiveList parents c
        · exact LineageDAG.ancestorList_le parents own c hrest

  theorem LineageDAG.ancestorList_le :
      (ps : List LineageDAG) → (acc c : LicenseClass) →
        c ∈ LineageDAG.allLicensesList ps →
        c ≤ LineageDAG.effectiveList ps acc
    | [], _, _, h => nomatch h
    | p :: rest, acc, c, h => by
        simp only [LineageDAG.allLicensesList, LineageDAG.effectiveList, List.mem_append] at h ⊢
        rcases h with hp | htl
        · have hpe : c ≤ p.effective := LineageDAG.ancestor_le_effective p c hp
          have hconj : p.effective ≤ acc.conj p.effective :=
            LicenseClass.le_conj_right acc p.effective
          exact LicenseClass.le_trans hpe
            (LicenseClass.le_trans hconj (LineageDAG.acc_le_effectiveList rest (acc.conj p.effective)))
        · exact LineageDAG.ancestorList_le rest (acc.conj p.effective) c htl
end

/-- Transitive DAG taint theorem: an `.evalOnly` ancestor at any depth forces `d.effective = .evalOnly`. -/
theorem LineageDAG.evalOnly_ancestor_taints_dag (d : LineageDAG)
    (hev : LicenseClass.evalOnly ∈ d.allLicenses) :
    d.effective = .evalOnly := by
  apply LicenseClass.le_antisymm (LicenseClass.le_evalOnly _)
  exact LineageDAG.ancestor_le_effective d .evalOnly hev

/-! ## 3. Registry Security, SPDX Governance & Benchmark Contamination Gate -/

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
  academicSafe   : ¬r.forTraining ∨ r.licenseClass.academicTrainOK = true
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
      (decide (¬r.forTraining ∨ r.licenseClass.academicTrainOK = true),
        { rule := "academic_training_license_guard",
          detail := "custom_terms or unverified license (NOASSERTION / LicenseRef) blocked from training" }),
      (decide (¬(r.forTraining ∧ r.commercial) ∨ r.licenseClass.commercialTrainOK = true),
        { rule := "commercial_training_license_guard",
          detail := "non-permissive or non-commercial corpus blocked from commercial training" }) ]

theorem checkAtlasResource_ok_iff (r : AtlasResource) :
    checkAtlasResource r = none ↔ AtlasResourceOK r := by
  unfold checkAtlasResource
  simp only [firstViolation_cons, firstViolation_nil, and_true, Bool.and_eq_true, decide_eq_true_eq]
  constructor
  · rintro ⟨h1, h2, h3, h4, h5⟩; exact ⟨h1, h2, h3, h4, h5⟩
  · rintro ⟨h1, h2, h3, h4, h5⟩; exact ⟨h1, h2, h3, h4, h5⟩

/-- Hard boundary theorem: `evalOnly` benchmarks are provably blocked from all training pipelines. -/
theorem eval_only_blocked_from_training (r : AtlasResource)
    (htr : r.forTraining = true) (hev : r.licenseClass = .evalOnly) :
    checkAtlasResource r ≠ none := by
  intro hok
  have hno := ((checkAtlasResource_ok_iff r).mp hok).noEvalLeakage
  simp [htr, hev] at hno

/-- Hard boundary theorem: `.customTerms` (`NOASSERTION`, `LicenseRef-Per-Article`, `LicenseRef-Proprietary`)
    is rejected across **all** training (`commercial = true` and `commercial = false` alike). -/
theorem custom_terms_blocked_from_all_training (r : AtlasResource)
    (htr : r.forTraining = true) (hct : r.licenseClass = .customTerms) :
    checkAtlasResource r ≠ none := by
  intro hok
  have hac := ((checkAtlasResource_ok_iff r).mp hok).academicSafe
  simp [htr, hct, LicenseClass.academicTrainOK] at hac

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

/-- Transitive contamination theorem: if any parent in `parents` is `.evalOnly`, a derived dataset
    cannot pass `checkAtlasResource` when `forTraining = true`, even if `own = .permissive`. -/
theorem eval_ancestor_blocks_derived_training (parents : List LicenseClass) (own : LicenseClass)
    (r : AtlasResource) (heff : r.licenseClass = effectiveLicense parents own)
    (htr : r.forTraining = true) (hev : LicenseClass.evalOnly ∈ parents) :
    checkAtlasResource r ≠ none := by
  apply eval_only_blocked_from_training r htr
  rw [heff]
  exact evalOnly_mem_imp_effectiveLicense_evalOnly parents own hev

/-- General ancestor taint theorem: any non-trainable parent (`academicTrainOK = false`, i.e.,
    `.evalOnly` or `.customTerms`) blocks all downstream training. -/
theorem untrainable_ancestor_blocks_derived_training (parents : List LicenseClass)
    (own p : LicenseClass) (r : AtlasResource)
    (heff : r.licenseClass = effectiveLicense parents own)
    (htr : r.forTraining = true) (hp : p ∈ parents) (hnt : p.academicTrainOK = false) :
    checkAtlasResource r ≠ none := by
  intro hok
  have hac := ((checkAtlasResource_ok_iff r).mp hok).academicSafe
  have htr_ok : r.licenseClass.academicTrainOK = true := by
    rcases hac with hnot | hyes
    · simp [htr] at hnot
    · exact hyes
  rw [heff] at htr_ok
  have hle : p ≤ effectiveLicense parents own := parent_le_effectiveLicense parents own p hp
  have hp_ok : p.academicTrainOK = true := LicenseClass.academicTrainOK_antitone hle htr_ok
  rw [hnt] at hp_ok
  contradiction

/-- Multi-hop DAG contamination theorem: any `.evalOnly` ancestor at arbitrary depth blocks training. -/
theorem dag_eval_ancestor_blocks_training (d : LineageDAG) (r : AtlasResource)
    (heff : r.licenseClass = d.effective) (htr : r.forTraining = true)
    (hev : LicenseClass.evalOnly ∈ d.allLicenses) :
    checkAtlasResource r ≠ none := by
  apply eval_only_blocked_from_training r htr
  rw [heff]
  exact LineageDAG.evalOnly_ancestor_taints_dag d hev

/-! ## 4. Idea #09: Typed `Lean-MCP` Hardware Capability Card & Signed Thermal Envelope Gate -/

/-- Typed hardware capability specification compiled into a strict JSON-Schema MCP tool card.
    Volumes are represented in tenths of a microliter (`0.1 uL`) and temperatures in signed
    tenths of degrees Celsius (`TenthC`, supporting cryogenic envelopes down to `-200.0 C`). -/
structure McpCapabilityCard where
  hasTypedNumericBounds : Bool
  forbidsExtraProps     : Bool
  requiresDeckEpoch     : Bool
  spdxKnown             : Bool
  licenseClass          : LicenseClass
  minVolTenthUL         : Nat
  maxVolTenthUL         : Nat
  deadVolTenthUL        : Nat
  minTempC              : TenthC
  maxTempC              : TenthC
  sealTempThreshC       : TenthC
  deriving DecidableEq, Repr

/-- Compile-time validity check rejecting prompt-only, untyped, or physically inverted MCP cards. -/
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
               minCryoFloorTenthC ≤ c.minTempC ∧
               c.minTempC ≤ c.maxTempC ∧ c.minTempC ≤ c.sealTempThreshC),
        { rule := "well_formed_physical_bounds",
          detail := "MCP capability card has inverted, zero-volume, or below-cryo-floor physical bounds" }) ]

/-- Runtime call arguments checked against a compiled `McpCapabilityCard`. -/
structure McpToolCall where
  tokenEpoch          : Nat
  liveDeckEpoch       : Nat
  volTenthUL          : Int
  srcWellVolTenthUL   : Int
  dstWellVolTenthUL   : Int
  dstWellCapTenthUL   : Int
  tempC               : TenthC
  plateSealed         : Bool
  hasUnknownExtraArgs : Bool
  commercialContext   : Bool
  validJsonTypes      : Bool := true
  forTraining         : Bool := false
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
        (call.validJsonTypes,
          { rule := "json_type_mismatch",
            detail := "MCP tool call field fails numeric or boolean JSON schema type check" }),
        (decide (call.tokenEpoch == call.liveDeckEpoch),
          { rule := "fresh_deck_epoch",
            detail := "MCP call deck_epoch does not match live physical deck state" }),
        (decide ((c.minVolTenthUL : Int) ≤ call.volTenthUL ∧ call.volTenthUL ≤ (c.maxVolTenthUL : Int)),
          { rule := "volume_envelope_bounds",
            detail := "requested volume_ul falls outside hardware [min, max] pipette envelope" }),
        (decide ((c.deadVolTenthUL : Int) + call.volTenthUL ≤ call.srcWellVolTenthUL ∧
                 call.dstWellVolTenthUL + call.volTenthUL ≤ call.dstWellCapTenthUL),
          { rule := "dead_volume_and_capacity_guard",
            detail := "aspiration underflows dead-volume floor or dispense overflows destination well" }),
        (decide (c.minTempC ≤ call.tempC ∧ call.tempC ≤ c.maxTempC ∧
                 (call.tempC < c.sealTempThreshC ∨ call.plateSealed = true)),
          { rule := "thermal_and_evaporation_seal_guard",
            detail := "temperature outside envelope or >= seal threshold on an unsealed plate" }),
        (decide (!call.forTraining ∨ c.licenseClass ≠ .evalOnly),
          { rule := "eval_only_contamination_guard",
            detail := "eval_only resource blocked from training pipeline" }),
        (decide (!call.forTraining ∨ c.licenseClass.academicTrainOK = true),
          { rule := "academic_training_license_guard",
            detail := "custom_terms license class blocked from training pipelines" }),
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
             call.srcWellVolTenthUL < (c.deadVolTenthUL : Int) + call.volTenthUL ∨
             (c.sealTempThreshC ≤ call.tempC ∧ call.plateSealed = false)) :
    checkMcpToolCall c call ≠ none := by
  intro hok
  unfold checkMcpToolCall at hok
  cases hcard : checkMcpCardSpec c with
  | some v => simp [hcard] at hok
  | none =>
    simp only [hcard, firstViolation_cons, firstViolation_nil, and_true,
               decide_eq_true_eq, beq_iff_eq] at hok
    rcases hok with ⟨_, _, hep, _, ⟨hdead, _⟩, ⟨_, _, hseal⟩, _, _, _⟩
    rcases hviol with he | hd | ⟨ht, hps⟩
    · exact he hep
    · omega
    · rcases hseal with hlt | hpst
      · exact absurd hlt (Int.not_lt.mpr ht)
      · rw [hps] at hpst; contradiction

/-! ## Compile-Time `#guard` Verification Witnesses -/

#guard (checkAtlasResource
         { httpsOnly := true, noPrivateIp := true, spdxKnown := true,
           licenseClass := .permissive, forTraining := true, commercial := true }).isNone == true

#guard (checkAtlasResource
         { httpsOnly := true, noPrivateIp := true, spdxKnown := true,
           licenseClass := .evalOnly, forTraining := true, commercial := false }).isSome == true

-- Issue #26 regression witness: `.customTerms` is now blocked even in academic (`commercial := false`) training!
#guard (checkAtlasResource
         { httpsOnly := true, noPrivateIp := true, spdxKnown := true,
           licenseClass := .customTerms, forTraining := true, commercial := false }).isSome == true

-- Academic training on explicit `.nonCommercial` remains valid, while commercial training is blocked:
#guard (checkAtlasResource
         { httpsOnly := true, noPrivateIp := true, spdxKnown := true,
           licenseClass := .nonCommercial, forTraining := true, commercial := false }).isNone == true

#guard (checkAtlasResource
         { httpsOnly := true, noPrivateIp := true, spdxKnown := true,
           licenseClass := .nonCommercial, forTraining := true, commercial := true }).isSome == true

-- Lineage taint propagation witness: `[WLP (.permissive), LAB-Bench (.evalOnly)]` taints MIT child:
#guard effectiveLicense [.permissive, .evalOnly] .permissive == .evalOnly
#guard effectiveLicense [.permissive, .nonCommercial] .permissive == .nonCommercial
#guard (LicenseClass.permissive.disj .nonCommercial) == .permissive

#guard (checkAtlasResource
         { httpsOnly := false, noPrivateIp := true, spdxKnown := true,
           licenseClass := .permissive, forTraining := false, commercial := false }).isSome == true

private def sampleHamiltonCard : McpCapabilityCard :=
  { hasTypedNumericBounds := true, forbidsExtraProps := true, requiresDeckEpoch := true,
    spdxKnown := true, licenseClass := .permissive,
    minVolTenthUL := 10, maxVolTenthUL := 10000, deadVolTenthUL := 150,
    minTempC := 40, maxTempC := 980, sealTempThreshC := 800 }

private def sampleCryoColdBlockCard : McpCapabilityCard :=
  { hasTypedNumericBounds := true, forbidsExtraProps := true, requiresDeckEpoch := true,
    spdxKnown := true, licenseClass := .permissive,
    minVolTenthUL := 5, maxVolTenthUL := 2000, deadVolTenthUL := 50,
    minTempC := -800, maxTempC := 250, sealTempThreshC := 200 }

#guard (checkMcpCardSpec sampleHamiltonCard).isNone == true
#guard (checkMcpCardSpec sampleCryoColdBlockCard).isNone == true
#guard (checkMcpCardSpec { sampleCryoColdBlockCard with minTempC := -2500 }).isSome == true

#guard (checkMcpCardSpec { sampleHamiltonCard with hasTypedNumericBounds := false }).isSome == true

#guard (checkMcpToolCall sampleHamiltonCard
         { tokenEpoch := 7, liveDeckEpoch := 7, volTenthUL := 500,
           srcWellVolTenthUL := 1000, dstWellVolTenthUL := 200, dstWellCapTenthUL := 2000,
           tempC := 370, plateSealed := false, hasUnknownExtraArgs := false,
           commercialContext := true }).isNone == true

-- Sub-zero `-20.0 C` (`-200` TenthC) enzyme transfer verified cleanly:
#guard (checkMcpToolCall sampleCryoColdBlockCard
         { tokenEpoch := 3, liveDeckEpoch := 3, volTenthUL := 100,
           srcWellVolTenthUL := 500, dstWellVolTenthUL := 50, dstWellCapTenthUL := 1000,
           tempC := -200, plateSealed := false, hasUnknownExtraArgs := false,
           commercialContext := true }).isNone == true

#guard (checkMcpToolCall sampleHamiltonCard
         { tokenEpoch := 6, liveDeckEpoch := 7, volTenthUL := 500,
           srcWellVolTenthUL := 1000, dstWellVolTenthUL := 200, dstWellCapTenthUL := 2000,
           tempC := 370, plateSealed := false, hasUnknownExtraArgs := false,
           commercialContext := true }).isSome == true

#guard (checkMcpToolCall sampleHamiltonCard
         { tokenEpoch := 7, liveDeckEpoch := 7, volTenthUL := 500,
           srcWellVolTenthUL := 600, dstWellVolTenthUL := 200, dstWellCapTenthUL := 2000,
           tempC := 370, plateSealed := false, hasUnknownExtraArgs := false,
           commercialContext := true }).isSome == true

end LabAtlasLean
