"""Fixed-plan paired production; atomic per-set checkpoints, no model calls."""
import os,sys,json,time,hashlib,gzip,collections,platform,resource
from pathlib import Path
O=Path(__file__).resolve().parent;A=O.parent
sys.path.insert(0,str(A/'corrected_smoke'))
import validate as v
q=v.q;np=v.np
COUNTS=collections.Counter()
def check(name,condition,detail=None):
 if not condition:raise AssertionError(name+': '+str(detail))
 COUNTS['passed']+=1
q.check=check
q.save=lambda *args:None
q.timed=lambda label,fn:fn()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,obj):
 temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(obj,indent=2,default=q.jsonable));os.replace(temp,p)
def freeze():
 assert not (O/'PLAN.json').exists(),'Plan already frozen'
 inputs=json.loads((A/'corrected_smoke/inputs.json').read_text())
 for f in ['smoke/smoke.py','corrected_smoke/validate.py','corrected_smoke/RESULT.json','corrected_smoke/artifact_manifest.json']:
  inputs[str(A/f)]=sha(A/f)
 for f in ['production.py','run.sh']:inputs[str(O/f)]=sha(O/f)
 for p,h in inputs.items():assert sha(Path(p))==h,p
 worlds=json.loads((q.R/'data/worlds/worlds_c90.json').read_text())['worlds']
 seeds=[dict(world=w['world_id'],rep=r,seed=int(np.random.SeedSequence([20260924,16000,i,r]).generate_state(1,dtype=np.uint64)[0])) for i,w in enumerate(worlds) for r in range(1000)]
 assert len({s['seed'] for s in seeds})==4000
 plan=dict(frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),N=1000,branches=16000,worlds=worlds,coverages=[0,.25,.5,.9],horizons=[40,60],seed_entropy=[20260924,16000,'world_index','rep'],seeds=seeds,estimand='Exact fixed day20 hidden state; independent future roots; common roots across arms',checkpoints=[100,300,500,1000],sampling_rule='Fixed N=1000; no stopping or tuning based on scores, ranks, ECI or ForecastBench',analysis=dict(normalization='Hold original paper C40/C60 fixed',quantiles='paper inverted_cdf',replay_bootstrap=1000,model_panel_bootstrap=2000,bootstrap_seed=2026092401,panels='Available matched complete model panels; no imputation; list memberships; bootstrap models separately from replay roots'),inputs=inputs,environment=dict(python=sys.version,starsim=q.ss.__version__,numpy=np.__version__,platform=platform.platform()))
 atomic(O/'PLAN.json',plan);(O/'PLAN.sha256').write_text(sha(O/'PLAN.json')+'\n');print('FROZEN',sha(O/'PLAN.json'),flush=True)
def run():
 start=time.time();assert sha(O/'PLAN.json')==(O/'PLAN.sha256').read_text().strip()
 plan=json.loads((O/'PLAN.json').read_text());assert q.ss.__version__=='3.3.4' and np.__version__=='2.5.2' and not q.ss.options.single_rng
 for p,h in plan['inputs'].items():assert sha(Path(p))==h,p
 D=O/'checkpoints';D.mkdir(exist_ok=True)
 worlds={w['world_id']:w for w in plan['worlds']};anchors={k:q.ss.load(A/'smoke'/(k+'.sim')) for k in worlds};fps={k:q.fingerprint(s) for k,s in anchors.items()}
 for k,s in anchors.items():
  q.boundary(s,k);assert int(q.ever(s)[0][20])==worlds[k]['c20']
 completed=0;donehash={};allroots=set();newsets=0
 for job in plan['seeds']:
  wid=job['world'];rep=job['rep'];p=D/f'{wid}_{rep:04d}.json.gz'
  if p.exists():
   with gzip.open(p,'rt') as f:r=json.load(f)
   assert r['job']==job and r['plan_sha256']==sha(O/'PLAN.json') and len(r['arms'])==4
  else:
   t=time.time();n0=COUNTS['passed'];w=worlds[wid];anchor=anchors[wid];paired=q.isolate_copy(anchor,f'{wid}/{rep}')
   roots=q.reseed(paired,job['seed'],f'{wid}/{rep}');fp=q.fingerprint(paired);rows=[]
   for cov in plan['coverages']:
    s=q.isolate_copy(paired,f'{wid}/{rep}/{cov}')
    row=v.execute(s,w,rep,cov,f'{wid}/{rep}/{cov}')
    assert q.fingerprint(paired)==fp and q.fingerprint(anchor)==fps[wid]
    rows.append(row);v.ROWS.clear();q.TIMINGS.clear()
   assert all(x['roots']==roots for x in rows)
   assert all(x['administration']['network']==rows[0]['administration']['network'] for x in rows)
   sets=[set(x['administration']['actual']) for x in rows];assert all(a<b for a,b in zip(sets,sets[1:]))
   for row in rows:
    adm=row['administration'];row['vaccinated_ids_sha256']=q.digest(adm['actual']);row['eligible_count']=len(adm['eligible']);row['day21_network']=adm['network']
    for key in ['administration','roots','path']:del row[key]
   r=dict(job=job,plan_sha256=sha(O/'PLAN.json'),roots=roots,arms=rows,checks=COUNTS['passed']-n0,elapsed_s=time.time()-t)
   temp=p.with_suffix('.tmp')
   with gzip.open(temp,'wt',compresslevel=6) as f:json.dump(r,f,default=q.jsonable)
   os.replace(temp,p);newsets+=1
  for root in r['roots'].values():
   assert root['root'] not in allroots,'Duplicate independent distribution root';allroots.add(root['root'])
  donehash[p.name]=sha(p);completed+=1
  if completed%25==0:print(json.dumps(dict(completed_sets=completed,branches=4*completed,new_sets=newsets,elapsed_s=time.time()-start)),flush=True)
  if completed%100==0:atomic(O/'PROGRESS.json',dict(completed_sets=completed,branches=4*completed,new_sets=newsets,elapsed_s=time.time()-start))
 assert completed==4000 and len(allroots)==40000
 for p,h in plan['inputs'].items():assert sha(Path(p))==h,p
 atomic(O/'checkpoint_hashes.json',donehash)
 atomic(O/'SUCCESS.json',dict(sets=completed,branches=4*completed,distinct_distribution_roots=len(allroots),new_sets_this_invocation=newsets,elapsed_s_this_invocation=time.time()-start,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
 print('SUCCESS',flush=True)
if __name__=='__main__':
 try:freeze() if '--freeze' in sys.argv else run()
 except Exception:
  import traceback
  atomic(O/f'FAILURE_{int(time.time())}.json',dict(traceback=traceback.format_exc()));raise
