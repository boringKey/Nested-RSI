import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

from triad_rsi import Bandit, confirm_gate, gate_from_vectors, paired_gate, select
from triad_rsi.demo import run


def summary(values):
    return {"complete": True, "results": [
        {"domain": "example", "task_id": str(i), "resolved": v}
        for i, v in enumerate(values)
    ]}


class GateTests(unittest.TestCase):
    def test_modes_disagree_on_small_gain(self):
        a, b = summary([False, True]), summary([True, True])
        result = paired_gate(a, b, acceptance_rule="net_improvement")
        self.assertTrue(result["accepted"])
        self.assertEqual(result["paired_one_sided_p"], 0.5)
        self.assertFalse(result["p_value_is_gate"])
        self.assertFalse(paired_gate(a, b)["accepted"])

    def test_exact_tail(self):
        result = paired_gate(summary([False] * 5), summary([True] * 5))
        self.assertTrue(result["accepted"])
        self.assertEqual(result["paired_one_sided_p"], 1 / 32)

    def test_tie_and_regression(self):
        a = summary([True, False])
        for b in [summary([False, True]), summary([False, False])]:
            self.assertFalse(paired_gate(a, b, acceptance_rule="net_improvement")["accepted"])

    def test_invalid_summaries_fail_closed(self):
        good = summary([True, False])
        bad_cases = []
        bad = copy.deepcopy(good); bad["complete"] = False; bad_cases.append(bad)
        bad = copy.deepcopy(good); del bad["complete"]; bad_cases.append(bad)
        bad = copy.deepcopy(good); bad["results"].pop(); bad_cases.append(bad)
        bad = copy.deepcopy(good); bad["results"].append(bad["results"][0]); bad_cases.append(bad)
        bad = copy.deepcopy(good); bad["results"][0]["error"] = "timeout"; bad_cases.append(bad)
        bad = copy.deepcopy(good); bad["results"][0]["resolved"] = "false"; bad_cases.append(bad)
        for bad in bad_cases:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                paired_gate(good, bad)

    def test_invalid_rule_and_alpha(self):
        for kwargs in [{"acceptance_rule": "unknown"}, {"alpha": 0}, {"alpha": math.nan}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                gate_from_vectors({("x", "1"): False}, {("x", "1"): True}, **kwargs)


class ConfirmationTests(unittest.TestCase):
    def test_majority_differs_from_episode_mean(self):
        # Candidate wins the episode average (4/9 vs 3/9) but ties the majority gate.
        base = [[True, False, False]] * 3
        cand = [[True, True, False], [False, False, True], [False, True, False]]
        initial_a, initial_b = summary(base[0]), summary(cand[0])
        rows = [{"domain": "example", "task_id": str(i)} for i in range(3)]
        calls = []

        def rerun(requested, side, attempt):
            self.assertEqual(requested, rows)
            calls.append((side, attempt))
            return summary((base if side == "baseline" else cand)[attempt + 1])

        gate, receipt = confirm_gate(paired_gate(initial_a, initial_b, acceptance_rule="net_improvement"),
                                     initial_a, initial_b, rows, rerun)
        self.assertEqual(calls, [("candidate", 0), ("baseline", 0), ("baseline", 1), ("candidate", 1)])
        self.assertFalse(gate["accepted"])
        self.assertEqual(gate["net_gains"], 0)
        self.assertGreater(receipt["mean_success_rate"]["candidate"], receipt["mean_success_rate"]["baseline"])
        self.assertEqual(len(receipt["tasks"]["example|0"]["votes"]["baseline"]), 3)

    def test_incomplete_repeat_rejected(self):
        a = summary([False])
        rows = [{"domain": "example", "task_id": "0"}]
        def rerun(*args):
            result = summary([True]); result["complete"] = False; return result
        with self.assertRaises(ValueError):
            confirm_gate(paired_gate(a, a), a, a, rows, rerun)

    def test_initial_gate_recomputed_and_no_reruns(self):
        a = summary([False])
        gate, _ = confirm_gate({"accepted": True, "acceptance_rule": "net_improvement"},
                               a, a, [{"domain": "example", "task_id": "0"}], None, reruns=0)
        self.assertFalse(gate["accepted"])

    def test_even_total_vote_count_rejected(self):
        a = summary([False])
        with self.assertRaises(ValueError):
            confirm_gate(paired_gate(a, a), a, a, [], None, reruns=1)


class SchedulingTests(unittest.TestCase):
    def test_probabilities_seed_and_cost(self):
        p = Bandit(["data", "harness", "model"])
        p.update("data", 1, 10)
        probs = p.probabilities(["data", "harness", "model"])
        self.assertAlmostEqual(sum(probs.values()), 1)
        self.assertTrue(all(v >= 0.15 / 3 for v in probs.values()))
        self.assertEqual(p.choose(7, ["data", "harness"]), p.choose(7, ["data", "harness"]))
        self.assertAlmostEqual(p.update("harness", 0, 10), -0.02)

    def test_state_is_not_aliased(self):
        state = {"data": {"count": 1, "mean_reward": 0.5}}
        p = Bandit(["data"], state=state)
        p.update("data", 0, 0)
        self.assertEqual(state["data"]["count"], 1)
        exposed = p.state; exposed["data"]["count"] = 999
        self.assertEqual(p.state["data"]["count"], 2)

    def test_invalid_policy_inputs(self):
        for settings in [{"bandit_softmax_temp": 0}, {"bandit_uniform_floor": 2}, {"bandit_bonus": math.nan}]:
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                Bandit(["data"], scheduler=settings)
        for eligible in [[], ["missing"], ["data", "data"]]:
            with self.subTest(eligible=eligible), self.assertRaises(ValueError):
                Bandit(["data"]).probabilities(eligible)

    def test_adversarial_proposal_cannot_monopolize_attempts(self):
        names = ["data", "harness", "model"]
        policy, history = Bandit(names), []
        limits = {"window": 6, "max_per_window": 3, "max_consecutive": 2, "max_count_gap": 2}
        for i in range(90):
            op = select({}, policy, names, i, None,
                        proposer=lambda _: {"operator": "data", "reason": "always"},
                        scheduler_policy={"mix_llm": 1}, history=history, balance=limits)
            history.append({"operator": op})
            policy.update(op, 100 if op == "data" else 0, 0)
            counts = [sum(row["operator"] == name for row in history) for name in names]
            self.assertLessEqual(max(counts) - min(counts), 2)

    def test_ineligible_action_and_invalid_proposal(self):
        with tempfile.TemporaryDirectory() as folder:
            receipt = Path(folder) / "selection.json"
            policy = Bandit(["data", "harness", "model"])
            history = [{"operator": "data"}, {"operator": "harness"}]
            op = select({}, policy, ["data", "harness"], 0, receipt,
                        proposer=lambda _: {"operator": "model"}, history=history)
            self.assertIn(op, ["data", "harness"])
            self.assertEqual(json.loads(receipt.read_text())["source"], "bandit_fallback_after_invalid_llm")
            op = select({}, policy, ["data", "harness", "model"], 0, receipt, history=history)
            self.assertEqual(op, "model")

    def test_single_action_relaxation_recorded(self):
        with tempfile.TemporaryDirectory() as folder:
            receipt = Path(folder) / "selection.json"
            select({}, Bandit(["data"]), ["data"], 0, receipt,
                   history=[{"operator": "data"}] * 5,
                   balance={"window": 6, "max_per_window": 3, "max_consecutive": 2})
            self.assertIn("relaxation", json.loads(receipt.read_text())["balance"])


class DemoTests(unittest.TestCase):
    def test_replay_artifacts_and_repeatability(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            result = run(a)
            self.assertEqual(result, run(b))
            self.assertEqual([r["operator"] for r in result["history"][:3]], ["data", "harness", "model"])
            self.assertEqual([r["accepted"] for r in result["history"][:3]], [True, False, False])
            self.assertEqual(len(list(Path(a).rglob("confirmation.json"))), 6)


if __name__ == "__main__":
    unittest.main()
