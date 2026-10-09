"""Corrected 36-start vaccine validation. Never starts production or model calls.
Uses existing validated anchors; preserves prior code, failures, and inputs.
Each start is claimed in a persistent ledger before execution. No auto-resume.
"""
import sys,os,json,time,copy,hashlib,subprocess,resource,platform
from pathlib import Path
START=time.perf_counter();O=Path(__file__).resolve().parent;OLD=O.parent/'smoke'
sys.path.insert(0,str(OLD))
import smoke as q
import numpy as np
IMPORT=time.perf_counter()-START
q.O=O
ROWS=[];STREAMS=[]

def claim(label):
    p=O/'ledger.json';r=json.loads(p.read_text()) if p.exists() else []
    if len(r)>=36:raise RuntimeError('Approved 36-start hard limit reached')
    r.append(dict(n=len(r)+1,label=label,time=time.time(),pid=os.getpid()));q.save('ledger.json',r)
    print(f'[{len(r)}/36] {label}',flush=True)
def dose_valid(prob,cov):
    assert np.issubdtype(prob.dtype,np.floating), 'coverage must be floating point'
    assert prob.size==1 and np.all(prob==cov), 'configured coverage differs from intended coverage'
def uptake_valid(actual,expected,cov):
    assert np.array_equal(actual,expected),'actual IDs do not equal independently predicted eligible Bernoulli draws'
    assert (len(actual)==0 if cov==0 else 0<len(actual)<5000),'nonvacuous fractional uptake check'
def child(w,rep):return int(np.random.SeedSequence([20260923,int(w['world_id'][1:]),rep]).generate_state(1,dtype=np.uint64)[0])
def prepare(w,rep,label):
    s=q.timed('load '+label,lambda:q.ss.load(OLD/(w['world_id']+'.sim')))
    q.boundary(s,label);before=q.fingerprint(s)
    c=q.isolate_copy(s,label);q.timed('reseed '+label,lambda:q.reseed(c,child(w,rep),label))
    q.check(label+' loaded anchor not mutated',q.fingerprint(s)==before)
    return c

def predict_uptake(s,cov):
    # Independent calculation from recorded root and current step, not from
    # campaign.step() or coverage_dist.filter(). No simulation steps consumed.
    iv=q.campaign(s);eligible=np.asarray(iv.check_eligibility(),dtype=int)
    slots=np.asarray(s.people.slot)[eligible].astype(int);d=iv.coverage_dist
    bg=type(d.rng.bit_generator)(0);bg.state=copy.deepcopy(d.history[0])
    bg=bg.jumped(jumps=d.dt_jump_size*(int(iv.ti)+1))
    u=np.random.Generator(bg).random(int(slots.max())+1,dtype=q.ss.dtypes.float)[slots]
    return eligible,eligible[u<cov]

