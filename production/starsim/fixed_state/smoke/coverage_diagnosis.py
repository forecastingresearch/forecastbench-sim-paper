"""Last two authorized trajectories. Correct integer campaign probability truncation.
Preserves earlier smoke code/results; does NOT certify the full intervention grid.
"""
import json,time
from pathlib import Path
import numpy as np
import smoke as q
P=Path(__file__).resolve().parent
assert (P/'extended/SUCCESS.json').exists()
q.O=P/'coverage_fix';q.O.mkdir(exist_ok=True)
if (q.O/'RESULT.json').exists():raise RuntimeError('Diagnosis already completed; no rerun')

def claim(label):
    ledger=json.loads((P/'trajectory_ledger.json').read_text());assert len(ledger)<70
    ledger.append(dict(n=len(ledger)+1,label=label,started=time.time(),pid=__import__('os').getpid()))
    (P/'trajectory_ledger.json').write_text(json.dumps(ledger,indent=2));print(label,flush=True)

def main():
    originals=json.loads((P/'outcomes.json').read_text());branches=[r for r in originals if r['label'].startswith('branch ')]
    q.check('old fractional arms delivered zero vaccine',all(len(r['day21']['vaccinated_ids'])==0 for r in branches if 0<r['coverage']<1))
    # Inspect saved anchor and reproduce truncation on standalone arrays: no simulation.
    anchor=q.ss.load(P/'w2.sim');prob=q.campaign(anchor).prob;bad=prob.copy();bad[:]=.9
    q.check('integer probability truncation identified',np.issubdtype(prob.dtype,np.integer) and np.all(bad==0),dict(dtype=str(prob.dtype),before=prob.tolist(),assigned09=bad.tolist()))
    q.save('DIAGNOSIS.json',dict(affected_main_fractional_branches=24,also_affected=['worker repeats','allstep c90 pair'],cause='campaign prob initialized from integer 0; in-place fractional assignments truncate to zero',original_script='smoke.py:125',historical_direct_factory_fractional_runs_affected=False))
    w=json.loads((q.R/'data/worlds/worlds_c90.json').read_text())['worlds'][2];seed=int(np.random.SeedSequence([20260923,2,0]).generate_state(1,dtype=np.uint64)[0])
    paired=q.isolate_copy(anchor,'fixed pair');q.reseed(paired,seed,'fixed pair')
    baseline=next(r for r in originals if r['label']=='branch w2 r0 c0')
    results=[]
    for cov in [.25,.9]:
        label='float_probability w2 r0 c'+str(cov);claim(label);s=q.isolate_copy(paired,label)
        q.campaign(s).prob=np.full(q.campaign(s).prob.shape,cov,dtype=float)
        q.check(label+' configured dose exact',np.issubdtype(q.campaign(s).prob.dtype,np.floating) and np.all(q.campaign(s).prob==cov))
        row=q.continue_branch(s,w,cov,label);n=len(row['day21']['vaccinated_ids'])
        q.check(label+' nonvacuous vaccine uptake',0<n<5000 and abs(n-5000*cov)<6*np.sqrt(5000*cov*(1-cov)),dict(n=n,coverage=cov))
        q.check(label+' actual outcome differs from control',row['trajectory']!=baseline['trajectory'],dict(new40=row['new40'],control40=baseline['new40']))
        q.check(label+' same day21 network as paired baseline',row['day21']['network']==baseline['day21']['network'])
        q.check(label+' paired roots match baseline',row['roots']==baseline['roots'])
        q.check(label+' anchor immutable',q.fingerprint(anchor)==q.fingerprint(q.ss.load(P/'w2.sim')))
        results.append(dict(coverage=cov,administered=n,new40=row['new40'],new60=row['new60'],baseline40=baseline['new40'],baseline60=baseline['new60']))
    q.save('RESULT.json',dict(status='fix verified in two w2 branches only; full intervention validation blocked by authorized budget',results=results,checks=len(q.CHECKS),total_budget_used=len(json.loads((P/'trajectory_ledger.json').read_text()))))
    print(json.dumps(json.loads((q.O/'RESULT.json').read_text())),flush=True)
try:main()
except Exception as e:
    q.save('FAILURE.json',dict(error=repr(e),traceback=q.traceback.format_exc()));raise
