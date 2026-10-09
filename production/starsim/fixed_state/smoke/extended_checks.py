"""Three additional bounded controls; cumulative ledger cannot exceed 70.
This does not launch the main suite again. Requires its successful completion.
"""
import json,time
from pathlib import Path
import numpy as np
import smoke as q
P=Path(__file__).resolve().parent
assert (P/'SUCCESS.json').exists()
if (P/'extended/SUCCESS.json').exists():raise RuntimeError('Extended controls already completed')
q.O=P/'extended';q.O.mkdir(exist_ok=True)

def claim(label):
    ledger=json.loads((P/'trajectory_ledger.json').read_text());assert len(ledger)<70
    ledger.append(dict(n=len(ledger)+1,label=label,started=time.time(),pid=__import__('os').getpid()))
    (P/'trajectory_ledger.json').write_text(json.dumps(ledger,indent=2));print(label,flush=True)

def main():
    worlds=json.loads((q.R/'data/worlds/worlds_c90.json').read_text())['worlds'];w=worlds[2];anchor=q.ss.load(P/'w2.sim');fixed=q.fingerprint(anchor)
    seed=int(np.random.SeedSequence([20260923,2,0]).generate_state(1,dtype=np.uint64)[0])
    paired=q.isolate_copy(anchor,'allstep pair');q.reseed(paired,seed,'allstep pair')
    paths={};measurements=[]
    original=json.loads((P/'outcomes.json').read_text())
    for cov in [0,.9]:
        label='allstep w2 c'+str(cov);claim(label);s=q.isolate_copy(paired,label);q.campaign(s).prob[:]=cov
        prefix=q.history(s);infected=q.sir(s).infected.raw.copy();recover=q.sir(s).ti_recovered.raw.copy();root=q.roots(s);path=[]
        for day in range(21,61):
            before=q.digest(np.random.get_state());t=time.perf_counter();s.run(until=2000+day);measurements.append(dict(coverage=cov,day=day,seconds=time.perf_counter()-t))
            q.check(label+f' d{day} global RNG unchanged',before==q.digest(np.random.get_state()))
            q.check(label+f' d{day} prefix fixed',prefix==q.history(s))
            q.check(label+f' d{day} old recovery schedule fixed',np.array_equal(q.sir(s).ti_recovered.raw[infected],recover[infected],equal_nan=True))
            q.check(label+f' d{day} root hashes fixed',all(root[k]['root']==v['root'] for k,v in q.roots(s).items()))
            path.append(dict(day=day,network={k:q.harray(v) for k,v in next(iter(s.networks.values())).edges.items()},rng=q.roots(s)))
        e,_=q.ever(s);ref=next(r for r in original if r['label']==f'branch w2 r0 c{cov}')
        q.check(label+' equals single continuation',q.hashlib.sha256(np.asarray(e[:61]).tobytes()).hexdigest()==ref['trajectory'])
        paths[str(cov)]=path
    q.check('common network on all 40 days',all(a['network']==b['network'] for a,b in zip(paths['0'],paths['0.9'])))
    q.check('common network generator state all 40 days',all(a['rng']['networks_randomnet_dist']==b['rng']['networks_randomnet_dist'] for a,b in zip(paths['0'],paths['0.9'])))
    q.check('anchor immutable after allstep test',q.fingerprint(anchor)==fixed)
    # Current generator state is overwritten on the next module jump from history[0].
    w=worlds[0];anchor=q.ss.load(P/'w0.sim');claim('negative current_state_only');s=q.isolate_copy(anchor,'current state negative');before=q.roots(s)
    for j,d in enumerate(s.dists.dists.values()):d.rng.bit_generator.state=np.random.default_rng(700000+j).bit_generator.state
    after=q.roots(s)
    q.check('current states changed without root change',all(before[k]['state']!=after[k]['state'] and before[k]['root']==after[k]['root'] for k in before))
    row=q.continue_branch(s,w,0,'negative current_state_only');ref=next(r for r in original if r['label']=='scaffold_control w0')
    q.check('current state mutation ineffective',row['trajectory']==ref['trajectory'])
    q.save('daywise_pairing.json',paths);q.save('daywise_timings.json',measurements)
    q.save('SUCCESS.json',dict(additional_trajectories=3,total_budget_used=len(json.loads((P/'trajectory_ledger.json').read_text())),checks=len(q.CHECKS),completed=time.time()))
    print(json.dumps(json.loads((q.O/'SUCCESS.json').read_text())),flush=True)
try:main()
except Exception as e:
    q.save('FAILURE.json',dict(error=repr(e),traceback=q.traceback.format_exc()));raise
