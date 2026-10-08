# Roadmap

Triad-RSI is under active development. These are scoped plans without promised dates.

## v1 / 0.1.0 — public core preview

- [x] Cost-aware scheduling and eligibility/coverage constraints.
- [x] Paired acceptance and repeated evaluation receipts.
- [x] Dependency-free synthetic replay.
- [x] Tests, evaluation notes, provenance, and MIT license.

## v2 / 0.2.x — portable experiment loop (planned)

- [ ] Stable Data, Harness, and Model operator interfaces.
- [ ] Provider-neutral training, inference, and evaluation adapters.
- [ ] Accepted-state persistence, candidate provenance, and resume logic.
- [ ] One small end-to-end integration with documented dependencies.

Exit criterion: another user can execute, inspect, and resume a real candidate experiment with their own backend.

## v3 / 0.3.x — improvement-rule experiments (planned)

- [ ] Bounded rule revisions and same-start old/new policy trials.
- [ ] Separate adaptive selection, meta evaluation, and held-out reporting.
- [ ] Equal-budget baselines and component ablations.
- [ ] Reproducible configurations and shareable experiment artifacts.

Exit criterion: artifacts permit independent assessment of whether a rule update improves subsequent experiments. A valid negative result also meets this criterion; positive recursive gains are not assumed.
