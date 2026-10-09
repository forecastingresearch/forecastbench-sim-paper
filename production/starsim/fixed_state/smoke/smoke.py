"""Bounded snapshot validation, maximum 70 cumulative trajectory starts.
No model/network calls. Inputs read-only. Outputs only alongside this script.
Resume is intentionally disabled: failures require review, and the persistent
budget ledger counts attempted lineages across invocations, including failures.
"""
import os,sys,time,json,hashlib,traceback,resource,subprocess,platform
from pathlib import Path
TIMPORT=time.perf_counter()
import numpy as np
import starsim as ss
import sciris as sc
IMPORT_SECONDS=time.perf_counter()-TIMPORT
O=Path(__file__).resolve().parent;A=Path('/Users/elsehow/Projects/iclr-2026');R=A/'results/causal'
MAX_TRAJECTORIES=70; CHECKS=[];TIMINGS=[];OUTCOMES=[];STREAMS=[];STEP21={};COUNTER=0

def jsonable(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    return str(x)
def save(name,x): (O/name).write_text(json.dumps(x,indent=2,default=jsonable))
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=jsonable,allow_nan=True).encode()).hexdigest()
def harray(x):
    x=np.asarray(x);return digest([str(x.dtype),list(x.shape),hashlib.sha256(x.tobytes()).hexdigest()])
def check(name,condition,detail=None):
    CHECKS.append(dict(test=name,pass_=bool(condition),detail=detail));save('checks.json',CHECKS)
    if not condition:raise AssertionError(name+': '+str(detail))
def claim(label):
    global COUNTER
    p=O/'trajectory_ledger.json';ledger=json.loads(p.read_text()) if p.exists() else []
    if len(ledger)>=MAX_TRAJECTORIES:raise RuntimeError('Hard cumulative 70-trajectory budget reached')
    ledger.append(dict(n=len(ledger)+1,label=label,started=time.time(),pid=os.getpid()));save(p.name,ledger)
    COUNTER+=1;print(f'[{len(ledger)}/{MAX_TRAJECTORIES}] {label}',flush=True)
def timed(label,fn):
    t=time.perf_counter();v=fn();dt=time.perf_counter()-t
    TIMINGS.append(dict(task=label,seconds=dt));save('timings.json',TIMINGS);return v

def factory(beta,seed,cov=None):
    sir=ss.SIR(init_prev=.005,beta=beta,dur_inf=10,p_death=0)
    pars=dict(n_agents=5000,networks=dict(type='random',n_contacts=6),diseases=sir,dur=90,dt=1,verbose=0,rand_seed=seed)
    if cov is not None:pars['interventions']=[ss.campaign_vx(product=ss.simple_vx(efficacy=.95,leaky=True),years=[2021],prob=cov)]
    return ss.Sim(pars)

def arrays(s):
    # Preserve named state owners instead of pointer-keyed people._states keys.
    out={}
    for k in ['uid','slot','parent','alive','age','female','ti_dead','ti_removed','scale']:
        out['people.'+k]=getattr(s.people,k).raw
    out['people.auids']=s.people.auids
    for mod in s.modules:
        for k,state in mod.state_dict.items():out[mod.name+'.'+k]=state.raw
        if hasattr(mod,'edges'):
            for k,v in mod.edges.items():out[mod.name+'.edges.'+k]=v
    return out

def physical(s):
    return {k:harray(v) for k,v in arrays(s).items()}
def common_physical(s):
    return {k:v for k,v in physical(s).items() if k.startswith(('people.','sir.','randomnet.'))}
def history(s,end=20):
    return {k:harray(np.asarray(s.diseases.sir.results[k])[:end+1]) for k in ['new_infections','n_infected','n_susceptible','n_recovered']}
def roots(s):
    return {k:dict(seed=int(d.seed),trace=d.trace,root=digest(d.history[0]),state=digest(d.rng.bit_generator.state),ind=int(d.ind)) for k,d in s.dists.dists.items()}
