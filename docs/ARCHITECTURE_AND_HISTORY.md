# Architecture and History — `lab-automation-atlas`

> **Auto-Lab Ecosystem Role**: Layer `L5 · Executive Planning, Procurement & Scheduling` in [Robot AI Auto-Lab (`auto-lab`)](https://github.com/yaniguan/auto-lab) ([Project Studio](https://yaniguan.github.io/auto-lab/)).

---

## 1. Object

### Problem Statement
Laboratory automation spans fragmented hardware vendors, cloud foundries, protocol intermediate representations (`Opentrons Python API v2`, `PyLabRobot`, `Autoprotocol`, `LabOP`, `XDL`, `SiLA 2`), orchestration engines (`WEI`, `Bluesky`, `Atlas`, `OR-Tools`), and open protocol corpora (`protocols.io`, `Bio-protocol`, `WLP`, `BioPlanner`, `BioProBench`, `LAB-Bench`), each governed by distinct licensing and terms-of-use constraints. Without a verified, neutral ecosystem registry, executive planning agents risk hallucinating dead endpoints, selecting incompatible protocol compilers for target liquid handlers, or ingesting non-commercial benchmark corpora into commercial pipelines.

`lab-automation-atlas` serves as the **curated, zero-copy semantic world map and pointer registry** of automated-lab platforms, open-source automation software, and open protocol datasets, backed by automated URL reachability checks (`scripts/check_links.py` and `.github/workflows/links.yml`).

### Role in the Auto-Lab `L0`–`L6` Hierarchy
Within the [Auto-Lab](https://github.com/yaniguan/auto-lab) Brain/Body architecture (`L0`–`L6`), `lab-automation-atlas` sits in **`L5 · Executive Planning, Procurement & Scheduling`**:
- **Tool & Target Selection (`L5`)**: Grounds platform, compiler, solver, and benchmark discovery for sibling `L5` planning and scheduling packages—explicitly cross-referencing [`labshift`](https://github.com/yaniguan/labshift) (`OR-Tools` CP-SAT multi-instrument scheduling), [`buy-or-make`](https://github.com/yaniguan/buy-or-make) (retrosynthetic & vendor procurement triage), and [`lab-decide`](https://github.com/yaniguan/lab-decide) (Bayesian optimization & conformal trust regions, complementary to `Atlas`).
- **Compiler & Verification Grounding (`L4` / `L2`)**: Maps the hardware-to-software boundary connecting [`stepbot`](https://github.com/yaniguan/stepbot) (`Opentrons Python API v2`), [`twinstep`](https://github.com/yaniguan/twinstep) (seeded protocol error twins), and [`lab-rehearsal`](https://github.com/yaniguan/lab-rehearsal) (`PyLabRobot` / `Opentrons` deck simulation).
- **Data Hub Alignment (`L0`)**: Indexes upstream protocol repositories (`protocols.io`, `WLP`, `BioProBench`, `LAB-Bench`) whose license-gated ingestion and unified schema conversion are implemented in [`assayfold`](https://github.com/yaniguan/assayfold).

### Inputs, Outputs, and Scope Boundaries
- **Inputs**:
  - Curated Markdown catalog tables in `README.md` (checked on `2026-11-18`).
- **Outputs**:
  - Human- and agent-readable domain taxonomy across 5 structured tables (`30` named tools, platforms, and datasets; `39` unique external HTTPS URLs in the initial catalog).
  - HTTP status audit log from `python scripts/check_links.py` (`<code> <url>` per link plus summary `<N> links, <M> not reachable`).
- **Scope Boundaries**:
  - Strictly a **pointer registry**: copies zero external datasets, ranks zero commercial vendors, claims zero partnerships, and delegates license enforcement to downstream data pipelines (`assayfold`, `buy-or-make`).

---

## 2. Data

### Curated Catalog Structure (`README.md`)
All entries were manually opened and verified on `2026-11-18` across five domain tables:

| Section | Entries | Representative Targets | Metadata Columns |
|---|---:|---|---|
| **Related tools in this account** | 3 | `twinstep`, `labshift`, `stepbot` | `Repo`, `What it does` |
| **Liquid handlers and lab robots** | 5 | `Opentrons` (OT-2, Flex), `Hamilton`, `Tecan`, `Automata`, `Biosero` | `Name`, `Type`, `Link` |
| **Cloud labs and automated foundries** | 4 | `Emerald Cloud Lab`, `Strateos`, `Ginkgo Bioworks`, `Acceleration Consortium` | `Name`, `Type`, `Link` |
| **Open-source lab automation software** | 12 | `Opentrons Python API v2`, `PyLabRobot`, `Autoprotocol`, `LabOP`, `SiLA 2`, `Aquarium`, `XDL (Chemputer)`, `XDL generation`, `Atlas`, `WEI`, `Bluesky`, `OR-Tools` | `Name`, `What it is`, `Link` |
| **Open protocol sources and datasets** | 6 | `protocols.io`, `Bio-protocol`, `Wet Lab Protocols (WLP)`, `BioPlanner (BioProt)`, `BioProBench`, `LAB-Bench` | `Name`, `What it is`, `License note`, `Link` |

### Provenance and Zero-Copy License Posture
- **Zero Data Redistribution**: No third-party protocol text, benchmark splits, or vendor manuals are stored in this repository.
- **License Annotations**: The repository text itself is `MIT`-licensed (`LICENSE`). Protocol dataset entries carry explicit license warnings—highlighting per-item terms (`protocols.io`, `Bio-protocol`), permissive/ShareAlike repos (`WLP` MIT, `LAB-Bench` CC-BY-SA-4.0), and non-commercial restrictions (`BioProBench` non-commercial).

---

## 3. Model

**No neural network, statistical estimator, or learned model is trained or executed inside this pointer-atlas repository.** Instead, `lab-automation-atlas` implements two lightweight deterministic representations:

1. **Five-Faceted Lab-Automation Ontology (`README.md`)**:
   - Partitions the automated laboratory stack into: *(i)* local Auto-Lab companion tools, *(ii)* physical benchtop liquid handlers & orchestrators, *(iii)* remote cloud labs & self-driving foundries, *(iv)* open-source protocol/driver/scheduling software (`IR`s, hardware SDKs, workflow engines, combinatorial solvers), and *(v)* open wet-lab protocol corpora & QA benchmarks.
2. **Regex + HTTP Link-Health Verifier (`scripts/check_links.py`)**:
   - Extracts unique Markdown hyperlink targets via `re.findall(r"\]\((https?://[^)]+)\)", ...)`.
   - Issues sequential HTTP requests (`urllib.request.Request(..., headers={"User-Agent": "Mozilla/5.0"})`, `timeout=20`) and classifies each URL as reachable when `code in {200, 403}` (accounting for vendor WAFs that return `403` to scripted `urllib` clients while serving normal browser fetches).

---

## 4. Training

- **Zero Training / Zero Parameters**: Contains no trainable weights, optimization loops, or external Python package dependencies (uses Python 3.12 standard library `re`, `sys`, `urllib.request`).
- **Scheduled Link-Rot Monitoring (`.github/workflows/links.yml`)**: Maintained continuously via a GitHub Actions workflow triggered on `push` and on a weekly cron schedule (`0 12 * * 1`, Mondays at 12:00 UTC) running `python scripts/check_links.py` on `ubuntu-latest`.

---

## 5. History

| Commit | Date | Author | Branch / Ref | Summary |
|---|---|---|---|---|
| `f2e2e83` (`f2e2e83c0003e3ffd2376112ac05196b66c6285d`) | `2026-11-18` | Yani Guan | `main` | Initial commit (`Initial version`): published the 5-section curated map of liquid-handling robots, cloud labs, open-source lab automation software, and open protocol datasets (`README.md`, verified `2026-11-18`), along with `scripts/check_links.py`, weekly link-check CI (`.github/workflows/links.yml`), and `MIT` license. |

---

## 6. Unique Properties

1. **Strict Zero-Copy, Vendor-Neutral Pointer Architecture**: Separates ecosystem discovery from data storage—providing verified entry points without redistributing third-party datasets, ranking commercial hardware vendors, or implying commercial endorsement.
2. **End-to-End Coverage of Hardware, Protocol IRs, Solvers, and Benchmarks**: Bridges physical actuation (`Opentrons`, `Hamilton`, `Tecan`), intermediate representations (`Autoprotocol`, `LabOP`, `XDL`, `SiLA 2`), scheduling/optimization (`OR-Tools`, `Atlas`, `WEI`, `Bluesky`), and protocol benchmarks (`WLP`, `BioPlanner`, `BioProBench`, `LAB-Bench`) in one concise reference.
3. **Automated Weekly Link Auditing**: Pairs manual initial verification (`2026-11-18`) with scheduled weekly CI sweeps (`.github/workflows/links.yml`) using zero third-party dependencies.
4. **Auto-Lab Sibling Contracts**:
   - Directly indexes [`twinstep`](https://github.com/yaniguan/twinstep), [`labshift`](https://github.com/yaniguan/labshift), and [`stepbot`](https://github.com/yaniguan/stepbot), and complements [`assayfold`](https://github.com/yaniguan/assayfold) (which operationalizes `WLP`, `BioProBench`, `LAB-Bench`, and `protocols.io` into license-gated unified JSONL/Parquet records) and [`buy-or-make`](https://github.com/yaniguan/buy-or-make) (which maps the chemical vendor and retrosynthesis ecosystem).
