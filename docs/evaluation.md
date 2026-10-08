# Evaluation protocol

## Three runs per side

1. The caller evaluates all selection tasks once under baseline and candidate.
2. Confirmation repeat 0 evaluates candidate, then baseline.
3. Confirmation repeat 1 evaluates baseline, then candidate.
4. Each task receives three Boolean outcomes per side; at least two successes resolve that side as successful.
5. Compare the majority-outcome vectors to count gains and regressions.

For N tasks this uses **6N episodes** including the initial pair. `confirm_gate` only invokes the four additional evaluations. Each evaluation must start from fresh task state. Pair task seeds across arms for each repeat; the callback is responsible for resets and seeds, which the library cannot enforce.

```text
baseline task A:  [false, true, false] -> false
candidate task A: [true, false, true] -> true
=> one gained task
```

This estimates a majority-resolved outcome, not the average success rate. Both are recorded in full mode and can disagree. Three repeats are not three independent tasks.

The prototype's `scope="discordant"` mode is retained for compatibility; it repeats only initially discordant tasks, yielding mixed coverage. Prefer `scope="full"`. An even nonnegative `reruns` value produces an odd total vote count.

## Acceptance

- `net_improvement`: accept only when gains exceed regressions. The p-value is descriptive.
- `significance`: additionally require exact one-sided McNemar p <= alpha (default 0.1).

Fix the mode and alpha before an experiment. Ties and regressions are rejected. Incomplete summaries, duplicate/missing tasks, execution errors, and non-Boolean outcomes are rejected rather than scored as failures.

The statistic uses discordant tasks. Adaptive repeated selection is not a held-out significance claim, even in significance mode. Task dependence may further weaken its interpretation.

## Evidence separation

The intended full experiment separates improvement data, adaptive selection, rule-level meta evaluation, and final held-out evaluation. This package does not enforce dataset splits or contamination control; backend integrations must implement them. No benchmark scores or empirical synergy claims are published with v1.

## Callback contract

`rerun(rows, side, attempt)` receives `baseline` or `candidate` and a zero-based confirmation attempt. Return exactly the requested tasks, once each:

```python
{"complete": True, "results": [
    {"domain": "example", "task_id": "task-1", "resolved": True}
]}
```

Use consistent string IDs and Boolean outcomes. A truthy `error` rejects the summary. Handle infrastructure failures before reporting completion. Optional `output_tokens` is metadata, not a score.
