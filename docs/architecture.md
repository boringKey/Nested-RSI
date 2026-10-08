# Architecture

Triad-RSI separates **system state** (accepted model, harness, data pool, training recipe) from **improvement policy** (operator proposal rules and experiment scheduling).

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
