"""Paired repeated evaluation with auditable votes and strict task coverage.

Full mode repeats every task, including initial agreements. The legacy
'discordant' mode is explicit and reports its mixed repetition coverage.
P-values remain descriptive when acceptance_rule is net_improvement.
"""
from .io import write_json
from . import gate as evaluator


def _vector(summary):
    if summary.get('complete') is not True:
        raise ValueError('Incomplete evaluation cannot enter confirmation')
    rows = summary['results']
    if any(row.get('error') for row in rows):
        raise ValueError('Execution errors cannot enter confirmation votes')
    if any(type(row.get('resolved')) is not bool for row in rows):
        raise ValueError('Resolved outcomes must be booleans')
    result = {(r['domain'], str(r['task_id'])): bool(r['resolved']) for r in rows}
    if len(result) != len(rows):
        raise ValueError('Duplicate evaluation task results')
    return result


def _majority(votes):
    return sum(votes) * 2 > len(votes)


def confirm_gate(raw_gate, baseline, candidate, rows, rerun, output=None,
                 reruns=2, scope='full'):
    if scope not in ('full', 'discordant'):
        raise ValueError('Unknown confirmation scope')
    if type(reruns) is not int or reruns < 0 or reruns % 2:
        raise ValueError('Confirmation reruns must be a nonnegative even integer')
    left, right = _vector(baseline), _vector(candidate)
    rows_by_key = {(r['domain'], str(r['task_id'])): r for r in rows}
    if not left or left.keys() != right.keys() or left.keys() != rows_by_key.keys() or len(rows_by_key) != len(rows):
        raise ValueError('Paired evaluation must cover exactly the requested tasks')
    raw_gate = evaluator.gate_from_vectors(
        left, right, alpha=raw_gate.get('alpha', 0.1),
        acceptance_rule=raw_gate.get('acceptance_rule', 'significance'))
    discordant = sorted(k for k in left if left[k] != right[k])
    selected = sorted(left) if scope == 'full' else discordant
    record = {'reruns': reruns, 'scope': scope, 'discordant': len(discordant),
              'repeated_tasks': len(selected) if reruns else 0,
              'total_tasks': len(left), 'tasks': {}, 'execution_order': []}
    if not selected or not reruns:
        record.update(final_gate=raw_gate, note='No additional repeats; gate unchanged')
        if output:
            write_json(output, record)
        return raw_gate, record
    votes = {side: {k: [vector[k]] for k in selected}
             for side, vector in [('baseline', left), ('candidate', right)]}
    output_tokens = 0
    measurements = [{'attempt': 'initial', 'baseline_resolved': sum(left.values()),
                     'candidate_resolved': sum(right.values()),
                     'net_gains': sum(right.values()) - sum(left.values())}]
    for attempt in range(reruns):
        measured = {}
        # Counterbalance arm order across repeats; paths/attempt IDs stay stable.
        order = ('candidate', 'baseline') if attempt % 2 == 0 else ('baseline', 'candidate')
        for side in order:
            summary = rerun([rows_by_key[k] for k in selected], side, attempt)
            vector = _vector(summary)
            if set(vector) != set(selected):
                raise ValueError('Confirmation result missing or unexpected tasks')
            output_tokens += summary.get('output_tokens') or 0
            measured[side] = sum(vector.values())
            record['execution_order'].append({'attempt': attempt, 'side': side})
            for k in selected:
                votes[side][k].append(vector[k])
        measurements.append({'attempt': attempt, 'baseline_resolved': measured['baseline'],
                             'candidate_resolved': measured['candidate'],
                             'net_gains': measured['candidate'] - measured['baseline']})
    verified_left, verified_right = dict(left), dict(right)
    for k in selected:
        verified_left[k] = _majority(votes['baseline'][k])
        verified_right[k] = _majority(votes['candidate'][k])
        record['tasks']['|'.join(k)] = {
            'raw': {'baseline': left[k], 'candidate': right[k]},
            'votes': {side: votes[side][k] for side in votes},
            'verified': {'baseline': verified_left[k], 'candidate': verified_right[k]}}
    final = evaluator.gate_from_vectors(verified_left, verified_right,
                                        alpha=raw_gate.get('alpha', 0.1),
                                        acceptance_rule=raw_gate.get('acceptance_rule', 'significance'))
    record.update(final_gate=final, raw_gate=raw_gate, output_tokens=output_tokens,
                  measurements=measurements)
    if scope == 'full':
        record['mean_success_rate'] = {side: sum(m[side + '_resolved'] for m in measurements) /
                                      ((1 + reruns) * len(left)) for side in votes}
    record['note'] = (f'{scope} confirmation: majority over {1 + reruns} runs on '
                      f'{len(selected)} tasks; p follows configured acceptance rule. '
                      'Adaptive selection evidence, not held-out generalization.')
    if output:
        write_json(output, record)
    return final, record
