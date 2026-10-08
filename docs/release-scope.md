# Release scope and provenance

v1 is a curated extraction from the author's existing research prototype, not a full experiment-workspace export. It cannot reproduce the complete training campaign.

| Public module | Prototype origin | Adaptation |
| --- | --- | --- |
| `bandit.py` | `policy_tau/meta_policy.py` | Original equations; input/state validation and defensive copies. |
| `scheduler.py` | `controller_tau/selector.py` | Original coverage/balance logic; replace provider and embedded prompt with a callback. |
| `gate.py` | `harness_tau/evaluator.py` | Original paired gate; reject invalid outcomes and duplicate/error rows. |
| `confirmation.py` | `harness_tau/confirmation.py` | Original voting/order; require completed Boolean summaries and recompute initial gate from evidence. |

Packaging, demo fixtures, documentation, and public tests were prepared for this release. Included defaults are public illustrative defaults, not a complete experimental recipe. The extracted package has not been rerun against the original full benchmark campaign.

## Included

Scheduling and evaluation code, a deterministic offline replay, behavior tests, architecture/evaluation documentation, and version history.

## Not included

- Production orchestration, training/serving integrations, and checkpoints.
- Data synthesis prompts, teacher configurations, and full operators.
- Raw traces, private datasets, held-out task lists, and unreleased analyses.
- Credentials, service endpoints, account settings, and machine-specific paths.
- Rule generation, same-start trial execution, and policy promotion.

Future milestones describe intended work, not currently available features. This release does not include third-party benchmark implementations or data.
