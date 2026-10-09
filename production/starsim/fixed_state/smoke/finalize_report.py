"""File-only final accounting; does not import or run any simulator."""
from pathlib import Path
import json,hashlib,re
O=Path(__file__).resolve().parent
read=lambda n:json.loads((O/n).read_text())
ledger=read('trajectory_ledger.json');assert len(ledger)==70
for p,h in read('inputs.json').items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
old=json.loads((O.parent/'manifest.json').read_text())
for p,h in old.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
fix=read('coverage_fix/RESULT.json');assert fix['total_budget_used']==70
checks={str(p.relative_to(O)):len(json.loads(p.read_text())) for p in [O/'checks.json',O/'extended/checks.json',O/'coverage_fix/checks.json',*O.glob('worker_*/checks.json')]}
status=dict(status='PARTIAL_VALIDATION_BLOCKED_BEFORE_PRODUCTION',trajectories=70,production_ready=False,
 verified=['historical cached trajectory recreation','displayed C20/I20','pause/resume','deepcopy and unshrunk serialization','future multistream reseeding without prefix/latent-state changes','three negative RNG controls','two corrected treatment branches in w2'],
 invalidated=['24 fractional branches in initial grid delivered zero vaccine','nominal treated process repeats were zero-dose','nominal treated 40-day pairing test was zero-dose'],
 cause='Smoke harness initialized campaign probability with integer zero; in-place fractional assignments truncated to zero. Earlier checks passed vacuously.',
 correction='Replace probability array with float dtype; exact dose and nonempty uptake checks. Verified only for w2/r0 c25 and c90.',
 next_approval='36-start corrected validation grid and treated process/daywise pairing, not production',
 checks_by_file=checks,automated_assertions_passed_but_not_equivalent_to_scientific_validation=sum(checks.values()),
 input_hashes_verified=len(read('inputs.json')),prior_audit_input_hashes_verified=len(old),fix_results=fix['results'])
(O/'VALIDATION_STATUS.json').write_text(json.dumps(status,indent=2))
for target in re.findall(r'\]\((/[^)]+)\)',(O/'REPORT.md').read_text()):
 p,sep,line=target.rpartition(':')
 if not(sep and line.isdigit()):p=target;line=None
 assert Path(p).exists(),target
 if line:assert int(line)<=len(Path(p).read_text().splitlines()),target
files=[p for p in O.rglob('*') if p.is_file() and not any(k in p.parts for k in ['uv-cache','numba-cache','mpl']) and p.name!='artifact_manifest.json']
(O/'artifact_manifest.json').write_text(json.dumps({str(p.relative_to(O)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
print('70 starts; no further simulations. Authoritative status:',status['status'])
print('All',len(read('inputs.json')),'feasibility-source and',len(old),'prior-audit input hashes unchanged; report links validated.')