def network(s):return {k:q.harray(v) for k,v in next(iter(s.networks.values())).edges.items()}
def path_state(s,day):return dict(day=day,network=network(s),network_rng=q.roots(s)['networks_randomnet_dist'],roots={k:v['root'] for k,v in q.roots(s).items()})
def execute(s,w,rep,cov,label,manual=True,daywise=False):
    iv=q.campaign(s);iv.prob=np.full(iv.prob.shape,cov,dtype=float);dose_valid(iv.prob,cov)
    q.check(label+' float exact dose',True,dict(dtype=str(iv.prob.dtype),value=iv.prob.tolist(),intended=cov))
    q.check(label+' campaign day21 schedule',np.array_equal(iv.timepoints,[21]))
    q.check(label+' leaky .95 configured',iv.product.pars.leaky and iv.product.pars.efficacy==.95)
    q.check(label+' default whole-population eligibility',iv.eligibility is None)
    q.check(label+' no preday21 intervention',not np.asarray(iv.vaccinated).any() and np.all(np.asarray(iv.n_doses)==0) and np.all(np.asarray(q.sir(s).rel_sus)==1))
    eligible,expected=predict_uptake(s,cov)
    q.check(label+' all 5000 eligible',np.array_equal(eligible,np.arange(5000)))
    prefix=q.history(s);rec=q.sir(s).ti_recovered.raw.copy();infected=q.sir(s).infected.raw.copy();r0=q.roots(s);su0=int(np.asarray(q.sir(s).susceptible).sum())
    global0=q.digest(np.random.get_state());simulation_s=0;before_sir=None;order=[];timing_asserted=False
    if manual:
        # Observe immediately before/after campaign inside the actual loop plan,
        # without adding a module or changing its ordering or random streams.
        t=time.perf_counter();s.timer.start()
        while int(s.ti)==21:
            f=s.loop.plan.func[s.loop.index];owner=getattr(f,'__self__',None);name=getattr(f,'__name__','')
            if name=='step':order.append(getattr(owner,'name',str(type(owner))))
            intervention=owner is iv and name=='step'
            if intervention:
                q.check(label+' intervention fires at ti21',iv.ti==21 and s.ti==21)
                q.check(label+' actual eligibility at administration',np.array_equal(np.asarray(iv.check_eligibility()),eligible))
                before_sir={k:v for k,v in q.physical(s).items() if k.startswith('sir.') and k!='sir.rel_sus'}
                q.check(label+' before campaign no protection',np.all(np.asarray(q.sir(s).rel_sus)==1))
            s.loop.run_one_step()
            if intervention:
                after_sir={k:v for k,v in q.physical(s).items() if k.startswith('sir.') and k!='sir.rel_sus'}
                q.check(label+' vaccination alters susceptibility not infection/prognosis flags',before_sir==after_sir)
                q.check(label+' immediate intended susceptibility change',np.allclose(np.asarray(q.sir(s).rel_sus)[expected],.05) and np.all(np.asarray(q.sir(s).rel_sus)[np.setdiff1d(eligible,expected)]==1))
                timing_asserted=True
        simulation_s+=time.perf_counter()-t
        names=list(s.networks.keys());q.check(label+' network then vaccine then transmission',timing_asserted and order.index(names[0])<order.index(iv.name)<order.index('sir'),order)
    else:
        t=time.perf_counter();s.run(until=2021);simulation_s+=time.perf_counter()-t
    actual=np.flatnonzero(np.asarray(iv.vaccinated));uptake_valid(actual,expected,cov)
    q.check(label+' independently predicted actual vaccinated IDs',True,dict(n=len(actual),expected=len(expected)))
    q.check(label+' exactly one dose only for chosen eligible IDs',np.array_equal(np.asarray(iv.n_doses),np.isin(np.arange(5000),actual).astype(float)))
    q.check(label+' dates for actual vaccination',np.all(np.asarray(iv.ti_vaccinated)[actual]==21))
    rel=np.asarray(q.sir(s).rel_sus);unvaccinated=np.setdiff1d(eligible,actual)
    q.check(label+' nonvacuous effect',np.allclose(rel[actual],.05) and np.all(rel[unvaccinated]==1) and (cov==0 or len(actual)>0))
    q.check(label+' efficacy includes initially infected and recovered',cov==0 or (np.any(np.isin(actual,np.flatnonzero(infected))) and np.any(np.isin(actual,np.flatnonzero(np.asarray(q.sir(s).recovered))))))
    administration=dict(eligible=eligible.tolist(),expected=expected.tolist(),actual=actual.tolist(),coverage=cov,dtype=str(iv.prob.dtype),day=21,network=network(s),root_hashes={k:v['root'] for k,v in r0.items()},new21=int(q.sir(s).results.new_infections[21]))
    path=[path_state(s,21)]
    if daywise:
        for day in range(22,61):
            t=time.perf_counter();s.run(until=2000+day);simulation_s+=time.perf_counter()-t
            q.check(label+f' d{day} history unchanged',q.history(s)==prefix)
            q.check(label+f' d{day} latent recovery unchanged',np.array_equal(q.sir(s).ti_recovered.raw[infected],rec[infected],equal_nan=True))
            q.check(label+f' d{day} no revaccination',np.array_equal(np.flatnonzero(np.asarray(iv.vaccinated)),actual) and np.array_equal(np.asarray(iv.n_doses),np.isin(np.arange(5000),actual).astype(float)))
            path.append(path_state(s,day))
    else:
        t=time.perf_counter();s.run(until=2060);simulation_s+=time.perf_counter()-t
    q.TIMINGS.append(dict(task='simulation21to60 '+label,seconds=simulation_s));q.save('timings.json',q.TIMINGS)
    q.check(label+' no global NumPy RNG use',global0==q.digest(np.random.get_state()))
    q.check(label+' unchanged history',q.history(s)==prefix)
    q.check(label+' fixed preexisting recoveries',np.array_equal(q.sir(s).ti_recovered.raw[infected],rec[infected],equal_nan=True))
    q.check(label+' no second vaccine doses',np.array_equal(np.asarray(iv.n_doses),np.isin(np.arange(5000),actual).astype(float)))
    q.check(label+' configured dose still exact',iv.prob.dtype.kind=='f' and np.all(iv.prob==cov))
    e,_=q.ever(s);daily=np.asarray(q.sir(s).results.new_infections);y=[int(daily[21:h+1].sum()) for h in [40,60]]
    q.check(label+' exact displayed C20 and subtraction',int(e[20])==w['c20'] and all(y[j]==int(e[h])-w['c20'] for j,h in enumerate([40,60])))
    q.check(label+' feasible support',0<=y[0]<=y[1]<=5000-w['c20'],y)
    q.check(label+' susceptible depletion',su0-int(np.asarray(q.sir(s).susceptible).sum())==y[1])
    q.check(label+' SIR conservation',np.all(sum(np.asarray(q.sir(s).results[k])[:61] for k in ['n_susceptible','n_infected','n_recovered'])==5000))
    q.check(label+' no dead agents',np.asarray(s.people.alive).all())
    row=dict(label=label,world=w['world_id'],rep=rep,coverage=cov,administered=len(actual),new40=y[0],new60=y[1],administration=administration,roots=r0,trajectory=q.harray(e[:61]),final=q.fingerprint(s),daily=daily[:61].tolist(),simulation_seconds=simulation_s,path=path)
    ROWS.append(row);q.save('outcomes.json',ROWS);return row

