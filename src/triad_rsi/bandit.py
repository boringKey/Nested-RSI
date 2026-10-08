"""Cost-aware softmax-UCB operator policy, extracted from the research prototype."""
import math
import random

BONUS = 0.12          # exploration bonus coefficient
SOFTMAX_TEMP = 0.15   # softmax temperature
UNIFORM_FLOOR = 0.15  # uniform-mix floor coefficient


class Bandit:
    def __init__(self, names, state=None, scheduler=None):
        names = list(names)
        if not names or len(set(names)) != len(names):
            raise ValueError("Action names must be nonempty and unique")
        self.actions = {name: {'count': 0, 'mean_reward': 0.0} for name in names}
        if state:
            if set(state) != set(names):
                raise ValueError("State must contain exactly the named actions")
            for stats in state.values():
                if type(stats.get("count")) is not int or stats["count"] < 0 or not math.isfinite(stats.get("mean_reward", float("nan"))):
                    raise ValueError("Invalid action statistics")
            self.actions.update({name: dict(stats) for name, stats in state.items()})
        s = scheduler or {}
        self.bonus = float(s.get('bandit_bonus', BONUS))
        self.softmax_temp = float(s.get('bandit_softmax_temp', SOFTMAX_TEMP))
        self.uniform_floor = float(s.get('bandit_uniform_floor', UNIFORM_FLOOR))

        if not math.isfinite(self.bonus) or self.bonus < 0:
            raise ValueError("Bonus must be finite and nonnegative")
        if not math.isfinite(self.softmax_temp) or self.softmax_temp <= 0:
            raise ValueError("Temperature must be positive and finite")
        if not 0 <= self.uniform_floor <= 1:
            raise ValueError("Uniform floor must be in [0, 1]")

    @property
    def state(self):
        return {name: dict(stats) for name, stats in self.actions.items()}

    def probabilities(self, eligible):
        if not eligible or len(set(eligible)) != len(eligible) or not set(eligible) <= set(self.actions):
            raise ValueError("Eligible actions must be nonempty, unique, and known")
        total = sum(self.actions[name]['count'] for name in eligible)
        scores = {}
        for name in eligible:
            stats = self.actions[name]
            bonus = self.bonus * math.sqrt(
                math.log(total + 2) / (stats['count'] + 1))
            scores[name] = stats['mean_reward'] + bonus
        top = max(scores.values())
        temp = self.softmax_temp
        weights = {name: math.exp((score - top) / temp)
                   for name, score in scores.items()}
        norm = sum(weights.values())
        n = len(eligible)
        floor = self.uniform_floor
        return {name: floor / n + (1.0 - floor) * weights[name] / norm
                for name in eligible}

    def choose(self, seed, eligible):
        rng = random.Random(seed)
        probs = self.probabilities(eligible)
        draw = rng.random()
        cumulative = 0.0
        for name in sorted(eligible):
            cumulative += probs[name]
            if draw <= cumulative:
                return name, probs
        return sorted(eligible)[-1], probs

    def update(self, name, performance_gain, cost_units, cost_weight=0.002):
        if not math.isfinite(cost_units) or cost_units < 0 or not math.isfinite(cost_weight) or cost_weight < 0:
            raise ValueError("Cost and cost weight must be finite and nonnegative")
        reward = performance_gain - cost_weight * cost_units
        if not math.isfinite(reward):
            raise ValueError('non-finite reward')
        stats = self.actions[name]
        stats['count'] += 1
        stats['mean_reward'] += (reward - stats['mean_reward']) / stats['count']
        return reward
