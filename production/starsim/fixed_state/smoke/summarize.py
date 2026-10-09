"""Summarize already-recorded validation; no Starsim import or simulation."""
import json,csv,hashlib,statistics,re
from pathlib import Path
O=Path(__file__).resolve().parent
read=lambda n:json.loads((O/n).read_text())
main=read('SUCCESS.json');ext=read('extended/SUCCESS.json');timings=read('timings.json');roots=read('streams.json');out=read('outcomes.json');ledger=read('trajectory_ledger.json')
checks={}
for p in [O/'checks.json',O/'extended/checks.json',*O.glob('worker_*/checks.json')]:
 c=json.loads(p.read_text());assert all(r['pass_'] for r in c);checks[str(p.relative_to(O))]=len(c)
assert len(ledger)==68
for p,h in read('inputs.json').items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p

def stats(values):return dict(n=len(values),min=min(values),median=statistics.median(values),mean=statistics.mean(values),max=max(values))
groups={}
for label,prefix in [('historical90','full90 '),('prefix20','prefix20 '),('resume90','resume90 '),('continuation40','continuation21to60 branch'),('branch_copy','deepcopy branch'),('pair_copy','deepcopy paired'),('reseed_including_checks','reseed '),('save','save '),('load','load '),('fresh_worker','worker_spawn_load_branch ')]:
 groups[label]=stats([r['seconds'] for r in timings if r['task'].startswith(prefix)])
first=timings[0]['seconds'];groups['historical90_warm']=stats([r['seconds'] for r in timings if r['task'].startswith('full90 ')][1:])
seeds=[v['seed'] for r in roots for v in r['streams'].values()];hs=[v['root'] for r in roots for v in r['streams'].values()]
assert len(set(seeds))==len(seeds) and len(set(hs))==len(hs)
comparison=[]
for w in ['w0','w1','w2','w3']:
 for cov in [0,.25,.5,.9]:
  a=next(r for r in out if r['label']==f'branch {w} r0 c{cov}');b=next(r for r in out if r['label']==f'branch {w} r1 c{cov}')
  comparison.append(dict(world=w,coverage=cov,rep0_day40=a['new40'],rep0_day60=a['new60'],rep1_day40=b['new40'],rep1_day60=b['new60'],different_trajectory=a['trajectory']!=b['trajectory'],different_final_physical=a['final']!=b['final']))
with (O/'sample_outcomes.csv').open('w') as f:
 wr=csv.DictWriter(f,fieldnames=comparison[0]);wr.writeheader();wr.writerows(comparison)
branch_unit=groups['continuation40']['mean']+groups['branch_copy']['mean']+(groups['pair_copy']['mean']+groups['reseed_including_checks']['mean'])/4
estimates={str(n):dict(branches=16*n,simulation_copy_reseed_seconds=16*n*branch_unit,serial_minutes=16*n*branch_unit/60) for n in [300,1000]}
summary=dict(trajectories=len(ledger),assertions=checks,total_assertions=sum(checks.values()),input_hashes_verified=len(read('inputs.json')),distribution_count_per_snapshot=len(roots[0]['streams']),unique_root_hashes=len(set(hs)),unique_distribution_seeds=len(set(seeds)),new_independent_replicate_sets=len(roots),outcome_pairs_different=sum(r['different_trajectory'] for r in comparison),outcome_pairs_tested=len(comparison),timings_s=groups,branch_unit_s=branch_unit,estimates=estimates,snapshot_bytes=read('snapshot_sizes.json'),snapshots_total_bytes=sum(r['bytes'] for r in read('snapshot_sizes.json')),main_import_seconds=main['import_s'],main_active_wall_seconds=main['completed']-ledger[0]['started'],peak_main_rss_bytes=main['max_rss_bytes'])
(O/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
files=[p for p in O.rglob('*') if p.is_file() and not any(t in p.parts for t in ['uv-cache','numba-cache','mpl']) and p.name!='artifact_manifest.json']
(O/'artifact_manifest.json').write_text(json.dumps({str(p.relative_to(O)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
