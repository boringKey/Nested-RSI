<div align="center">

# Nested-RSI

### Local Improvement Loops, Global System Evolution

**Exploring RSI within RSI across data, harnesses, and models.**

[![Tests](https://github.com/boringKey/Nested-RSI/actions/workflows/tests.yml/badge.svg)](https://github.com/boringKey/Nested-RSI/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Status](https://img.shields.io/badge/Status-Research%20Preview-orange)

[RSI within RSI](#rsi-within-rsi) · [Quick start](#quick-start) · [Roadmap](ROADMAP.md) · [中文介绍](docs/README.zh-CN.md)

</div>

**Nested-RSI explores an “RSI within RSI” architecture:** an outer loop coordinates improvements to an agent system, while individual improvement operators can run their own feedback-driven local loops. Local outcomes produce candidate data, harnesses, or models; only system changes accepted by the outer comparison become the starting state of subsequent global iterations.

The research focus is on **how improvement is organized**: local search and verification inside an operator, coordinated selection across operators, and evidence-driven revision of the improvement rules themselves.

**Current release: v1 / 0.1.0, public core preview.** Scheduling, paired evaluation, and repeated confirmation are available with a runnable offline demo. The full nested improvement workflows and training integrations are being prepared for release. Development is ongoing. See [release scope](docs/release-scope.md) and [changelog](CHANGELOG.md).

## RSI within RSI

An improvement operator need not be a single fixed action. To improve the global system, it may first need to improve the process that produces its own candidates.

| Level | Question | What changes? |
| --- | --- | --- |
| **Local operator loop** | How can this improvement attempt produce a better candidate? | Execution support, candidate construction, and validated local artifacts. |
| **Global system loop** | Which intervention should be tried and inherited next? | The accepted data pool, harness, model checkpoint, and training recipe. |
| **Improvement-rule revision** | Can experience make later improvement attempts more effective? | Operator proposal rules and experiment scheduling policies, subject to separate evaluation. |

The outer loop coordinates **Data-RSI**, **Harness-RSI**, and **Model-RSI**. For example, Data-RSI can first use the current student to generate trajectories, revise its harness in response to failures, and introduce teacher assistance for unresolved tasks. Verified experience then supports a student candidate that must pass the outer evaluation before being inherited. This illustrates how a local feedback loop can support global system evolution.

“Nested” describes this architecture. A bounded retry or assistance ladder alone does not establish recursive progress. The stronger research objective is to show that inherited artifacts or revised rules improve later cycles—not merely that multiple loops execute.

## What is inherited?

- **Trajectory admission:** a sample passes execution and quality checks and becomes eligible for the data pool.
- **System acceptance:** a candidate passes the outer comparison and becomes the accepted state for later iterations.
- **Rule acceptance:** a proposed improvement policy requires a separate same-start old/new comparison before adoption.

These are distinct decisions. Local success does not bypass the global gate, and global selection outcomes do not substitute for held-out evaluation.

The project studies this separation through controlled comparisons and reproducible evidence. It does not claim that every operator already has an equally developed internal loop, or that sustained recursive gains have been demonstrated by the public preview. See [architecture](docs/architecture.md) and [evaluation](docs/evaluation.md).

## Current public release

- **Cost-aware operator policy:** softmax-UCB sampling with exploration and a uniform probability floor.
- **Controlled scheduling:** eligibility, coverage, attempt-balance constraints, and an optional injected proposal callback.
- **Paired selection:** exact task pairing, gain/regression accounting, and configurable acceptance rules.
- **Repeated confirmation:** three runs per side by default, task-wise majority outcomes, and recorded confirmation order.
- **Inspectable receipts:** JSON records of decisions, probabilities, votes, and gate results.
- **Offline demo:** deterministic synthetic replay with no API key, GPU, model download, or runtime dependency.

The demo does **not** generate data, train a model, or reproduce benchmark results.

## Quick start

Requires Python 3.10+. The v1 Python namespace (`triad_rsi`) and CLI (`triad-rsi-demo`) retain their original names for compatibility; the project and repository are now Nested-RSI.

```bash
git clone https://github.com/boringKey/Nested-RSI.git
cd Nested-RSI
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install .
triad-rsi-demo --output artifacts/demo
python -m unittest discover -s tests -v
```

For a source-only run without installation:

```bash
PYTHONPATH=src python -m triad_rsi.demo --output artifacts/demo
```

The demo replays six synthetic iterations, including an improving candidate, an unchanged candidate, and a regressing candidate. It writes:

```text
artifacts/demo/
├── summary.json
└── iteration-000/ ... iteration-005/
    ├── selection.json
    └── confirmation.json
```

Fixtures reset each iteration. Accepted demo outcomes do not imply cumulative learning. See [the walkthrough](examples/README.md).

## Use the core

```python
from triad_rsi import Bandit, gate_from_vectors

policy = Bandit(["data", "harness", "model"])
operator, probabilities = policy.choose(seed=7, eligible=["data", "harness"])

baseline = {("example", "task-1"): False, ("example", "task-2"): True}
candidate = {("example", "task-1"): True, ("example", "task-2"): True}
result = gate_from_vectors(baseline, candidate, acceptance_rule="net_improvement")

# Count the accepted gain; charge cost even when a proposal is rejected.
gain = result["delta"] if result["accepted"] else 0.0
policy.update(operator, performance_gain=gain, cost_units=1.0)
```

This tiny example illustrates the API, not statistical evidence. [Evaluation notes](docs/evaluation.md) explain majority voting, the two gate modes, and why adaptive selection is not held-out evaluation.

## Repository layout

```text
src/triad_rsi/
  bandit.py         Cost-aware operator probabilities
  scheduler.py      Eligibility, coverage, balance, proposal callback
  gate.py           Paired candidate acceptance
  confirmation.py   Repeated evaluations and majority votes
  demo.py           Synthetic offline replay
docs/               Architecture, evaluation, release scope, Chinese overview
examples/           Demo walkthrough
tests/              Core behavior and failure-path tests
```

## Release plan

| Milestone | Status | Scope |
| --- | --- | --- |
| **v1 / 0.1.0** | Current public preview | Scheduling, paired gates, repeated confirmation, demo, tests and documentation. |
| **v2 / 0.2.x** | Planned | Portable operator/backend interfaces, Data-RSI assistance loops, and accepted-state persistence. |
| **v3 / 0.3.x** | Planned | Same-start improvement-rule trials and reproducible held-out evaluation recipes. |

Future milestones are plans, not completed releases. The original experiments' internal iteration numbers are not public version numbers. See [ROADMAP.md](ROADMAP.md).

## Contributing

Reproducible bug reports, evaluation-protocol discussions, and backend integration proposals are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md).

## License

The code and documentation in this repository are released under the [MIT License](LICENSE). External models and datasets retain their respective terms.