def compare(a,b,label):
    q.check(label,all(a[k]==b[k] for k in ['administration','roots','trajectory','final','daily']))

def main():
    if (O/'RESULT.json').exists() or (O/'ledger.json').exists():raise RuntimeError('Fresh suite directory required; no automatic replay/resume')
    q.check('pinned version and multistream',q.ss.__version__=='3.3.4' and not q.ss.options.single_rng)
    inputs=json.loads((OLD/'inputs.json').read_text())
    for p,h in json.loads((OLD/'artifact_manifest.json').read_text()).items():inputs[str(OLD/p)]=h
    for p,h in json.loads((O.parent/'manifest.json').read_text()).items():inputs[p]=h
    for p,h in inputs.items():q.check('input unchanged '+p,hashlib.sha256(Path(p).read_bytes()).hexdigest()==h)
    q.save('inputs.json',inputs);q.save('environment.json',dict(python=sys.version,platform=platform.platform(),starsim=q.ss.__version__,numpy=np.__version__,import_s=IMPORT))
    # Regression tests are array-only, not additional simulated trajectories.
    for cov in [.25,.5,.9]:
        bad=np.array([0],dtype=int);bad[:]=cov
        try:dose_valid(bad,cov);rejected=False
        except AssertionError:rejected=True
        q.check(f'integer truncation regression rejected c{cov}',rejected)
        try:uptake_valid(np.array([],int),np.array([7],int),cov);rejected=False
        except AssertionError:rejected=True
        q.check(f'empty-uptake vacuity regression rejected c{cov}',rejected)
    worlds=json.loads((q.R/'data/worlds/worlds_c90.json').read_text())['worlds'];results={}
    for w in worlds:
        for rep in range(2):
            paired=prepare(w,rep,f"pair {w['world_id']} r{rep}");f=q.fingerprint(paired)
            STREAMS.append(dict(world=w['world_id'],rep=rep,seed=child(w,rep),streams=q.roots(paired)));q.save('streams.json',STREAMS)
            for cov in ([0,.25,.5,.9] if rep==0 else [.9,.5,.25,0]):
                label=f"grid {w['world_id']} r{rep} c{cov}";claim(label)
                s=q.isolate_copy(paired,label);results[w['world_id'],rep,cov]=execute(s,w,rep,cov,label)
                q.check(label+' paired source immutable',q.fingerprint(paired)==f)
            rows=[results[w['world_id'],rep,c] for c in [0,.25,.5,.9]]
            q.check(f"{w['world_id']} r{rep} common initial RNG roots",all(r['roots']==rows[0]['roots'] for r in rows))
            q.check(f"{w['world_id']} r{rep} common day21 network",all(r['administration']['network']==rows[0]['administration']['network'] for r in rows))
            sets=[set(r['administration']['actual']) for r in rows]
            q.check(f"{w['world_id']} r{rep} strictly increasing nested uptake",all(a<b for a,b in zip(sets,sets[1:])))
    seeds=[v['seed'] for r in STREAMS for v in r['streams'].values()];roots=[v['root'] for r in STREAMS for v in r['streams'].values()]
    q.check('80 distinct across-replicate distribution seeds and roots',len(seeds)==80 and len(set(seeds))==80 and len(set(roots))==80)
    for w in [worlds[0],worlds[-1]]:
        label='worker '+w['world_id'];claim(label);job=dict(world=w,rep=1,cov=.9,label=label)
        q.save('job_'+w['world_id']+'.json',job);t=time.perf_counter()
        subprocess.run(['sh',str(O/'run.sh'),'--worker',str(O/('job_'+w['world_id']+'.json'))],check=True)
        q.TIMINGS.append(dict(task='worker_total '+label,seconds=time.perf_counter()-t));q.save('timings.json',q.TIMINGS)
        r=json.loads((O/('worker_'+w['world_id'])/'result.json').read_text());compare(r,results[w['world_id'],1,.9],label+' reproducible including normal day21 run')
    w=worlds[2];paths={}
    for cov in [0,.9]:
        label='daywise w2 c'+str(cov);claim(label);s=prepare(w,0,label);r=execute(s,w,0,cov,label,daywise=True);compare(r,results['w2',0,cov],label+' same endpoints as continuous run');paths[cov]=r['path']
    q.check('real control-vaccine identical networks and network RNG all 40 days',all(a['network']==b['network'] and a['network_rng']==b['network_rng'] for a,b in zip(paths[0],paths[.9])))
    q.check('real control-vaccine same root hashes all 40 days',all(a['roots']==b['roots'] for a,b in zip(paths[0],paths[.9])))
    for p,h in inputs.items():q.check('final immutable '+p,hashlib.sha256(Path(p).read_bytes()).hexdigest()==h)
    q.save('RESULT.json',dict(status='PASS',trajectories=len(json.loads((O/'ledger.json').read_text())),parent_assertions=len(q.CHECKS),elapsed_s=time.perf_counter()-START,import_s=IMPORT,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,production_executed=False,scope='32 grid, 2 fresh-process true vaccine repeats, 2 real control/vaccine daywise checks; fixed hidden-state validation only'))
    print(json.dumps(json.loads((O/'RESULT.json').read_text())),flush=True)

def worker(jobfile):
    job=json.loads(Path(jobfile).read_text());q.O=O/('worker_'+job['world']['world_id']);q.O.mkdir(exist_ok=True)
    s=prepare(job['world'],job['rep'],job['label']);row=execute(s,job['world'],job['rep'],job['cov'],job['label'],manual=False);q.save('result.json',row)

if __name__=='__main__':
    try:
        if len(sys.argv)>1 and sys.argv[1]=='--worker':worker(sys.argv[2])
        else:main()
    except Exception as e:
        q.save('FAILURE.json',dict(error=repr(e),traceback=q.traceback.format_exc()));q.traceback.print_exc();sys.exit(1)