def physical_state(s):return dict(arrays=physical(s),history=history(s),clock=int(s.ti),module_clocks={m.name:int(m.ti) for m in s.modules},loop_index=int(s.loop.index))
def fingerprint(s):return digest(dict(physical=physical_state(s),rng=roots(s)))
def sir(s):return s.diseases.sir
def campaign(s):return next(iter(s.interventions.values()))
def ever(s):
    # Daily new cases exclude initialized infections at ti=0. Infer initial count
    # exactly as the original miner; do not finalize a paused simulation.
    res=sir(s).results;daily=np.asarray(res.new_infections)
    initial=int(round(float(res.n_infected[0])-float(daily[0])))
    return initial+np.cumsum(daily),initial

def registry_check(s,label):
    ds=list(s.dists.dists.values());ids={id(d) for d in ds};mods=list(s.modules)
    check(label+' registry unique objects',len(ids)==len(ds))
    check(label+' unique seeds',len({d.seed for d in ds})==len(ds))
    for k,d in s.dists.dists.items():
        check(label+' sim/slot linkage '+k,d.sim is s and d.slots is s.people.slot)
    for m in mods:
        if m.dists:
            check(label+' module dist linkage '+m.name,all(id(d) in ids and d.module is m for d in m.dists.dists.values()))
    owners={id(s),id(s.people)}|{id(m) for m in mods}
    check(label+' loop bound methods',all(getattr(f,'__self__',None) is None or id(f.__self__) in owners for f in s.loop.plan.func))

def isolate_copy(s,label):
    c=timed('deepcopy '+label,lambda:s.copy(die=True));a=arrays(s);b=arrays(c)
    check(label+' no state alias',all(not np.shares_memory(a[k],b[k]) for k in a))
    check(label+' no RNG alias',all(s.dists.dists[k].rng is not c.dists.dists[k].rng for k in s.dists.dists))
    registry_check(c,label)
    check(label+' copy equality',fingerprint(s)==fingerprint(c))
    return c

def reseed(s,seed,label):
    before=physical_state(s);old=roots(s);param={k:digest(d.pars) for k,d in s.dists.dists.items()}
    for trace,d in s.dists.dists.items():d.init(trace=trace,seed=int(seed),module=d.module,sim=s,slots=s.people.slot,force=True)
    check(label+' physical/history preserved',before==physical_state(s))
    check(label+' dist params preserved',param=={k:digest(d.pars) for k,d in s.dists.dists.items()})
    check(label+' every root changed',all(old[k]['root']!=v['root'] for k,v in roots(s).items()))
    registry_check(s,label)
    return roots(s)

def boundary(s,label):
    check(label+' next clock 21',s.ti==21,{m.name:m.ti for m in s.modules})
    check(label+' module clocks 21',all(m.ti==21 for m in s.modules))
    f=s.loop.plan.func[s.loop.index]
    check(label+' next day21 sim.start_step',getattr(f,'__self__',None) is s and f.__name__=='start_step')
    check(label+' not finalized',not s.complete and not s.results_ready)

def cached_check(s,w,cov,cache,dose,full,label):
    e,n0=ever(s);b=w['beta'];seed=w['seed'];r=cache[b,seed,False if cov in (None,0) else True]
    if cov in (None,0,.9):
        ds=[0,5,10,15,20,40,60] if full else [0,5,10,15,20]
        check(label+' cache ever',all(int(e[d])==r['ever'][str(d)] for d in ds),dict(actual={d:int(e[d]) for d in ds},expected={d:r['ever'][str(d)] for d in ds}))
        check(label+' cache active',all(int(sir(s).results.n_infected[d])==r['active'][str(d)] for d in [0,20]))
        check(label+' initial infected',n0==r['seeds0'])
    else:
        target=dose[f'{b:.3f}|{cov:.2f}|{seed}'];stop=91 if full else 21
        check(label+' full dose series',np.array_equal(e[:stop],target[:stop]))
    check(label+' displayed cumulative',int(e[20])==w['c20'])
    check(label+' displayed infectious',int(sir(s).results.n_infected[20])==cache[b,seed,False]['active']['20'])
    if full:check(label+' finalization accounting',np.array_equal(e,n0+np.asarray(sir(s).results.cum_infections)))

