# Architecture and History — `lab-automation-atlas`

> **Auto-Lab Ecosystem Role**: Layer `L5 · Executive Planning, Procurement & Scheduling` in [Robot AI Auto-Lab (`auto-lab`)](https://github.com/yaniguan/auto-lab) ([Project Studio](https://yaniguan.github.io/auto-lab/)).

---

## 1. Object

### Problem Statement
Laboratory automation spans heterogeneous liquid handlers (`Opentrons`, `Hamilton`, `Tecan`, `Automata`, `Biosero`), cloud foundries (`Emerald Cloud Lab`, `Strateos`, `Ginkgo Bioworks`), intermediate representations and SDKs (`Opentrons Python API v2`, `PyLabRobot`, `Autoprotocol`, `LabOP`, `XDL`, `SiLA 2`), campaign/scheduling solvers (`Atlas`, `WEI`, `Bluesky`, `OR-Tools`), chemical synthesis/procurement databases (`ORD`, `USPTO`, `AiZynthFinder`, `RDKit`, `PubChem PUG REST`, `eLabFTW`), and protocol benchmarks (`WLP`, `BioPlanner`, `BioProBench`, `LAB-Bench`). Without a machine-readable registry carrying verified SPDX licenses, maintenance statuses, hardware compatibility, and benchmark-contamination flags, autonomous planning agents risk selecting archived/incompatible stacks or leaking `eval_only` benchmarks into training pipelines.

`lab-automation-atlas` is the **machine-readable semantic world map, SPDX license registry, and automated link auditor** for Layer `L5` of Auto-Lab.

### Role in the Auto-Lab `L0`–`L6` Hierarchy
- **Executive Planning & Procurement (`L5`)**: Supplies typed JSON/YAML queries (`lab-atlas list`, `lab-atlas compatibility`) to [`labshift`](https://github.com/yaniguan/labshift), [`buy-or-make`](https://github.com/yaniguan/buy-or-make), and [`lab-decide`](https://github.com/yaniguan/lab-decide).
- **Simulation & Default-Deny Verification (`L4`)**: Cross-indexes embodied robotics twins (`LabUtopia`, `AutoBio`, `MATTERIX`) in [`lab-rehearsal`](https://github.com/yaniguan/lab-rehearsal) and formal Lean 4 / SQL benchmarks (`Lean 4`, `miniF2F`, `Spider 2.0`) in [`lab-verify`](https://github.com/yaniguan/lab-verify).
- **Motor & Compiler Grounding (`L1` / `L3`)**: Maps target liquid handlers to open SDKs/simulators consumed by [`stepbot`](https://github.com/yaniguan/stepbot) and [`twinstep`](https://github.com/yaniguan/twinstep).
- **License-Gated Data Hub Alignment (`L2`)**: Harmonizes dataset SPDX expressions, `commercial_use_ok`, and `allowed_purposes` (`train_commercial` vs `eval_only`) with [`assayfold`](https://github.com/yaniguan/assayfold) and [`labbench-posttrain`](https://github.com/yaniguan/labbench-posttrain).

---

## 2. Data

### Canonical Catalog (`atlas.json` & `schema/atlas.schema.json`)
All `58` entries reside in [`atlas.json`](../atlas.json), governed by Draft 2020-12 JSON Schema [`schema/atlas.schema.json`](../schema/atlas.schema.json) (`additionalProperties: false`) and synchronized byte-for-byte with [`README.md`](../README.md) via `scripts/sync_catalog.py`:

| Category ID | Section Title | Entries | Key Governance Fields |
|---|---|---:|---|
| `autolab_sibling` | Related Auto-Lab repositories (`L6` to `L0`) | 20 | `layer` (`Hub`, `L6`..`L0`), `spdx_license` (`MIT`), `has_simulator` |
| `hardware` | Liquid handlers and lab robots | 5 | `supported_hardware`, `protocol_formats`, `has_simulator` |
| `cloud_lab` | Cloud labs and automated foundries | 4 | `maintenance_status` (`Strateos` flagged `commercial_restructured`) |
| `software` | Open-source lab automation software | 12 | `spdx_license`, `osi_approved` (non-OSI flagged), `maintenance_status` (`Aquarium` `archived`, `Autoprotocol` & `XDL generation` `legacy`) |
| `chemistry_and_procurement` | Chemical synthesis, reaction databases, and procurement | 6 | `ORD`, `USPTO`, `AiZynthFinder`, `RDKit`, `PubChem PUG REST`, `eLabFTW` |
| `dataset` | Open protocol sources and datasets | 6 | `spdx_license`, `commercial_use_ok`, `allowed_purposes`, `contamination_warning`, `huggingface_id`, `doi`, `record_count` |
| `simulation_and_verification` | Embodied simulation & formal verification (`L4` cross-refs) | 5 | Cross-references to `lab-rehearsal` and `lab-verify` |

---

## 3. Model

**No neural network or statistical estimator is trained in this repository.** Instead, `lab_atlas` provides three deterministic subsystems:

1. **Strict Schema Validator & Query Engine (`lab_atlas/catalog.py`)**:
   - Enforces `additionalProperties: false`, unique slugs, HTTPS-only URLs, enum invariants, and `eval_only` contamination warnings using only the Python standard library.
   - Computes the hardware-to-SDK-to-IR compatibility matrix (`build_compatibility_matrix`) and exports deterministic JSON/YAML.
2. **Synchronized Markdown Table Renderer (`lab_atlas/render.py`)**:
   - Generates uniform 6-column Markdown tables (`Name | Role / Type | Status | License | Commercial Use | Links`) across all 7 catalog categories plus the hardware compatibility table.
3. **SSRF-Hardened Concurrent Link Auditor (`lab_atlas/linkcheck.py`, `scripts/check_links.py`)**:
   - **Balanced Markdown Parser**: Strips fenced/inline code spans and parses inline links with nested balanced parentheses and optional link titles, reference-style definitions, `<https://...>` autolinks, and local file `#anchor` targets across `README.md` and `docs/**/*.md`.
   - **SSRF & Redirect Safety (`SafeRedirectHandler`)**: Rejects non-HTTPS schemes, `https -> http` downgrades, credentials, `localhost`/`.local` hostnames, and private/loopback/link-local/reserved IPs (both literal and DNS-resolved).
   - **Protocol & WAF Resilience**: Issues `HEAD` requests with `GET` fallback (`Range: bytes=0-16383`) on `400`/`403`/`405`/`501`, bounded exponential backoff on `429`/`502`/`503`/`504`, `ThreadPoolExecutor` concurrency with per-host semaphores, soft-404/root-redirect detection, and an explicit commercial-vendor-only WAF `403` allowlist.

---

## 4. Training & Verification

- **Zero Parametric Training**: Pure Python 3.10+ standard library runtime (`dependencies = []` in [`pyproject.toml`](../pyproject.toml)).
- **Continuous Verification (`.github/workflows/links.yml`)**:
  - Runs offline `pytest` unit tests and `python scripts/sync_catalog.py --check` on every `push`, `pull_request`, and `workflow_dispatch`.
  - Runs live concurrent link checks (`timeout-minutes: 10`, `permissions: contents: read`) on `push`, `pull_request`, `workflow_dispatch`, and weekly Mondays (`0 12 * * 1`), uploading `reports/link_status.json` as a workflow artifact and failing CI (`exit 1`) on broken links.

---

## 5. History

| Commit | Date | Author | Branch / Ref | Summary |
|---|---|---|---|---|
| `f2e2e83` | `2026-11-18` | Yani Guan | `main` | Initial commit: 5-section Markdown pointer map (`30` entries), sequential `scripts/check_links.py`, weekly `links.yml`, and `MIT` license. |
| `0.2.0` | `2026-11-23` | Yani Guan | `fix/resolve-audit-issues` | Resolved audit issues `#1..#22`: published 58-entry `atlas.json` + Draft 2020-12 `schema/atlas.schema.json`, packaged `lab-atlas` CLI, added SPDX/OSI/commercial/contamination metadata, hardware-to-SDK-to-IR compatibility matrix, chemistry & `L4` cross-references, SSRF-safe concurrent balanced-paren link checker with JSON reporting, hardened CI, and offline `pytest` suite. |

---

## 6. Unique Properties

1. **Single Source of Truth (`atlas.json` <-> `README.md`)**: Eliminates drift between programmatic JSON/YAML agent queries and human-readable Markdown tables.
2. **SPDX & Benchmark-Contamination Hygiene**: Aligns dataset licensing directly with `assayfold` while explicitly guarding `LAB-Bench`, `BioProBench`, and `BioPlanner` against training contamination.
3. **Zero-Dependency, Security-Hardened Link Auditing**: Combines balanced-parenthesis Markdown parsing, local heading-anchor verification, SSRF/downgrade redirect blocking, per-host concurrency limits, and explicit WAF `403` allowlisting in pure standard-library Python.
