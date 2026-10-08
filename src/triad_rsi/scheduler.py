"""Operator selection: LLM suggestion mixed 50/50 with bandit probabilities.

If the LLM proposal is invalid (unknown operator / not eligible / malformed),
we fall back to the bandit's choice and mark it — never silently pretend the
model made a legal decision.
"""
import random

from .io import write_json



def select(diagnosis, policy, eligible, seed, output, proposer=None,
           scheduler_policy=None, history=None, max_gap=6, balance=None, experience=None):
    if len(set(eligible)) != len(eligible) or not set(eligible) <= set(policy.state):
        raise ValueError("Eligible operators must be unique and known")
    if not eligible:
        raise ValueError('No eligible operators')
    if isinstance(max_gap, bool) or not isinstance(max_gap, int) or max_gap < len(eligible):
        raise ValueError('operator_max_gap must be an integer >= eligible operator count')
    if balance:
        limits = [balance.get(k) for k in ('window', 'max_per_window', 'max_consecutive')]
        if any(type(v) is not int or v < 1 for v in limits) or limits[1] > limits[0]:
            raise ValueError('Invalid operator balance limits')
    history = history or []
    # Count attempts, including rejected candidates. Acceptance is never a
    # scheduling quota. Restrict to currently legal operators: an unqualified
    # model operator must not prevent the others from making progress.
    attempt_counts = {op: sum(row.get('operator') == op for row in history)
                      for op in eligible}
    count_balance = {'eligible': list(eligible), 'attempt_counts': attempt_counts}
    count_gap = balance.get('max_count_gap') if balance else None
    if count_gap is not None:
        if type(count_gap) is not int or count_gap < 1:
            raise ValueError('operator balance max_count_gap must be a positive integer')
        minimum = min(attempt_counts.values())
        eligible = [op for op in eligible
                    if attempt_counts[op] < minimum + count_gap]
        count_balance.update({'max_count_gap': count_gap,
                              'permitted': list(eligible),
                              'reason': 'bound cumulative attempt imbalance among eligible operators'})
    last = {op: max((i for i, row in enumerate(history)
                     if row.get('operator') == op), default=-1) for op in eligible}
    unseen = [op for op in eligible if last[op] < 0]
    overdue = [op for op in eligible if len(history) - last[op] >= max_gap]
    forced = unseen or overdue
    if forced:
        chosen = min(forced, key=lambda op: (last[op], eligible.index(op)))
        write_json(output, {'operator': chosen, 'source': 'coverage_guard',
                            'last_selected': last, 'max_gap': max_gap,
                            'eligible': list(eligible),
                            'count_balance': count_balance,
                            'coverage_reason': 'unseen' if unseen else 'overdue'})
        return chosen
    # Immutable experiment constraints bound concentration; rewards still decide
    # among the remaining choices. Coverage takes precedence over these caps.
    original_eligible = list(eligible)
    balance_record = {'eligible': original_eligible, 'excluded': {}}
    if balance:
        window = balance['window']
        cap = balance['max_per_window']
        consecutive = balance['max_consecutive']
        recent = history[-(window - 1):] if window > 1 else []
        counts = {op: sum(row.get('operator') == op for row in recent)
                  for op in eligible}
        streak = 0
        previous = history[-1].get('operator') if history else None
        for row in reversed(history):
            if row.get('operator') != previous:
                break
            streak += 1
        permitted = []
        for op in eligible:
            reasons = []
            if counts[op] >= cap:
                reasons.append('window_share')
            if op == previous and streak >= consecutive:
                reasons.append('consecutive_limit')
            if reasons:
                balance_record['excluded'][op] = reasons
            else:
                permitted.append(op)
        # Changing eligibility may make all caps infeasible. Do not deadlock:
        # restore the least represented legal choices and explicitly record it.
        if not permitted:
            minimum = min(counts.values())
            permitted = [op for op in eligible if counts[op] == minimum]
            balance_record['relaxation'] = 'no choice satisfies caps; least represented eligible'
        eligible = permitted
        balance_record.update({'counts': counts, 'limits': balance,
                               'permitted': list(eligible)})
    probs = policy.probabilities(eligible)
    mix_llm = 0.5
    if scheduler_policy is not None:
        mix_llm = float(scheduler_policy.get('mix_llm', 0.5))
    if not 0 <= mix_llm <= 1:
        raise ValueError('mix_llm must be in [0, 1]')
    suggestion = None
    try:
        payload = {'diagnosis': {'counts': diagnosis.get('counts'),
                                 'summary': diagnosis.get('summary')},
                   'bandit_probabilities': probs, 'eligible': eligible,
                   'recent_experiments': experience or [],
                   'experience_scope': 'adaptive selection outcomes; not causal proof'}
        value = proposer(payload) if proposer is not None else {}
        if not isinstance(value, dict):
            raise ValueError('Proposal must be a dictionary')
        if value.get('operator') in eligible:
            suggestion = value
    except ValueError:
        suggestion = None
    rng = random.Random(seed)
    if suggestion and rng.random() < mix_llm:
        chosen, source = suggestion['operator'], 'llm'
    else:
        chosen, probs = policy.choose(seed, eligible)
        source = 'bandit' if suggestion else 'bandit_fallback_after_invalid_llm'
    write_json(output, {'operator': chosen, 'source': source,
                        'probabilities': probs, 'llm_suggestion': suggestion,
                        'balance': balance_record,
                        'count_balance': count_balance})
    return chosen