def continue_branch(s,w,cov,label):
    campaign(s).prob[:]=cov
    h=history(s);initial_state=physical_state(s);recover=sir(s).ti_recovered.raw.copy();infected=sir(s).infected.raw.copy();rngroot=roots(s)
    check(label+' no preday21 vaccine',not np.asarray(campaign(s).vaccinated).any() and np.all(np.asarray(sir(s).rel_sus)==1))
    initial_sus=int(np.asarray(sir(s).susceptible).sum())
    t=time.perf_counter();s.run(until=2021);day21time=time.perf_counter()-t
    check(label+' historical preservation day21',history(s)==h)
    vac=np.asarray(campaign(s).vaccinated);rel=np.asarray(sir(s).rel_sus)
    check(label+' efficacy and uptake',np.allclose(rel[vac],.05) and np.all(rel[~vac]==1) and (cov!=0 or not vac.any()) and (cov!=1 or vac.all()))
    check(label+' vaccine timing',np.all(np.asarray(campaign(s).ti_vaccinated)[vac]==21))
    check(label+' existing recovery unchanged',np.array_equal(sir(s).ti_recovered.raw[infected],recover[infected],equal_nan=True))
    d21=dict(physical=physical(s),network={k:harray(v) for k,v in next(iter(s.networks.values())).edges.items()},rng=roots(s),vaccinated_ids=np.flatnonzero(vac).tolist(),new=int(sir(s).results.new_infections[21]))
    STEP21[label]=d21
    # Global NumPy state must not drive future selected model mechanisms.
    global_before=digest(np.random.get_state())
    t=time.perf_counter();s.run(until=2060);remain=time.perf_counter()-t
    check(label+' no global RNG use days22to60',global_before==digest(np.random.get_state()))
    TIMINGS.append(dict(task='continuation21to60 '+label,seconds=day21time+remain));save('timings.json',TIMINGS)
    e,n0=ever(s);daily=np.asarray(sir(s).results.new_infections)
    y=[int(daily[21:t+1].sum()) for t in [40,60]]
    check(label+' unchanged prehistory',h==history(s))
    check(label+' exact subtraction',all(y[j]==int(e[t])-w['c20'] for j,t in enumerate([40,60])))
    check(label+' feasible support',0<=y[0]<=y[1]<=5000-w['c20'],y)
    check(label+' conservation',np.all(np.asarray(sir(s).results.n_susceptible)[:61]+np.asarray(sir(s).results.n_infected)[:61]+np.asarray(sir(s).results.n_recovered)[:61]==5000))
    check(label+' susceptible accounting',initial_sus-int(np.asarray(sir(s).susceptible).sum())==y[1])
    check(label+' original infected recovery still fixed',np.array_equal(sir(s).ti_recovered.raw[infected],recover[infected],equal_nan=True))
    row=dict(label=label,world=w['world_id'],coverage=cov,new40=y[0],new60=y[1],roots=rngroot,day21=d21,trajectory=hashlib.sha256(np.asarray(e[:61]).tobytes()).hexdigest(),final=fingerprint(s),daily=daily[:61].tolist())
    OUTCOMES.append(row);save('outcomes.json',OUTCOMES);return row

