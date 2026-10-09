"""Production assertion-only correction: match actual float64 coverage comparison."""
import copy
import numpy as np

def tests():
 checks=[]
 for cov in [0,.25,.5,.9]:
  u0=np.float32(cov);u=np.array([np.nextafter(u0,np.float32(-np.inf)),u0,np.nextafter(u0,np.float32(np.inf))],dtype=np.float32)
  expected=u.astype(np.float64)<np.float64(cov)
  actual_semantics=u<np.full(1,cov,dtype=float)[0]
  assert np.array_equal(expected,actual_semantics)
  if cov==.9:assert not np.array_equal(u<cov,expected),'Must catch weak-scalar regression'
  checks.append(dict(coverage=cov,uniforms=u.tolist(),expected=expected.tolist(),old=(u<cov).tolist()))
 return checks

def predict_uptake(s,cov):
 import validate as v
 q=v.q;iv=q.campaign(s);eligible=np.asarray(iv.check_eligibility(),dtype=int)
 slots=np.asarray(s.people.slot)[eligible].astype(int);d=iv.coverage_dist
 bg=type(d.rng.bit_generator)(0);bg.state=copy.deepcopy(d.history[0]);bg=bg.jumped(jumps=d.dt_jump_size*(int(iv.ti)+1))
 u=np.random.Generator(bg).random(int(slots.max())+1,dtype=q.ss.dtypes.float)[slots]
 # Strong float64 matches campaign's np.float64 probability scalar; unlike a
 # Python float it does not round the threshold to uniform's float32 dtype.
 return eligible,eligible[u<np.float64(cov)]
