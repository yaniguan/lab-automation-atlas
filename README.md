# lab-automation-atlas

A short, high-level map of automated-lab platforms, lab automation software, and open protocol datasets.
Every link below was opened and checked on 2026-11-18.

This is a pointer list only. It does not copy data, rank vendors, or claim any partnership.
Check each project's own license before you use it.

## Related tools in this account

| Repo | What it does |
|---|---|
| [twinstep](https://github.com/yaniguan/twinstep) | Makes labeled error twins of protocol step lists for error-detection and ordering benchmarks |
| [labshift](https://github.com/yaniguan/labshift) | Lab scheduling benchmark: jobs on shared instruments, greedy and CP-SAT solvers, makespan metrics |
| [stepbot](https://github.com/yaniguan/stepbot) | Compiles a simple step format to Opentrons Python API v2 protocols and checks them in a simulator |

## Liquid handlers and lab robots

| Name | Type | Link |
|---|---|---|
| Opentrons | Open-source liquid-handling robots (OT-2, Flex) | [opentrons.com](https://opentrons.com/) |
| Hamilton | Automated liquid handling | [hamiltoncompany.com](https://www.hamiltoncompany.com/automated-liquid-handling) |
| Tecan | Liquid handling and lab automation | [tecan.com](https://www.tecan.com/) |
| Automata | Lab automation systems | [automata.tech](https://www.automata.tech/) |
| Biosero | Lab automation scheduling and orchestration | [biosero.com](https://www.biosero.com/) |

## Cloud labs and automated foundries

| Name | Type | Link |
|---|---|---|
| Emerald Cloud Lab | Remote cloud lab | [emeraldcloudlab.com](https://www.emeraldcloudlab.com/) |
| Strateos | Robotic cloud lab | [strateos.com](https://www.strateos.com/) |
| Ginkgo Bioworks | Automated biology foundry | [ginkgobioworks.com](https://www.ginkgobioworks.com/) |
| Acceleration Consortium (U of Toronto) | Self-driving labs research program | [acceleration.utoronto.ca](https://acceleration.utoronto.ca/) |

## Open-source lab automation software

| Name | What it is | Link |
|---|---|---|
| Opentrons Python API v2 | Python protocols for Opentrons robots, with a simulator | [docs](https://docs.opentrons.com/v2/), [code](https://github.com/Opentrons/opentrons), [PyPI](https://pypi.org/project/opentrons/) |
| PyLabRobot | Hardware-agnostic Python interface for liquid handlers | [GitHub](https://github.com/PyLabRobot/pylabrobot) |
| Autoprotocol | JSON standard for lab protocols, with a Python library | [GitHub](https://github.com/autoprotocol/autoprotocol-python) |
| LabOP | Open protocol representation (Bioprotocols Working Group) | [GitHub](https://github.com/Bioprotocols/labop), [site](https://www.bioprotocols.org/) |
| SiLA 2 | Open standard for lab device communication | [sila-standard.com](https://sila-standard.com/) |
| Aquarium | Lab workflow and inventory system | [GitHub](https://github.com/aquariumbio/aquarium) |
| XDL (Chemputer) | Chemical description language for automated synthesis | [docs](https://croningroup.gitlab.io/chemputer/xdl/), [group](https://www.chem.gla.ac.uk/cronin/) |
| XDL generation | Turning text procedures into XDL | [GitHub](https://github.com/ac-rad/xdl-generation) |
| Atlas | Bayesian optimization for self-driving labs | [GitHub](https://github.com/aspuru-guzik-group/atlas) |
| WEI | Workflow execution for autonomous labs | [GitHub](https://github.com/AD-SDL/wei) |
| Bluesky | Experiment orchestration for instruments | [GitHub](https://github.com/bluesky/bluesky) |
| OR-Tools | Open-source solvers, incl. CP-SAT for scheduling | [GitHub](https://github.com/google/or-tools), [docs](https://developers.google.com/optimization) |

## Open protocol sources and datasets

| Name | What it is | License note | Link |
|---|---|---|---|
| protocols.io | Open repository of lab protocols, with a public API | Per protocol | [site](https://www.protocols.io/), [API](https://www.protocols.io/developers) |
| Bio-protocol | Peer-reviewed protocol journal | Per article | [bio-protocol.org](https://bio-protocol.org/) |
| Wet Lab Protocols (WLP) | Annotated protocol text (actions, amounts, times) | MIT (repo) | [GitHub](https://github.com/chaitanya2334/WLP-Dataset) |
| BioPlanner (BioProt) | Protocol planning benchmark | See repo | [paper](https://arxiv.org/abs/2310.10632), [GitHub](https://github.com/bioplanner/bioplanner) |
| BioProBench | Protocol QA, step ordering, error correction, generation | Non-commercial (check repo) | [paper](https://arxiv.org/abs/2505.07889), [GitHub](https://github.com/YuyangSunshine/bioprobench) |
| LAB-Bench | Biology research tasks, incl. ProtocolQA | CC-BY-SA-4.0 (repo) | [paper](https://arxiv.org/abs/2407.10362), [GitHub](https://github.com/Future-House/LAB-Bench), [HF](https://huggingface.co/datasets/futurehouse/lab-bench) |

## How the links were checked

Each URL was fetched on 2026-11-18 and returned a live page. Some vendor sites block scripted
requests, so they were opened in a normal page fetch. Links can move; please open an issue if one breaks.

## License

The text in this list is MIT licensed. Linked projects keep their own licenses.
