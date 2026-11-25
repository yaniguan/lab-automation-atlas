# lab-automation-atlas

A machine-readable and human-curated map of automated-lab hardware platforms, cloud foundries, open-source protocol SDKs/IRs, chemical synthesis & procurement databases, open wet-lab protocol benchmarks, and `L4` simulation/verification cross-references.

> **Auto-Lab Ecosystem**: Layer `L5 · Executive Planning, Procurement & Scheduling` in [auto-lab](https://github.com/yaniguan/auto-lab) · [Project Studio](https://yaniguan.github.io/auto-lab/)

This repository is strictly a zero-copy pointer and governance registry. It does not redistribute third-party datasets, rank commercial vendors, or imply partnerships. Always verify upstream licenses before integrating code or datasets.

## Quickstart & CLI (`lab-atlas`)

`lab-automation-atlas` ships a zero-dependency Python 3.10+ package (`lab_atlas`) backed by [`atlas.json`](atlas.json) and [`schema/atlas.schema.json`](schema/atlas.schema.json):

```bash
pip install -e ".[dev]"

# Query catalog entries programmatically
lab-atlas list --category software --commercial-ok --osi-only
lab-atlas list --category dataset --purpose train_commercial --json
lab-atlas compatibility
lab-atlas inspect bioprobench --json

# Export YAML or validate schema + README table synchronization
lab-atlas export --format yaml
python scripts/sync_catalog.py --check

# Run offline Markdown/SSRF/local-path checks and unit tests
python scripts/check_links.py --offline
pytest
```

## System Profile: Object · Data · Model · Training · History · Unique Properties

Full architectural documentation, schema invariants, link-checker security controls, and sibling contracts are maintained in [`docs/ARCHITECTURE_AND_HISTORY.md`](docs/ARCHITECTURE_AND_HISTORY.md):

- **Object**: Canonical semantic world map, SPDX license gate, and hardware-to-SDK-to-IR compatibility registry (`L5`) grounding platform, compiler, solver, procurement, and dataset selection across the Auto-Lab stack.
- **Data**: `59` typed entries across `7` catalog categories stored in [`atlas.json`](atlas.json) (`additionalProperties: false` in [`schema/atlas.schema.json`](schema/atlas.schema.json)) and rendered deterministically into standardized 6-column Markdown tables in `README.md`.
- **Model**: Typed ontology + hardware/IR compatibility resolver (`lab_atlas/catalog.py`) paired with a concurrent, SSRF-hardened Markdown link auditor (`lab_atlas/linkcheck.py`, `scripts/check_links.py`); **no parametric model is trained in this repository**.
- **Training**: Zero parametric training; continuously verified via offline `pytest` schema/parser tests and scheduled/PR GitHub Actions link-rot audits (`.github/workflows/links.yml`).
- **History**: Initialized in `f2e2e83` (`2026-11-18`) and expanded with [`atlas.json`](atlas.json), [`schema/atlas.schema.json`](schema/atlas.schema.json), `lab-atlas` CLI, hardware-to-SDK-to-IR matrix, chemistry/procurement & `L4` bridges, and hardened concurrent link verification.
- **Unique Properties**: Byte-for-byte `atlas.json` <-> `README.md` synchronization, `assayfold`-harmonized SPDX & `commercial_use_ok` flags, explicit `eval_only` benchmark-contamination guards (`LAB-Bench`, `BioProBench`, `BioPlanner`), maintenance status tracking (`archived`, `legacy`, `commercial_restructured`), and explicit vendor WAF `403` allowlisting.

## Repository Layout

```text
lab-automation-atlas/
├── .github/workflows/
│   └── links.yml                         # Offline pytest + schema sync + concurrent link-health CI
├── docs/
│   └── ARCHITECTURE_AND_HISTORY.md       # Deep technical profile (Object, Data, Model, History)
├── lab_atlas/
│   ├── __init__.py                       # Public Python API exports
│   ├── catalog.py                        # Loader, stdlib schema validator, filters & YAML exporter
│   ├── cli.py                            # `lab-atlas` CLI (list, inspect, compatibility, validate, ...)
│   ├── linkcheck.py                      # Balanced-paren parser, pinned SSRF/HTTPS guard & ThreadPool auditor
│   ├── render.py                         # Deterministic Markdown table & compatibility matrix renderer
│   ├── spdx.py                           # SPDX 2.3/3.0 expression parser & default-deny license lattice
│   └── resources/                        # Packaged copies of atlas.json and atlas.schema.json
├── lean/
│   └── LabAtlasLean.lean                 # Lean 4.36.0 license lattice, lineage taint & MCP envelope proofs
├── schema/
│   └── atlas.schema.json                 # Draft 2020-12 JSON Schema (additionalProperties: false)
├── scripts/
│   ├── check_links.py                    # Concurrent Markdown URL & local-anchor auditor CLI
│   └── sync_catalog.py                   # Validates atlas.json and syncs README.md & package resources
├── tests/                                # Offline pytest suite (link parser, SSRF, catalog, CLI)
├── atlas.json                            # Canonical 59-entry machine-readable catalog
├── autolab_wire.py                       # Auto-Lab 15-repo L5 wire node (autolab-wire/v1)
├── LICENSE                               # MIT License
├── pyproject.toml                        # Zero-dependency package & `lab-atlas` console script
└── README.md                             # Synchronized 7-section ecosystem map & compatibility matrix
```

<!-- BEGIN GENERATED CATALOG -->

## Related Auto-Lab repositories (`L6` to `L0`)

Complete internal navigation map across the 7-layer Auto-Lab Brain/Body stack and companion organs in `@yaniguan`.

| Name | Role / Type | Status | License | Commercial Use | Links |
|---|---|---|---|---|---|
| **auto-lab** (`Hub`) | 7-layer embodied brain, default-deny safety harness, and closed-loop orchestrator hub. | `active` | [`MIT`](https://github.com/yaniguan/auto-lab/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/auto-lab), [Studio](https://yaniguan.github.io/auto-lab/) |
| **lab-ask-why** (`L6`) | Socratic metacognitive co-scientist retrieving opposing scientific evidence (SUPPORT vs CONTRADICT). | `active` | [`MIT`](https://github.com/yaniguan/lab-ask-why/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/lab-ask-why) |
| **lab-decide** (`L6`) | Split-conformal molecular property decision API with calibrated abstention trust regions. | `active` | [`MIT`](https://github.com/yaniguan/lab-decide/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/lab-decide) |
| **YLM** (`L6`) | SE(3)-equivariant 3D molecular + language reasoner and home of formal Lean 4 LabLean. | `active` | [`MIT`](https://github.com/yaniguan/YLM/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/YLM), [Studio](https://yaniguan.github.io/YLM/) |
| **buy-or-make** (`L5`) | Make-vs-buy molecular procurement triage with conservative listed-catalog USD/g leaf lower bounds. | `active` | [`MIT`](https://github.com/yaniguan/buy-or-make/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/buy-or-make) |
| **labshift** (`L5`) | Multi-instrument time-window lab scheduler comparing greedy vs OR-Tools CP-SAT makespan solvers. | `active` | [`MIT`](https://github.com/yaniguan/labshift/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/labshift) |
| **lab-automation-atlas** (`L5`) | Machine-readable semantic map, SPDX license registry, and link auditor for automated-lab ecosystems. | `active` | [`MIT`](https://github.com/yaniguan/lab-automation-atlas/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/lab-automation-atlas) |
| **lab-rehearsal** (`L4`) | Episodic recall and 96-well digital-twin dry-run safety gate blocking liquid-handling fault classes. | `active` | [`MIT`](https://github.com/yaniguan/lab-rehearsal/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/lab-rehearsal) |
| **lab-verify** (`L4`) | Default-deny 4-layer SQL, Lean 4, and symbolic protocol verification gate. | `active` | [`MIT`](https://github.com/yaniguan/lab-verify/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/lab-verify) |
| **lab-attrib** (`L4`) | Post-execution causal blame gate, NNLS XRD precursor deconvolution, EVOI orthogonal routing, and SHA-256 certified memory ledger. | `active` | [`MIT`](https://github.com/yaniguan/lab-attrib/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/lab-attrib) |
| **WignerFlow** (`L4`) | 50-fs integrator-free equivariant molecular dynamics and physics surrogate gate for YLM. | `active` | [`MIT`](https://github.com/yaniguan/WignerFlow/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/WignerFlow), [Studio](https://yaniguan.github.io/WignerFlow/) |
| **labbench-posttrain** (`L3`) | Verifiable RL post-training SDK (SFT, DPO/MPO/TROPD, PPO/GRPO/GDPO+DAPO) with anti-reward-hack gates. | `active` | [`MIT`](https://github.com/yaniguan/labbench-posttrain/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/labbench-posttrain) |
| **twinstep** (`L3`) | Deterministic seeded-error protocol twin generator and topological step-ordering benchmark. | `active` | [`MIT`](https://github.com/yaniguan/twinstep/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/twinstep) |
| **labfill** (`L3`) | Batched protocol checking and sequence-packed bf16 GPU training throughput harness. | `active` | [`MIT`](https://github.com/yaniguan/labfill/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/labfill) |
| **lab-ears** (`L2`) | Wet-lab protocol span parser and benchtop acoustic machine-anomaly monitor. | `active` | [`MIT`](https://github.com/yaniguan/lab-ears/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/lab-ears) |
| **assayfold** (`L2`) | SHA-256-sealed, UCUM-normalized, SPDX-license-gated ingestion hub across 12 open lab datasets. | `active` | [`MIT`](https://github.com/yaniguan/assayfold/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/assayfold) |
| **ouroboros-ocsr** (`L2`) | SE(2)-equivariant optical chemical structure recognition bridging 2D figures to 3D conformers. | `active` | [`MIT`](https://github.com/yaniguan/ouroboros-ocsr/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/ouroboros-ocsr), [Studio](https://yaniguan.github.io/ouroboros-ocsr/) |
| **stepbot** (`L1`) | Deterministic YAML/JSON-to-Opentrons Python API v2 compiler with static volume/tip checks and simulator. | `active` | [`MIT`](https://github.com/yaniguan/stepbot/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/stepbot) |
| **lab-hands** (`L1`) | Collision-free SBS 96-well RRT motion planner with path shortcutting and last-cm tactile control. | `active` | [`MIT`](https://github.com/yaniguan/lab-hands/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/lab-hands) |
| **lab-feet** (`L0`) | Edge knowledge distillation and int8 / packed 4-bit quantized runtime for benchtop boards. | `active` | [`MIT`](https://github.com/yaniguan/lab-feet/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/lab-feet) |
| **equivariant-gpu-lab** (`L0`) | Fused GPU/CPU tensor-product and spherical-harmonic kernel benchmarks for equivariant models. | `active` | [`MIT`](https://github.com/yaniguan/equivariant-gpu-lab/blob/main/LICENSE) | yes | [GitHub](https://github.com/yaniguan/equivariant-gpu-lab) |

## Liquid handlers and lab robots

Benchtop pipetting robots, high-throughput liquid handlers, and multi-instrument workcell orchestrators.

| Name | Role / Type | Status | License | Commercial Use | Links |
|---|---|---|---|---|---|
| Opentrons | Open-source benchtop liquid-handling robots (OT-2, Flex) and modular deck peripherals. | `active` | [`Apache-2.0`](https://github.com/Opentrons/opentrons/blob/edge/LICENSE) | yes | [opentrons.com](https://opentrons.com/), [GitHub](https://github.com/Opentrons/opentrons) |
| Hamilton | High-throughput automated liquid-handling workstations (Microlab STAR, Vantage, NIMBUS). | `active` | [`LicenseRef-Proprietary`](https://www.hamiltoncompany.com/automated-liquid-handling) | yes | [hamiltoncompany.com](https://www.hamiltoncompany.com/automated-liquid-handling) |
| Tecan | Automated liquid-handling platforms and microplate workstations (Freedom EVO, Fluent, Cavro). | `active` | [`LicenseRef-Proprietary`](https://www.tecan.com/) | yes | [tecan.com](https://www.tecan.com/) |
| Automata | Modular benchtop lab automation workcells and robotic transport rails (LINQ). | `active` | [`LicenseRef-Proprietary`](https://www.automata.tech/) | yes | [automata.tech](https://www.automata.tech/) |
| Biosero | Vendor-neutral laboratory workcell scheduling and robotic orchestration suite (Green Button Go). | `active` | [`LicenseRef-Proprietary`](https://biosero.com/) | yes | [biosero.com](https://biosero.com/) |

## Cloud labs and automated foundries

Remote symbolic cloud laboratories, biofoundries, and self-driving laboratory research consortia.

| Name | Role / Type | Status | License | Commercial Use | Links |
|---|---|---|---|---|---|
| Emerald Cloud Lab | Remote symbolic cloud laboratory executing wet-lab protocols across 200+ shared instruments. | `active` | [`LicenseRef-Proprietary`](https://www.emeraldcloudlab.com/) | yes | [emeraldcloudlab.com](https://www.emeraldcloudlab.com/) |
| Strateos | Robotic cloud-lab pioneer behind Autoprotocol (remote cloud-lab operations restructured). | `commercial_restructured` | [`LicenseRef-Proprietary`](https://strateos.com/) | no | [strateos.com](https://strateos.com/) |
| Ginkgo Bioworks | High-throughput automated cell-engineering foundry and modular Reconfigurable Automation Carts (RACs). | `active` | [`LicenseRef-Proprietary`](https://www.ginkgobioworks.com/) | yes | [ginkgobioworks.com](https://www.ginkgobioworks.com/) |
| Acceleration Consortium (U of Toronto) | Academic-industrial self-driving laboratories research consortium and open SDL training hub. | `active` | [`LicenseRef-Custom-Check-Upstream`](https://acceleration.utoronto.ca/) | yes | [acceleration.utoronto.ca](https://acceleration.utoronto.ca/) |

## Open-source lab automation software

Hardware drivers, declarative protocol IRs, device communication standards, campaign optimizers, and schedulers (non-OSI licenses flagged explicitly).

| Name | Role / Type | Status | License | Commercial Use | Links |
|---|---|---|---|---|---|
| Opentrons Python API v2 | Python protocol execution API and bundled offline deck/pipette simulator for OT-2 and Flex. | `active` | [`Apache-2.0`](https://github.com/Opentrons/opentrons/blob/edge/LICENSE) | yes | [docs](https://docs.opentrons.com/v2/), [code](https://github.com/Opentrons/opentrons), [PyPI](https://pypi.org/project/opentrons/) |
| PyLabRobot | Hardware-agnostic pure-Python driver and browser visualizer for Hamilton, Tecan, and Opentrons. | `active` | [`MIT`](https://github.com/PyLabRobot/pylabrobot/blob/main/LICENSE) | yes | [GitHub](https://github.com/PyLabRobot/pylabrobot) |
| Autoprotocol | Declarative JSON standard for liquid-handling and incubation operations with Python generator SDK. | `legacy` | [`LicenseRef-Autoprotocol-Custom`](https://github.com/autoprotocol/autoprotocol-python) *(non-OSI)* | no | [GitHub](https://github.com/autoprotocol/autoprotocol-python) |
| LabOP | Open RDF/UML laboratory protocol representation from the Bioprotocols Working Group. | `active` | [`MIT`](https://github.com/Bioprotocols/labop/blob/main/LICENSE.txt) | yes | [GitHub](https://github.com/Bioprotocols/labop), [site](https://www.bioprotocols.org/) |
| SiLA 2 | Open gRPC/Protobuf microservice standard for laboratory instrument discovery and control. | `active` | [`MIT`](https://gitlab.com/SiLA2/sila_python/-/blob/master/LICENSE) | yes | [sila-standard.com](https://sila-standard.com/), [sila_python](https://gitlab.com/SiLA2/sila_python) |
| Aquarium | Human-in-the-loop laboratory workflow, sample inventory, and technician execution LIMS (Krill DSL). | `archived` | [`MIT`](https://github.com/aquariumbio/aquarium/blob/master/LICENSE) | yes | [GitHub](https://github.com/aquariumbio/aquarium) |
| XDL (Chemputer) | Executable XML/JSON chemical synthesis description language for modular batch/flow reactors. | `active` | [`LicenseRef-Custom-Check-Upstream`](https://croningroup.gitlab.io/chemputer/xdl/) *(non-OSI)* | no | [docs](https://croningroup.gitlab.io/chemputer/xdl/), [group](https://www.chem.gla.ac.uk/cronin/) |
| XDL generation | Rule- and NLP-based compiler translating prose organic synthesis procedures into XDL (no OSI license file). | `legacy` | [`NOASSERTION`](https://github.com/ac-rad/xdl-generation) *(non-OSI)* | no | [GitHub](https://github.com/ac-rad/xdl-generation) |
| Atlas | Bayesian optimization planner for mixed continuous/categorical/molecular self-driving lab campaigns. | `active` | [`MIT`](https://github.com/aspuru-guzik-group/atlas/blob/main/LICENSE) | yes | [GitHub](https://github.com/aspuru-guzik-group/atlas) |
| WEI | Argonne autonomous-lab workflow execution engine coordinating ROS2 arms and benchtop instruments. | `active` | [`MIT`](https://github.com/AD-SDL/wei/blob/main/LICENSE) | yes | [GitHub](https://github.com/AD-SDL/wei) |
| Bluesky | Event-driven Python experiment orchestration engine (RunEngine + Ophyd) for instruments and beamlines. | `active` | [`BSD-3-Clause`](https://github.com/bluesky/bluesky/blob/main/LICENSE) | yes | [GitHub](https://github.com/bluesky/bluesky) |
| OR-Tools | Combinatorial optimization suite including the CP-SAT constraint solver used in labshift scheduling. | `active` | [`Apache-2.0`](https://github.com/google/or-tools/blob/stable/LICENSE) | yes | [GitHub](https://github.com/google/or-tools), [docs](https://developers.google.com/optimization) |

## Chemical synthesis, reaction databases, and procurement

Open reaction corpora, retrosynthesis planners, cheminformatics toolkits, vendor APIs, and ELN systems bridging `XDL`, `buy-or-make`, and `assayfold`.

| Name | Role / Type | Status | License | Commercial Use | Links |
|---|---|---|---|---|---|
| Open Reaction Database (ORD) | Open schema and curated repository of structured organic reaction conditions, workups, and yields (indexed in assayfold and buy-or-make). Scale: 2M+ structured organic reactions. Tasks: `reaction_prediction`, `condition_recommendation`, `yield_modeling`. Policy: `train_commercial`, `train_academic`, `eval_only`, `tool_integration` (`git_or_hf_download`). | `active` | [`CC-BY-SA-4.0`](https://github.com/open-reaction-database/ord-data) | yes | [site](https://open-reaction-database.org/), [GitHub](https://github.com/open-reaction-database/ord-schema), [HF](https://huggingface.co/datasets/open-reaction-database/ord-data) |
| USPTO Reactions (Lowe) | Public-domain chemical reactions extracted from US patents (1976-2016) bridging XDL synthesis and buy-or-make route lookup. Scale: 1.8M+ patent chemical reactions (grants + applications). Tasks: `retrosynthesis`, `forward_prediction`, `procedure_extraction`. Policy: `train_commercial`, `train_academic`, `eval_only` (`git_or_hf_download`). | `active` | [`CC0-1.0`](https://doi.org/10.6084/m9.figshare.5104873.v1) | yes | [DOI](https://doi.org/10.6084/m9.figshare.5104873.v1) |
| AiZynthFinder | Monte Carlo tree search retrosynthetic route planner backing multi-step makeability checks in buy-or-make. Tasks: `retrosynthesis`, `stock_triage`. Policy: `tool_integration`, `train_commercial`, `train_academic` (`git_or_hf_download`). | `active` | [`MIT`](https://github.com/MolecularAI/aizynthfinder/blob/master/LICENSE) | yes | [GitHub](https://github.com/MolecularAI/aizynthfinder) |
| RDKit | Open-source cheminformatics, SMILES/InChIKey canonicalization, and SMARTS reaction engine across Auto-Lab. Policy: `tool_integration`, `train_commercial`, `train_academic` (`git_or_hf_download`). | `active` | [`BSD-3-Clause`](https://github.com/rdkit/rdkit/blob/master/license.txt) | yes | [site](https://www.rdkit.org/), [GitHub](https://github.com/rdkit/rdkit) |
| PubChem PUG REST | NCBI programmatic chemical structure, safety GHS, and commercial vendor directory API queried by buy-or-make (<= 5 req/s). Policy: `tool_integration`, `rag_pointer_only` (`public_api_rate_limited`). | `active` | [`CC0-1.0`](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest) | yes | [docs](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest) |
| eLabFTW | Open-source electronic lab notebook (ELN) and chemical/sample inventory manager with OpenAPI REST interface. Policy: `tool_integration` (`public_api_rate_limited`). | `active` | [`AGPL-3.0-only`](https://github.com/elabftw/elabftw/blob/master/LICENSE) | yes | [site](https://www.elabftw.net/), [GitHub](https://github.com/elabftw/elabftw) |

## Open protocol sources and datasets

Wet-lab protocol repositories and evaluation benchmarks with `assayfold`-harmonized SPDX licenses, commercial-use gates, and benchmark-contamination guards.

| Name | Role / Type | Status | License | Commercial Use | Links |
|---|---|---|---|---|---|
| protocols.io | Open repository of community wet-lab protocols with versioned DOIs and rate-limited REST API. Scale: Public open-access protocol collection via REST API v3/v4. Tasks: `protocol_retrieval`, `step_parsing`. Policy: `rag_pointer_only`, `train_commercial`, `train_academic` (`public_api_rate_limited`). | `active` | [`CC-BY-4.0`](https://www.protocols.io/terms) | yes | [site](https://www.protocols.io/), [API](https://www.protocols.io/developers) |
| Bio-protocol | Peer-reviewed life-science protocol journal; individual articles carry per-article copyright terms. Scale: 4,500+ peer-reviewed protocol articles (no bulk scraping). Tasks: `literature_reference`. Policy: `rag_pointer_only` (`no_bulk_scraping_per_article`). | `active` | [`LicenseRef-Per-Article`](https://bio-protocol.org/) | no | [bio-protocol.org](https://bio-protocol.org/) |
| Wet Lab Protocols (WLP) | Fine-grained span and action-graph annotated wet-lab protocol corpus used in assayfold and lab-ears. Scale: 622 annotated protocols. Tasks: `ner`, `relation_extraction`, `action_graph`. Policy: `train_commercial`, `train_academic`, `eval_only` (`git_or_hf_download`). | `active` | [`MIT`](https://github.com/chaitanya2334/WLP-Dataset/blob/master/LICENSE) | yes | [GitHub](https://github.com/chaitanya2334/WLP-Dataset) |
| BioPlanner (BioProt) | Automatic evaluation benchmark for translating biology protocol goals into structured pseudocode functions. Scale: 100 curated evaluation protocols (BioProt). Tasks: `planning`, `next_step_prediction`, `pseudocode_generation`. Policy: `eval_only` (`git_or_hf_download`). **Contamination guard**: Held-out planning benchmark; exclude evaluation splits from L3 post-training. | `active` | [`NOASSERTION`](https://github.com/bioplanner/bioplanner) | no | [paper](https://arxiv.org/abs/2310.10632), [GitHub](https://github.com/bioplanner/bioplanner) |
| BioProBench | Multi-task biological protocol benchmark aligned with assayfold (`CC-BY-NC-4.0`, non-commercial). Scale: 4,333 test items (PQA 1,200; ORD 1,161; ERR 1,200; GEN 772). Tasks: `qa`, `ordering`, `error_detection`, `generation`. Policy: `eval_only` (`git_or_hf_download`). **Contamination guard**: Non-commercial held-out benchmark; never ingest into commercial pipelines or L3 training. | `active` | [`CC-BY-NC-4.0`](https://github.com/YuyangSunshine/bioprobench) | no | [paper](https://arxiv.org/abs/2505.07889), [GitHub](https://github.com/YuyangSunshine/bioprobench), [HF](https://huggingface.co/datasets/BioProBench/BioProBench) |
| LAB-Bench | FutureHouse biology research evaluation suite including ProtocolQA, LitQA2, DbQA, and CloningScenarios. Scale: 1,967 rows across 8 subsets (108 ProtocolQA). Tasks: `qa`, `protocol_qa`, `lit_qa`, `db_qa`, `seq_qa`. Policy: `eval_only` (`git_or_hf_download`). **Contamination guard**: Contains benchmark canary strings; strictly eval_only — never train on LAB-Bench splits. | `active` | [`CC-BY-SA-4.0`](https://huggingface.co/datasets/futurehouse/lab-bench) | yes | [paper](https://arxiv.org/abs/2407.10362), [GitHub](https://github.com/Future-House/LAB-Bench), [HF](https://huggingface.co/datasets/futurehouse/lab-bench) |

## Embodied simulation and formal verification (`L4` cross-references)

Pointer bridge to embodied robotics/digital-twin benchmarks in `lab-rehearsal` and formal Lean 4 / SQL verification gates in `lab-verify`.

| Name | Role / Type | Status | License | Commercial Use | Links |
|---|---|---|---|---|---|
| LabUtopia | High-fidelity Isaac-based lab scenes and hierarchical embodied agent benchmark (curated in L4 lab-rehearsal). Tasks: `embodied_manipulation`, `hierarchical_planning`. | `active` | [`MIT`](https://github.com/Rui-li023/LabUtopia/blob/main/LICENSE) | yes | [paper](https://arxiv.org/abs/2505.22634), [GitHub](https://github.com/Rui-li023/LabUtopia), [lab-rehearsal](https://github.com/yaniguan/lab-rehearsal) |
| AutoBio | MuJoCo biology lab manipulation simulation for pipetting, centrifuges, and thermal cyclers (curated in L4 lab-rehearsal). Tasks: `pipetting_sim`, `instrument_manipulation`. **Contamination guard**: Held-out embodied lab manipulation benchmark (NOASSERTION license); exclude evaluation scenes from L3 training corpora. | `active` | [`NOASSERTION`](https://github.com/autobio-bench/AutoBio) | no | [paper](https://arxiv.org/abs/2505.14030), [GitHub](https://github.com/autobio-bench/AutoBio), [lab-rehearsal](https://github.com/yaniguan/lab-rehearsal) |
| MATTERIX | Multiscale digital twin combining robotic manipulation, liquid/powder handling, and reaction kinetics (curated in L4 lab-rehearsal). Tasks: `digital_twin`, `chemistry_simulation`. | `active` | [`Apache-2.0`](https://arxiv.org/abs/2601.13232) | yes | [paper](https://arxiv.org/abs/2601.13232), [lab-rehearsal](https://github.com/yaniguan/lab-rehearsal) |
| Lean 4 & miniF2F | Interactive theorem prover kernel and formal benchmark backing L4 lab-verify and L6 YLM LabLean proofs. Tasks: `formal_verification`, `theorem_proving`. | `active` | [`Apache-2.0`](https://github.com/leanprover/lean4/blob/master/LICENSE) | yes | [Lean 4](https://github.com/leanprover/lean4), [miniF2F](https://github.com/facebookresearch/miniF2F), [lab-verify](https://github.com/yaniguan/lab-verify) |
| Spider 2.0 | Enterprise database-grounded text-to-SQL benchmark cross-indexed with L4 lab-verify 4-layer SQL gate. Tasks: `text_to_sql`, `execution_verification`. **Contamination guard**: Held-out SQL benchmark cross-referenced with lab-verify. | `active` | [`MIT`](https://github.com/xlang-ai/Spider2/blob/main/LICENSE) | yes | [site](https://spider2-sql.github.io/), [GitHub](https://github.com/xlang-ai/Spider2), [lab-verify](https://github.com/yaniguan/lab-verify) |

## Hardware-to-SDK-to-IR compatibility matrix

Generated from structured `supported_hardware`, `protocol_formats`, and `has_simulator` fields in [`atlas.json`](atlas.json):

| Hardware Platform | Open-Source SDKs / Drivers | Protocol IRs / Standards | Offline Simulators | Auto-Lab Integrations |
|---|---|---|---|---|
| Opentrons OT-2 / Flex | Opentrons Python API v2, PyLabRobot, LabOP, WEI | `Rehearsal Step JSON`, `Stepbot YAML/JSON`, `Opentrons Python API v2`, `PyLabRobot Python`, `LabOP RDF/JSON`, `Autoprotocol JSON`, `WEI YAML Workflow` | lab-rehearsal, stepbot, Opentrons Python API v2, PyLabRobot, WEI | `lab-rehearsal`, `stepbot` |
| Hamilton STAR / Vantage | PyLabRobot, SiLA 2 | `PyLabRobot Python`, `SiLA 2 gRPC/Protobuf` | PyLabRobot, SiLA 2 | — |
| Tecan EVO / Fluent | PyLabRobot, SiLA 2 | `PyLabRobot Python`, `SiLA 2 gRPC/Protobuf` | PyLabRobot, SiLA 2 | — |
| Cloud Labs (ECL / Strateos) | Emerald Cloud Lab, Strateos, Autoprotocol, LabOP | `Symbolic Lab Language (SLL)`, `Autoprotocol JSON`, `LabOP RDF/JSON`, `Opentrons Python API v2` | Emerald Cloud Lab | — |
| Chemputer Modular Synthesis | XDL (Chemputer), XDL generation | `XDL XML/JSON` | XDL (Chemputer) | — |
| Modular SDL / Beamlines (ROS2, EPICS) | Acceleration Consortium (U of Toronto), Atlas, WEI, Bluesky | `Python Campaign API`, `WEI YAML Workflow`, `Bluesky RunEngine Plans` | Atlas, WEI, Bluesky | — |

<!-- END GENERATED CATALOG -->

## Governance: Rate Limits, Scraping & Benchmark-Contamination Policy

Every dataset and API entry in [`atlas.json`](atlas.json) declares `allowed_purposes`, `scraping_policy`, and `contamination_warning`:

- **Held-out evaluation suites (`eval_only`)**: `LAB-Bench` (carries benchmark canary strings), `BioProBench` (`CC-BY-NC-4.0` non-commercial), `BioPlanner`, and `Spider 2.0` must **never** be ingested into `L3` post-training (`labbench-posttrain`) or commercial training corpora.
- **Permissive training corpora (`train_commercial` / `train_academic`)**: `Wet Lab Protocols (WLP)` (`MIT`), `Open Reaction Database` (`CC-BY-SA-4.0`), and `USPTO Reactions (Lowe)` (`CC0-1.0`) are synchronized with [`assayfold`](https://github.com/yaniguan/assayfold) license gates.
- **Rate-limited APIs & journal terms**: `PubChem PUG REST` (`<= 5 req/s`) and `protocols.io` require polite API rate limiting (`public_api_rate_limited`); `Bio-protocol` articles carry per-article copyright (`no_bulk_scraping_per_article`).

## How the links are checked

`scripts/check_links.py` parses inline links (including balanced nested parentheses and link titles), reference links, autolinks, and relative local paths/anchors across `README.md` and `docs/*.md`. It checks external URLs concurrently over HTTPS with SSRF protection, `HEAD -> GET` fallback, bounded exponential retry on `429`/`502`/`503`/`504`, soft-404/root-redirect warnings, and an explicit vendor-only WAF `403` allowlist (`github.com`, `arxiv.org`, `huggingface.co`, and `pypi.org` are never `403`-allowlisted). Non-zero exit codes fail CI whenever a broken link is detected.

## 15-Repository Auto-Lab Wire Contract (autolab-wire/v1)

[`autolab_wire.py`](autolab_wire.py) (`REPO_ID = "lab-automation-atlas"`, `LAYER = "L5"`) exposes `process_packet(packet: dict) -> dict` for the 15-repository closed-loop Auto-Lab wire:

- **Upstream / Downstream**: Consumes candidate goals and datasets after `L2` (`assayfold`, `lab-ears`) and `L6` (`lab-ask-why`, `lab-decide`), grounds hardware/SDK capabilities (`platform_grounding`) for `L5` (`buy-or-make`, `labshift`), `L4` pre-execution gates (`lab-rehearsal`, `lab-verify`), `L1`/`L0` execution (`stepbot`, `lab-hands`, `lab-feet`), `L4` post-execution causal blame (`lab-attrib`), and `L3` post-training (`twinstep`, `labfill`, `labbench-posttrain`).
- **Safety & License Gate**: Enforces `LabAtlasLean` `eval_only_blocked_from_training` and HTTPS-only public-host SSRF validation, halting unsafe URLs or restricted training licenses (`eval_only`, `CC-BY-NC-2.0`, `non_commercial`) with `halt_reason = "L5_ATLAS_LICENSE_OR_URL_BLOCK"`.

## License

Code, schema, and catalog annotations in this repository are MIT licensed ([`LICENSE`](LICENSE)). Linked projects and datasets retain their own upstream licenses.
