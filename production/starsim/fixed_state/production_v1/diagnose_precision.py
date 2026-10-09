"""Array-only threshold diagnosis: does not advance a simulator."""
import production as p
q=p.q;np=p.np;O=p.O
plan=p.json.loads((O/'PLAN.json').read_text());job=next(j for j in plan['seeds'] if j['world']=='w2' and j['rep']==245)
s=q.ss.load(p.A/'smoke/w2.sim');q.reseed(s,job['seed'],'array-only diagnosis')
iv=q.campaign(s);d=iv.coverage_dist;bg=type(d.rng.bit_generator)(0);bg.state=d.history[0];bg=bg.jumped(jumps=d.dt_jump_size*(int(iv.ti)+1));u=np.random.Generator(bg).random(5000,dtype=q.ss.dtypes.float)
a=u<.9;b=u<np.float64(.9);ids=np.flatnonzero(a!=b)
assert len(ids)>0
out=dict(job=job,uniform_dtype=str(u.dtype),python_scalar_result_dtype=str(np.result_type(u,.9)),numpy_scalar_result_dtype=str(np.result_type(u,np.float64(.9))),different_ids=ids.tolist(),uniforms=[float(u[i]) for i in ids],float32_threshold=float(np.float32(.9)),float64_threshold=float(np.float64(.9)),old_predicted_count=int(a.sum()),corrected_predicted_count=int(b.sum()),simulation_steps=0,mechanism='NumPy weak Python scalar casts .9 to float32; actual campaign passes numpy.float64 from float64 prob array and comparison promotes uniform to float64')
(O/'threshold_diagnosis.json').write_text(p.json.dumps(out,indent=2));print(p.json.dumps(out,indent=2))