def main():
    if (O/'SUCCESS.json').exists():raise RuntimeError('Suite already completed; no automatic rerun')
    check('Starsim exact version',ss.__version__=='3.3.4',ss.__version__)
    check('multistream enabled',not ss.options.single_rng)
    sources={Path(p):v['sha256'] for p,v in json.loads((O.parent/'feasibility/source_manifest.json').read_text()).items()}
    for p,h in sources.items():check('input unchanged '+str(p),hashlib.sha256(p.read_bytes()).hexdigest()==h)
    save('inputs.json',{str(p):h for p,h in sources.items()})
    save('environment.json',dict(python=sys.version,platform=platform.platform(),starsim=ss.__version__,numpy=np.__version__,sciris=sc.__version__,import_s=IMPORT_SECONDS,options=str(ss.options)))
    rows=json.loads((R/'starsim_causal/.sim_cache_v2.json').read_text());cache={(r['beta'],r['seed'],r['vax']):r for r in rows};dose=json.loads((R/'starsim_causal/.sim_cache_dose.json').read_text());worlds=json.loads((R/'data/worlds/worlds_c90.json').read_text())['worlds']
    anchors={};immutable={};historical={};scaffold_controls={};sizes=[]
    for w in worlds:
        wid=w['world_id']; b=w['beta'];seed=w['seed']
        # 16 unmodified historical trajectories, including the displayed seeds.
        for cov in [None,.25,.5,.9]:
            label=f'historical {wid} {cov}';claim(label);s=factory(b,seed,cov)
            timed('full90 '+label,lambda:s.run());cached_check(s,w,cov,cache,dose,True,label)
            historical[wid,cov]=dict(e=ever(s)[0].copy(),physical=common_physical(s))
        # Four independent pause/resume tests, without changing random roots.
        label='pause_control '+wid;claim(label);s=factory(b,seed)
        timed('prefix20 '+label,lambda:s.run(until=2020));boundary(s,label);cached_check(s,w,None,cache,dose,False,label)
        basephys=common_physical(s);baserng=roots(s);basehistory=history(s)
        timed('resume90 '+label,lambda:s.run());cached_check(s,w,None,cache,dose,True,label)
        check(label+' uninterrupted equality',np.array_equal(ever(s)[0],historical[wid,None]['e']) and common_physical(s)==historical[wid,None]['physical'])
        # Four dormant campaign anchors, preserving original prehistory.
        label='anchor '+wid;claim(label);s=factory(b,seed,0)
        timed('prefix20 '+label,lambda:s.run(until=2020));boundary(s,label);cached_check(s,w,0,cache,dose,False,label)
        check(label+' scaffold identical physical',common_physical(s)==basephys)
        check(label+' scaffold identical prefix',history(s)==basehistory)
        newrng=roots(s);check(label+' unchanged common RNG paths',set(baserng)<=set(newrng) and all(baserng[k]==newrng[k] for k in baserng))
        registry_check(s,label);anchors[wid]=s;immutable[wid]=fingerprint(s)
        path=O/(wid+'.sim');timed('save '+wid,lambda:s.save(path,shrink=False));sizes.append(dict(world=wid,bytes=path.stat().st_size))
        loaded=timed('load '+wid,lambda:ss.load(path));check(label+' serialization equality',fingerprint(loaded)==fingerprint(s));registry_check(loaded,'loaded '+wid)
        # Four no-reseed copy continuations: zero-campaign equals original control.
        claim('scaffold_control '+wid);c=isolate_copy(loaded,'scaffold_control '+wid)
        row=continue_branch(c,w,0,'scaffold_control '+wid);scaffold_controls[wid]=row
        check('scaffold no-op original future '+wid,np.array_equal(ever(c)[0][:61],historical[wid,None]['e'][:61]))
        check('anchor immutable after control '+wid,fingerprint(s)==immutable[wid])
    save('snapshot_sizes.json',sizes)
    result={}
    for w in worlds:
        wid=w['world_id'];anchor=anchors[wid]
        rep_roots=[]
        for rep in range(2):
            k=int(np.random.SeedSequence([20260923,int(wid[1:]),rep]).generate_state(1,dtype=np.uint64)[0])
            paired=isolate_copy(anchor,f'paired {wid} r{rep}')
            rr=timed('reseed '+wid,lambda:reseed(paired,k,f'reseed {wid} r{rep}'));rep_roots.append(rr)
            STREAMS.append(dict(world=wid,rep=rep,child_seed=k,streams=rr));save('streams.json',STREAMS)
            order=[0,.25,.5,.9] if rep==0 else [.9,.5,.25,0]
            for cov in order:
                label=f'branch {wid} r{rep} c{cov}';claim(label)
                s=isolate_copy(paired,label);before=fingerprint(paired)
                result[wid,rep,cov]=continue_branch(s,w,cov,label)
                check(label+' pair source immutable',fingerprint(paired)==before)
                check(label+' original anchor immutable',fingerprint(anchor)==immutable[wid])
            day21=[result[wid,rep,c]['day21'] for c in [0,.25,.5,.9]]
            check(f'{wid} r{rep} same day21 network',all(d['network']==day21[0]['network'] for d in day21))
            vsets=[set(d['vaccinated_ids']) for d in day21];check(f'{wid} r{rep} nested vaccine uptake',all(x<=y for x,y in zip(vsets,vsets[1:])))
            keys=[k for k in rr if ('randomnet' in k or 'trans_rng' in k)]
            check(f'{wid} r{rep} same network/transmission day21 streams',bool(keys) and all(all(d['rng'][k]==day21[0]['rng'][k] for k in keys) for d in day21))
        check(wid+' distinct roots across replicates',all(rep_roots[0][k]['root']!=rep_roots[1][k]['root'] for k in rep_roots[0]))
    # Reproduce two branches from disk in a fresh process, counted by parent.
    for w in [worlds[0],worlds[-1]]:
        wid=w['world_id'];label='worker_repeat '+wid;claim(label)
        job=dict(world=w,rep=1,cov=.9,label=label);save('worker_job.json',job)
        t=time.perf_counter();subprocess.run(['sh',str(O/'run_smoke.sh'),'--worker',str(O/'worker_job.json')],check=True)
        TIMINGS.append(dict(task='worker_spawn_load_branch '+wid,seconds=time.perf_counter()-t));save('timings.json',TIMINGS)
        row=json.loads((O/'worker_result.json').read_text());ref=result[wid,1,.9]
        check(label+' same process-independent result',all(row[k]==ref[k] for k in ['roots','day21','trajectory','final','daily']))
    # Negative controls: changing rand_seed or global NumPy alone leaves future unchanged.
    w=worlds[0];wid=w['world_id']
    for kind in ['rand_seed_only','numpy_seed_only']:
        label='negative '+kind;claim(label);s=isolate_copy(anchors[wid],label)
        if kind=='rand_seed_only':s.pars.rand_seed=987654321
        else:np.random.seed(987654321)
        row=continue_branch(s,w,0,label)
        check(label+' unchanged original continuation',row['trajectory']==scaffold_controls[wid]['trajectory'])
    # Positive uptake endpoint control on the same snapshot.
    claim('coverage_one');s=isolate_copy(anchors[wid],'coverage_one');continue_branch(s,w,1,'coverage_one')
    for wid,s in anchors.items():check('final anchor immutable '+wid,fingerprint(s)==immutable[wid])
    for p,h in sources.items():check('final input unchanged '+str(p),hashlib.sha256(p.read_bytes()).hexdigest()==h)
    save('SUCCESS.json',dict(trajectories_this_invocation=COUNTER,total_budget_used=len(json.loads((O/'trajectory_ledger.json').read_text())),checks=len(CHECKS),max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,import_s=IMPORT_SECONDS,completed=time.time(),remaining_caveat='Fixed hidden state, not report-conditional distribution; two independent replicates do not validate independence statistically.'))
    print('SUCCESS',json.dumps(json.loads((O/'SUCCESS.json').read_text())),flush=True)

def worker(jobfile):
    # Parent has claimed this trajectory. Isolate child output to avoid touching
    # parent checks/timings/outcomes while retaining the same simulation code.
    global O
    parent=O;job=json.loads(Path(jobfile).read_text());O=parent/('worker_'+job['world']['world_id']);O.mkdir(exist_ok=True)
    w=job['world'];s=ss.load(parent/(w['world_id']+'.sim'))
    seed=int(np.random.SeedSequence([20260923,int(w['world_id'][1:]),job['rep']]).generate_state(1,dtype=np.uint64)[0]);reseed(s,seed,job['label'])
    row=continue_branch(s,w,job['cov'],job['label']);(parent/'worker_result.json').write_text(json.dumps(row,default=jsonable))

if __name__=='__main__':
    try:
        if len(sys.argv)>1 and sys.argv[1]=='--worker':worker(sys.argv[2])
        else:main()
    except Exception as e:
        save('FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc(),trajectories_this_invocation=COUNTER));traceback.print_exc();sys.exit(1)
