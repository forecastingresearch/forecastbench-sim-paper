"""File-only accounting and analytic Monte Carlo precision; no simulation imports."""
import csv,json,math,statistics,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent
read=lambda n:json.loads((O/n).read_text())
r=read('RESULT.json');assert r['status']=='PASS' and r['trajectories']==36
assert len(read('ledger.json'))==36
rows=[x for x in read('outcomes.json') if x['label'].startswith('grid ')]
assert len(rows)==32
assert all(x['administration']['dtype']=='float64' and x['administration']['actual']==x['administration']['expected'] and len(x['administration']['eligible'])==5000 and (x['administered']==0 if x['coverage']==0 else x['administered']>0) for x in rows)
with (O/'grid.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['world','rep','coverage','administered','new40','new60','simulation_seconds']);w.writeheader();w.writerows({k:x[k] for k in w.fieldnames} for x in rows)
counts={str(p.relative_to(O)):len(json.loads(p.read_text())) for p in [O/'checks.json',*O.glob('worker_*/checks.json')]}
for p in counts:assert all(c['pass_'] for c in read(p))
def stats(a):return dict(n=len(a),min=min(a),mean=statistics.mean(a),median=statistics.median(a),max=max(a))
timings=read('timings.json');ts={}
for name,prefix in [('grid_continuation','simulation21to60 grid'),('grid_copy','deepcopy grid'),('pair_load','load pair'),('pair_copy','deepcopy pair'),('pair_reseed','reseed pair'),('worker_total','worker_total')]:ts[name]=stats([x['seconds'] for x in timings if x['task'].startswith(prefix)])
uptake={str(c):dict(n_runs=sum(x['coverage']==c for x in rows),min=min(x['administered'] for x in rows if x['coverage']==c),max=max(x['administered'] for x in rows if x['coverage']==c)) for c in [0,.25,.5,.9]}
unit=ts['grid_continuation']['mean']+ts['grid_copy']['mean']+(ts['pair_load']['mean']+ts['pair_copy']['mean']+ts['pair_reseed']['mean'])/4
precision=[]
for n in [300,1000]:
 precision.append(dict(continuations_per_world=n,independent_world_replicate_sets=4*n,branches=16*n,expected_lower_decile_count=.1*n,median_cdf_se=math.sqrt(.25/n),median_cdf_95_margin=1.96*math.sqrt(.25/n),decile_cdf_se=math.sqrt(.09/n),decile_cdf_95_margin=1.96*math.sqrt(.09/n),dkw_95_one_distribution=math.sqrt(math.log(40)/(2*n)),dkw_95_all32_distributions=math.sqrt(math.log(1280)/(2*n)),serial_minutes_estimate=16*n*unit/60))
with (O/'precision.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=precision[0]);w.writeheader();w.writerows(precision)
for p,h in read('inputs.json').items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
summary=dict(status='PASS',new_trajectories=36,total_audit_trajectory_starts=106,checks_by_file=counts,total_assertions=sum(counts.values()),inputs_verified=len(read('inputs.json')),uptake=uptake,timing_s=ts,instrumented_branch_unit_s=unit,production_precision=precision,total_elapsed_s=r['elapsed_s'],import_s=r['import_s'],active_s=r['elapsed_s']-r['import_s'],peak_rss_bytes=r['max_rss_bytes'])
(O/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
