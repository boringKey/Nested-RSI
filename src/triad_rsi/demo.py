"""Offline synthetic replay. No model training, inference, or benchmark claims."""
import argparse
import json
from pathlib import Path

from . import Bandit, confirm_gate, paired_gate, select
from .io import write_json


def run(output, seed=7):
    output = Path(output)
    rows = [{"domain": "synthetic", "task_id": str(i)} for i in range(6)]
    baseline_votes = [
        [True, True, False, False, False, False],
        [True, True, False, False, False, True],
        [True, True, False, False, False, False],
    ]
    candidates = {
        "data": [
            [True, True, True, False, False, False],
            [True, True, True, True, False, False],
            [True, True, True, False, False, False],
        ],
        "harness": baseline_votes,
        "model": [[True, False, False, False, False, False]] * 3,
    }

    def summary(votes):
        return {"complete": True, "results": [dict(row, resolved=value) for row, value in zip(rows, votes)]}

    policy = Bandit(["data", "harness", "model"])
    history = []
    limits = {"window": 6, "max_per_window": 3, "max_consecutive": 2, "max_count_gap": 2}
    for iteration in range(6):
        step = output / f"iteration-{iteration:03d}"
        operator = select({}, policy, ["data", "harness", "model"], seed + iteration,
                          step / "selection.json", history=history, balance=limits)
        baseline = summary(baseline_votes[0])
        candidate = summary(candidates[operator][0])
        raw = paired_gate(baseline, candidate, acceptance_rule="net_improvement")

        def rerun(requested_rows, side, attempt):
            assert requested_rows == rows
            votes = baseline_votes if side == "baseline" else candidates[operator]
            return summary(votes[attempt + 1])

        result, receipt = confirm_gate(raw, baseline, candidate, rows, rerun,
                                      output=step / "confirmation.json", reruns=2, scope="full")
        gain = result["delta"] if result["accepted"] else 0.0
        reward = policy.update(operator, gain, cost_units=1.0)
        history.append({"iteration": iteration, "operator": operator,
                        "accepted": result["accepted"], "delta": result["delta"],
                        "reward": reward, "synthetic_cost_units": 1.0})
    report = {"mode": "synthetic_replay", "seed": seed, "history": history,
              "bandit": policy.state,
              "note": "Fixed fixtures reset each iteration. This demonstrates selection and gate mechanics, not cumulative improvement or benchmark performance."}
    write_json(output / "summary.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/demo"))
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    report = run(args.output, args.seed)
    print(json.dumps({"mode": report["mode"], "iterations": len(report["history"]),
                      "artifacts": str(args.output), "note": report["note"]}, indent=2))


if __name__ == "__main__":
    main()
