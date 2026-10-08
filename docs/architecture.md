# Architecture

**Nested-RSI: Local Improvement Loops, Global System Evolution.**

## RSI within RSI

The outer loop selects an improvement operator; the operator can run a bounded feedback loop to construct its candidate. Local search outcomes feed system-level evaluation, while accumulated experiment evidence can inform later proposal rules and scheduling policies.

Data-RSI makes this concrete in the prototype: current-student execution, paired probes of locally revised harnesses, teacher assistance for unresolved targets, and optional teacher-side harness refinement. Teacher failures can trigger further diagnosis rather than ending the data-construction process. Every stage uses verified outcomes, not model identity, to qualify trajectories.

This workflow operates on improvement tasks. Temporary harness probes do not mutate production state. Selecting a locally useful harness and retaining an individually verified trajectory are separate decisions; a candidate student trained from the pool must still pass the outer gate.

Once accepted, the updated student participates in subsequent improvement iterations. Demonstrating that this inheritance improves later search or data efficiency is a research objective. A fixed escalation ladder alone is not evidence of recursive progress.

## State and policy

Nested-RSI separates **system state** (accepted model, harness, data pool, training recipe) from **improvement policy** (operator proposal rules and experiment scheduling).

The research prototype proposes a candidate, evaluates it against the accepted state, and carries accepted changes forward. Public v1 exposes scheduling and comparison primitives; callers are responsible for execution, persistence, and state promotion.

| Module | Inputs | Outputs |
| --- | --- | --- |
| `bandit` | Eligible actions and observed gains/costs | Probabilities and a seeded action |
| `scheduler` | Eligibility, history, bandit, optional proposer callback | Operator and JSON receipt |
| `gate` | Exactly paired task outcomes | Gains, regressions, p-value, decision |
| `confirmation` | Initial evaluations and a rerun callback | Repeated votes and a final gate |

## Scheduling

The bandit adds a UCB exploration bonus to mean reward, applies softmax, then mixes in a uniform floor. The reward is `performance_gain - cost_weight * cost_units`. Callers must define consistent cost units. Poor scaling can favor cheap unsuccessful actions over expensive useful ones; the demo's units are illustrative, not dollars or measured compute.

`select(...)` applies cumulative attempt balance, coverage, and recent concentration constraints before mixing a legal proposer suggestion with bandit sampling. Rejected attempts count toward coverage. Coverage can override recent caps; explicit relaxations are recorded when caps cannot be satisfied.

The optional `proposer(payload)` returns `{"operator": "data", "reason": "..."}`. It can wrap a model or deterministic policy. An invalid response or `ValueError` falls back to the bandit; other exceptions propagate. No model provider or private prompt is bundled.

## Intended operator contracts

- Data: change the pool and train with a fixed recipe. This is not a weights-frozen intervention.
- Model: hold the accepted pool fixed and change the training recipe to produce a checkpoint.
- Harness: change agent guidance/execution behavior while keeping weights fixed.

These contracts describe the prototype; full operator implementations are not part of v1.

## Improving the improver

A future milestone compares old and new improvement rules from the same frozen system state. Equal round counts alone do not mean equal compute: record costs, use independent evaluation, and repeat across starts/seeds. This preview does not install rule candidates or claim improved research efficiency.
