"""Paired candidate acceptance on selection data only; audit/test never select.

Reports exact one-sided McNemar statistics on discordant pairs. The immutable
run configuration selects significance or net_improvement acceptance. Both
raw and confirmed vectors use the same rule; p remains descriptive in the
improvement-first mode. Audit/test outcomes never enter candidate selection.
"""
import math


def paired_gate(baseline, candidate, alpha=0.1, acceptance_rule="significance"):
    if baseline.get('complete') is not True or candidate.get('complete') is not True:
        raise ValueError('Cannot gate on incomplete evaluation')
    left = {(r['domain'], r['task_id']): r for r in baseline['results']}
    right = {(r['domain'], r['task_id']): r for r in candidate['results']}
    if len(left) != len(baseline['results']) or len(right) != len(candidate['results']):
        raise ValueError('Duplicate task results')
    if any(row.get('error') for row in baseline['results'] + candidate['results']):
        raise ValueError('Execution errors cannot enter the gate')
    if not left or set(left) != set(right):
        raise ValueError('A/B tasks must be exactly paired')
    return gate_from_vectors(left, right, alpha=alpha, acceptance_rule=acceptance_rule)


def gate_from_vectors(left, right, alpha=0.1, acceptance_rule="significance"):
    """left/right: {task_key: {'resolved': bool, ...}, ...}, exactly paired.

    Accepts either full result rows (as produced by runner.evaluate) or bare
    booleans. net_improvement accepts strictly positive net gains; significance
    additionally requires exact one-sided p <= alpha. The run fixes the rule.
    """
    if not left or set(left) != set(right):
        raise ValueError('A/B tasks must be exactly paired')

    if acceptance_rule not in ('significance', 'net_improvement'):
        raise ValueError(f'Unknown acceptance rule: {acceptance_rule}')

    if not 0 < alpha < 1:
        raise ValueError('Alpha must be in (0, 1)')

    def resolved(entry):
        value = entry if isinstance(entry, bool) else entry['resolved']
        if type(value) is not bool:
            raise ValueError('Resolved outcomes must be booleans')
        return value

    gains = sum(not resolved(left[k]) and resolved(right[k]) for k in left)
    regressions = sum(resolved(left[k]) and not resolved(right[k]) for k in left)
    discordant = gains + regressions
    p = (sum(math.comb(discordant, k) for k in range(gains, discordant + 1))
         / 2 ** discordant if discordant else 1.0)
    by_domain = {}
    for k in left:
        slot = by_domain.setdefault(k[0], {'gains': 0, 'regressions': 0})
        slot['gains'] += int(not resolved(left[k]) and resolved(right[k]))
        slot['regressions'] += int(resolved(left[k]) and not resolved(right[k]))
    accepted = gains > regressions and (acceptance_rule == 'net_improvement' or p <= alpha)
    return {'accepted': accepted,
            'acceptance_rule': acceptance_rule,
            'p_value_is_gate': acceptance_rule == 'significance',
            'net_gains': gains - regressions,
            'baseline_resolved': sum(resolved(v) for v in left.values()),
            'candidate_resolved': sum(resolved(v) for v in right.values()),
            'total': len(left),
            'gains': gains, 'regressions': regressions, 'paired_one_sided_p': p,
            'alpha': alpha, 'delta': (gains - regressions) / len(left),
            'by_domain': by_domain,
            'note': 'Selection evidence only; repeated adaptive tests are not a '
                    'held-out significance claim.'}
