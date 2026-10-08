# Offline replay walkthrough

Run `triad-rsi-demo --output artifacts/demo` after installation. Six synthetic tasks are replayed over six attempts. Coverage first selects Data, Harness, Model; later choices use the bandit and balance constraints.

| Label | Majority baseline | Majority candidate | Gate |
| --- | --- | --- | --- |
| Data | 2/6 | 3/6 | Accept under net-improvement |
| Harness | 2/6 | 2/6 | Reject tie |
| Model | 2/6 | 1/6 | Reject regression |

These are invented fixtures, **not evidence of relative operator effectiveness**. Measurements reset every iteration. No model or accepted checkpoint is updated. Costs are synthetic units.

Inspect `iteration-000/confirmation.json` for votes/order, `selection.json` for scheduling evidence, and `summary.json` for attempt history.

A real integration supplies independent execution through the callback in [evaluation.md](../docs/evaluation.md), resets state, pairs seeds, and separates data partitions.
