"""Assess native-produced S3 outcomes, not source-text presence."""
import json,sys
from pathlib import Path
variant=sys.argv[1]
result=json.loads((Path(__file__).parent/(variant+'-output.json')).read_text())
cases={case['id']:case for case in result['cases']}
failures=[]
for name in ['S3-undeclared','S3-git-path','S3-missing','S3-stale']:
 case=cases[name]
 if case['implementation_eligible'] or case['initial_envelope']['analyze']['high']<1:
  failures.append(name+': required HIGH/block missing')
for name in ['S3-add','S3-remove','S3-rename','S3-expand','S3-protected']:
 case=cases[name];env=case['initial_envelope']
 if env['status']!='needs_input' or case['implementation_eligible'] or not env['questions'] or not all(q.get('requires_user') for q in env['questions']):
  failures.append(name+': protected confirmation missing')
for name in ['S3-covered','S3-exempt']:
 if not cases[name]['implementation_eligible']:failures.append(name+': eligible control blocked')
case=cases['S3-protected']
reply=case.get('explicit_reply_continuation') or case['after_explicit_reply']
if not reply['implementation_eligible']:failures.append('explicit acceptance did not permit continuation')
print('S3-failure-scope-acceptance:', 'PASS' if not failures else 'FAIL', '; '.join(failures))
sys.exit(bool(failures))
