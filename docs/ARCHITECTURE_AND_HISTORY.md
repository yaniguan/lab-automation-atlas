# Architecture and History — `lab-automation-atlas`

> **Auto-Lab Ecosystem Role**: Layer `L5 · Executive Planning, Procurement & Scheduling` in [Robot AI Auto-Lab (`auto-lab`)](https://github.com/yaniguan/auto-lab) ([Project Studio](https://yaniguan.github.io/auto-lab/)).

---

## 1. Object

### Problem Statement
Laboratory automation spans heterogeneous liquid handlers (`Opentrons`, `Hamilton`, `Tecan`, `Automata`, `Biosero`), cloud foundries (`Emerald Cloud Lab`, `Strateos`, `Ginkgo Bioworks`), intermediate representations and SDKs (`Opentrons Python API v2`, `PyLabRobot`, `Autoprotocol`, `LabOP`, `XDL`, `SiLA 2`), campaign/scheduling solvers (`Atlas`, `WEI`, `Bluesky`, `OR-Tools`), chemical synthesis/procurement databases (`ORD`, `USPTO`, `AiZynthFinder`, `RDKit`, `PubChem PUG REST`, `eLabFTW`), and multimodal wet-lab, self-driving formulation, spectroscopy, crystallography, acoustic, and embodied-manipulation datasets/benchmarks (`WLP`, `BioPlanner`, `BioProBench`, `LAB-Bench`, `FineBio`, `ChemBench`, `BixBench`, `MassSpecGym`, `MSD`, `AqSolDB`, `CALiSol-23`, `COD/ROD`, `OMat24`, `DCASE Task 2`, `DROID`). Without a machine-readable registry carrying verified SPDX licenses, maintenance statuses, hardware compatibility, analytical modalities, and benchmark-contamination flags, autonomous planning agents risk selecting archived/incompatible stacks or leaking `eval_only` benchmarks into training pipelines.

`lab-automation-atlas` is the **machine-readable semantic world map, SPDX license registry, and automated link auditor** for Layer `L5` of Auto-Lab.

### Role in the Auto-Lab `L0`–`L6` Hierarchy
- **Executive Planning & Procurement (`L5`)**: Supplies typed JSON/YAML queries (`lab-atlas list`, `lab-atlas compatibility`) to [`labshift`](https://github.com/yaniguan/labshift), [`buy-or-make`](https://github.com/yaniguan/buy-or-make), and [`lab-decide`](https://github.com/yaniguan/lab-decide).
- **Simulation, Verification & Post-Run Attribution (`L4`)**: Cross-indexes embodied robotics twins (`LabUtopia`, `AutoBio`, `MATTERIX`) in [`lab-rehearsal`](https://github.com/yaniguan/lab-rehearsal), formal Lean 4 / SQL benchmarks (`Lean 4`, `miniF2F`, `Spider 2.0`) in [`lab-verify`](https://github.com/yaniguan/lab-verify), and post-execution causal blame / NNLS XRD deconvolution in [`lab-attrib`](https://github.com/yaniguan/lab-attrib).
- **Motor & Compiler Grounding (`L1` / `L3`)**: Maps target liquid handlers to open SDKs/simulators consumed by [`stepbot`](https://github.com/yaniguan/stepbot) and [`twinstep`](https://github.com/yaniguan/twinstep).
- **License-Gated Data Hub Alignment (`L2`)**: Harmonizes dataset SPDX expressions, `commercial_use_ok`, and `allowed_purposes` (`train_commercial` vs `eval_only`) with [`assayfold`](https://github.com/yaniguan/assayfold) and [`labbench-posttrain`](https://github.com/yaniguan/labbench-posttrain).

---

## 2. Data

### Canonical Catalog (`atlas.json` & `schema/atlas.schema.json`)
All `84` entries reside in [`atlas.json`](../atlas.json), governed by Draft 2020-12 JSON Schema [`schema/atlas.schema.json`](../schema/atlas.schema.json) (`additionalProperties: false`) and synchronized byte-for-byte with [`README.md`](../README.md) via `scripts/sync_catalog.py`:

| Category ID | Section Title | Entries | Key Governance Fields |
|---|---|---:|---|
| `autolab_sibling` | Related Auto-Lab repositories (`L6` to `L0`) | 21 | `layer` (`Hub`, `L6`..`L0`), `spdx_license` (`MIT`, `Apache-2.0`), `has_simulator` |
| `hardware` | Liquid handlers and lab robots | 5 | `supported_hardware`, `protocol_formats`, `has_simulator` |
| `cloud_lab` | Cloud labs and automated foundries | 4 | `maintenance_status` (`Strateos` flagged `commercial_restructured`) |
| `software` | Open-source lab automation software | 14 | `spdx_license`, `osi_approved` (non-OSI flagged), `maintenance_status` (`Aquarium` `archived`, `Autoprotocol` & `XDL generation` `legacy`, `PyJobShop` & `HuggingFace LeRobot` `active`) |
| `chemistry_and_procurement` | Chemical synthesis, reaction databases, and procurement | 6 | `ORD`, `USPTO`, `AiZynthFinder`, `RDKit`, `PubChem PUG REST`, `eLabFTW` |
| `dataset` | Open protocol sources and datasets | 29 | `spdx_license`, `commercial_use_ok`, `allowed_purposes`, `contamination_warning`, `analytical_modalities`, `huggingface_id`, `doi`, `record_count` |
| `simulation_and_verification` | Embodied simulation & formal verification (`L4` cross-refs) | 5 | Cross-references to `lab-rehearsal` and `lab-verify` |

---

## 3. Model

**No neural network or statistical estimator is trained in this repository.** Instead, `lab_atlas` provides three deterministic subsystems:

1. **Strict Schema Validator & Query Engine (`lab_atlas/catalog.py`)**:
   - Enforces `additionalProperties: false`, unique slugs, HTTPS-only SSRF-safe URLs, real calendar dates (`datetime.date.fromisoformat`), license-to-purpose consistency (`train_commercial` requires `commercial_train_ok`; `train_academic` requires `academic_train_ok`; `commercial_use_ok: true` rejected for `non_commercial`, `custom_terms`, and `eval_only` SPDX classes on `dataset` and `chemistry_and_procurement` entries), upstream-only `license_evidence` (rejecting generic Creative Commons / SPDX / OSI deeds and bare `arxiv.org/abs/` pages on dataset entries), and `eval_only` contamination warnings.
   - Computes the hardware-to-SDK-to-IR compatibility matrix (`build_compatibility_matrix`) and exports deterministic JSON/YAML.
2. **Synchronized Markdown Table Renderer (`lab_atlas/render.py`)**:
   - Generates uniform 6-column Markdown tables (`Name | Role / Type | Status | License | Commercial Use | Links`) across all 7 catalog categories plus the hardware compatibility table.
3. **SSRF-Hardened Concurrent Link & Upstream License Auditors (`lab_atlas/linkcheck.py`, `scripts/check_links.py`, `scripts/check_licenses.py`)**:
   - **Balanced Markdown Parser**: Strips fenced/inline code spans and parses inline links with nested balanced parentheses and optional link titles, reference-style definitions, `<https://...>` autolinks, and local file `#anchor` targets across `README.md` and `docs/**/*.md`.
   - **SSRF & Redirect Safety (`SafeRedirectHandler`)**: Rejects non-HTTPS schemes, `https -> http` downgrades, credentials, `localhost`/`.local` hostnames, and private/loopback/link-local/reserved IPs (both literal and DNS-resolved).
   - **Protocol, WAF & License Resilience**: Issues `HEAD` requests with `GET` fallback (`Range: bytes=0-16383`) on `400`/`403`/`405`/`501`, bounded exponential backoff on `429`/`502`/`503`/`504`, `ThreadPoolExecutor` concurrency with per-host semaphores, soft-404/root-redirect detection, vendor-only WAF `403` allowlisting, and weekly scheduled SPDX cross-verification against Hugging Face `cardData.license`, GitHub's license API, Zenodo `metadata.license`, and Harvard Dataverse (`scripts/check_licenses.py`).

---

## 4. Training & Verification

- **Zero Parametric Training**: Pure Python 3.10+ standard library runtime (`dependencies = []` in [`pyproject.toml`](../pyproject.toml); `pytest`, `jsonschema`, and `license-expression` in `.[dev]`).
- **Continuous Verification (`.github/workflows/links.yml`)**:
  - Runs Lean `v4.36.0` (`lake build`) on [`lean/LabAtlasLean.lean`](../lean/LabAtlasLean.lean) and the auto-generated [`lean/LabAtlasLean/Parity.lean`](../lean/LabAtlasLean/Parity.lean) (`260` `#guard` assertions generated by [`scripts/gen_lean_parity.py`](../scripts/gen_lean_parity.py): `160` `AtlasResource` states + `25` `conj` + `25` `disj` + `50` `checkMcpToolCall` benchmark calls), followed by [`scripts/verify_lean_parity.py`](../scripts/verify_lean_parity.py) auditing `#print axioms` across all `48` theorems (`no custom axioms`; strictly `propext`, `Classical.choice`, `Quot.sound`). **Scope of Lean parity**: Lean formally models and checks the boolean resource policy, the 5-element license lattice, lineage DAG taint, and the fixed-point MCP capability-card checker only — URL canonicalization (`lab_atlas/urlmatch.py`) and SPDX string parsing/classification (`lab_atlas/spdx.py`) are implemented and verified in Python.
  - Runs offline `pytest` unit tests, `python scripts/sync_catalog.py --check`, and `python scripts/gen_lean_parity.py --check` on every `push`, `pull_request`, and `workflow_dispatch`.
  - Runs live concurrent link checks (`timeout-minutes: 10`, `permissions: contents: read`) on `push`, `pull_request`, `workflow_dispatch`, and weekly Mondays (`0 12 * * 1`), plus weekly scheduled upstream license checks (`scripts/check_licenses.py --json-out reports/license_status.json`).

---

## 5. History

| Commit | Date | Author | Branch / Ref | Summary |
|---|---|---|---|---|
| `f2e2e83` | `2026-11-18` | Yani Guan | `main` | Initial commit: 5-section Markdown pointer map (`30` entries), sequential `scripts/check_links.py`, weekly `links.yml`, and `MIT` license. |
| `0.2.0` | `2026-11-23` | Yani Guan | `fix/resolve-audit-issues` | Resolved audit issues `#1..#22`: published 58-entry `atlas.json` + Draft 2020-12 `schema/atlas.schema.json`, packaged `lab-atlas` CLI, added SPDX/OSI/commercial/contamination metadata, hardware-to-SDK-to-IR compatibility matrix, chemistry & `L4` cross-references, SSRF-safe concurrent balanced-paren link checker with JSON reporting, hardened CI, and offline `pytest` suite. |
| `cab4852` | `2026-11-25` | Yani Guan | `fix/phase2-audit-and-wire` | Resolved Phase-2 audit issues `#24..#29`: added `LabAtlasLean` SPDX 2.3/3.0 bounded lattice + lineage taint proofs, stdlib compound SPDX AST parser (`lab_atlas/spdx.py`), typed `hardware_capabilities` & `analytical_modalities`, pinned-IP SSRF redirect validation, and dynamic `autolab_wire.py` (`autolab-wire/v1`) node. |
| `0.3.0` | `2026-11-25` | Yani Guan | `feat/open-datasets-2026` | Expanded `dataset` registry from `6` to `17` verified entries (`70` total) covering 2024-2026 open wet-lab atomic actions (`FineBio`), chemistry/bio benchmarks (`ChemBench`, `BixBench`), MS/MS & multimodal NMR/FTIR spectroscopy (`MassSpecGym`, `MSD`), solubility & electrolyte formulation (`AqSolDB`, `CALiSol-23`), open XRD/Raman crystallography (`COD/ROD`, `OMat24`), machine audio (`DCASE Task 2`), and robot manipulation (`DROID`). |
| `b6455d9` | `2026-11-27` | Yani Guan | `feat/frontier-84-entries-and-lean-ci` | Expanded catalog from `70` to `84` entries (`12` frontier chemistry/XRD/SQL/Lean-4/drift/transparent-depth datasets & benchmarks + `PyJobShop` & `HuggingFace LeRobot`), hardened fail-closed `autolab_wire.py` input validation, and added live Lean 4.36.0 `#print axioms` + 335-case `#eval` differential parity CI. |
| `0.4.0` | `2026-11-27` | Yani Guan | `fix/audit-33-36-url-spdx-lean-guards` | Resolved audit issues `#33..#36`: unified URL canonicalization (`lab_atlas/urlmatch.py`) and default-deny missing `license_class` on `autolab_wire.py`; license-to-purpose/commercial validation, strengthened Draft 2020-12 JSON Schema & 25-mutation differential suite; upstream-verified licenses (`AqSolDB` `CC0-1.0`, `CALiSol-23` & `MATTERIX` `NOASSERTION`, `Spider 2.0` `MIT`), banned generic deed `license_evidence`, trimmed sibling roles, added `scripts/check_licenses.py`; and added `260` compiled `#guard` parity checks (`lean/LabAtlasLean/Parity.lean`). |

---

## 6. Unique Properties

1. **Single Source of Truth (`atlas.json` <-> `README.md`)**: Eliminates drift between programmatic JSON/YAML agent queries and human-readable Markdown tables.
2. **SPDX & Benchmark-Contamination Hygiene**: Aligns dataset licensing directly with `assayfold` and `LabAtlasLean` while explicitly guarding `LAB-Bench`, `BixBench`, `ChemBench`, `FineBio`, `BioProBench`, `BioPlanner`, `CALiSol-23`, `EHRSQL-2024`, `Spider 2.0`, `PutnamBench`, and `AutoBio` against training contamination across equivalent URL aliases.
3. **Zero-Dependency, Security-Hardened Link Auditing**: Combines balanced-parenthesis Markdown parsing, local heading-anchor verification, SSRF/downgrade redirect blocking, per-host concurrency limits, and explicit WAF `403` allowlisting in pure standard-library Python.

---

## 7. 15-Repository Auto-Lab Wire Contract (`autolab-wire/v1`)

[`autolab_wire.py`](../autolab_wire.py) (`REPO_ID = "lab-automation-atlas"`, `LAYER = "L5"`) implements the standardized `process_packet(packet: dict) -> dict` contract connecting `lab-automation-atlas` into the 15-repository closed-loop Auto-Lab wire:

- **Path & State Hygiene**: Resolves [`atlas.json`](../atlas.json) strictly via `REPO_DIR = Path(__file__).resolve().parent`, deep-copies incoming packets, initializes `autolab-wire/v1` defaults, and passes already-halted packets (`halted=True`) through unchanged.
- **15-Repository Pipeline Topology**:
  - **Upstream (`L2` / `L6`)**: Receives protocol/assay packets from [`assayfold`](https://github.com/yaniguan/assayfold), [`lab-ears`](https://github.com/yaniguan/lab-ears), [`lab-ask-why`](https://github.com/yaniguan/lab-ask-why), and [`lab-decide`](https://github.com/yaniguan/lab-decide).
  - **Peer & Downstream (`L5` -> `L4` -> `L1`/`L0` -> `L4` -> `L3`)**: Dynamically resolves `platform_grounding` per `target_platform` from `atlas.json` `hardware_capabilities` (e.g., `opentrons_ot2` -> `api_level: "2.16"`, `max_deck_slots: 11`; `opentrons_flex` -> `api_level: "2.20"`, `max_deck_slots: 12`, `staging_slots: 4`; `hamilton_star` -> `api_level: "VENUS-6"`, `deck_architecture: "carrier_rails"`; `chemputer` -> `api_level: "XDL-2.0"`, `deck_architecture: "flow_batch_reactor"`; default-deny `L5_ATLAS_UNKNOWN_PLATFORM` on unrecognized platforms) and routes `analytical_modalities` (`XRD`, `Raman`, `NMR`, `LC-MS`, `UV-Vis`, `FTIR`) to [`buy-or-make`](https://github.com/yaniguan/buy-or-make), [`labshift`](https://github.com/yaniguan/labshift), [`lab-rehearsal`](https://github.com/yaniguan/lab-rehearsal), [`lab-verify`](https://github.com/yaniguan/lab-verify), [`stepbot`](https://github.com/yaniguan/stepbot), [`lab-hands`](https://github.com/yaniguan/lab-hands), [`lab-feet`](https://github.com/yaniguan/lab-feet), [`lab-attrib`](https://github.com/yaniguan/lab-attrib), [`twinstep`](https://github.com/yaniguan/twinstep), [`labfill`](https://github.com/yaniguan/labfill), and [`labbench-posttrain`](https://github.com/yaniguan/labbench-posttrain).
- **Canonical URL Matching, Default-Deny SPDX Gate & Lean Parity Scope (`eval_only_blocked_from_training`)**:
  - Validates `resource_url` against `lab_atlas.linkcheck.validate_url_target` (canonical HTTPS-only public host, blocking octal/hex/integer IPv4 and IPv6 transition SSRF targets).
  - Canonicalizes both catalog links and `resource_url` via `lab_atlas.urlmatch.canonicalize_url_for_match` (host lower-casing, `www.` stripping, `hf.co -> huggingface.co`, case-insensitive GitHub/Hugging Face `<owner>/<repo>` + `.git` stripping, `raw.githubusercontent.com/<owner>/<repo>/... -> github.com/<owner>/<repo>`, `huggingface.co/api/datasets/<id>/...` and `datasets-server.huggingface.co/...?dataset=<id> -> huggingface.co/datasets/<id>`, and arXiv `/pdf/<id>(.pdf)` / `/abs/<id>vN` / `/pdf/<id>vN(.pdf) -> arxiv.org/abs/<id>`).
  - Enforces default-deny when `license_class` is omitted: resolves `spdx_license` from the matched catalog entry (so empty `{}` packets resolve to `stepbot`'s `MIT` record), and halts unknown URLs lacking `license_class` with `halt_reason="L5_ATLAS_LICENSE_OR_URL_BLOCK"` and rule `explicit_spdx_license`.
  - Evaluates compound SPDX 2.3/3.0 expressions (`AND`, `OR`, `WITH`) and `parent_licenses` lineage taint via `lab_atlas.spdx`, then evaluates the boolean resource policy verified against `lean/LabAtlasLean.lean` (`lean/LabAtlasLean/Parity.lean`; Lean covers the boolean policy, license lattice, and fixed-point MCP card checker only, not URL canonicalization or SPDX string parsing).

