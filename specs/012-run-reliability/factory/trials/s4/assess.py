"""Assess observed native boundary decisions; no source-text assertions."""
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())
cases = {case['id']: case for case in report['cases']}
pending = cases['S4-pending']['final_envelope']
assert pending['status'] == 'partial', 'S4-required-check-admission: known broad check cannot fit existing-role boundary'
assert pending.get('pending_checks'), 'mandatory checks must remain explicit across handoff'
assert 'python3 probe.py' not in pending.get('completed_checks', []), 'unrun required checks cannot be claimed complete'
assert not pending.get('overrun'), 'pre-deadline fit handoff cannot claim an overrun'
for name in ('S4-optional', 'S4-uncertain'):
    case = cases[name]
    assert case['final_envelope']['status'] == 'done'
    commands = case.get('chosen_commands', case.get('commands', []))
    assert not any('probe.py' in str(command.get('argv', command.get('command', ''))) for command in commands)
inflight = cases['S4-inflight']
assert inflight['final_envelope']['status'] == 'partial'
assert inflight['final_envelope'].get('overrun'), 'actual in-flight overshoot remains visible'
print('S4-required-check-admission: passed; optional and in-flight controls preserved')
