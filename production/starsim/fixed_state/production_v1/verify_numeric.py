"""Resolve numeric-library warnings with finite checks and independent non-BLAS sums."""
import sys,json,csv,runpy,warnings
from pathlib import Path
import numpy as np
O=Path(__file__).resolve().parent;R=O/'rescore';A=Path('/Users/elsehow/Projects/iclr-2026');P=Path('/Users/elsehow/Projects/iclr-score-refresh/paper')
sys.path.insert(0,str(P/'data/starsim/scripts'));sys.argv=['verify','--analysis-root',str(A)];import build_excess as be
plan=json.loads((O/'PLAN.json').read_text());rng=np.random.default_rng(plan['analysis']['bootstrap_seed']);B=1000;N=1000
indices={wi:rng.integers(0,N,(B,N)) for wi in range(4)}
weights={wi:np.apply_along_axis(lambda a:np.bincount(a,minlength=N),1,ix)/N for wi,ix in indices.items()}
archive=np.load(R/'bootstrap_arrays.npz');a={k:archive[k] for k in archive.files};Y=np.load(R/'production_arrays.npz')['outcomes'];items=list(csv.DictReader((R/'truths_quantiles_floors.csv').open()));names=['cont_uncond','cont_int_c25','cont_int_c50','cont_int_c90'];C={40:200,60:300};mx=0;directmax=0;pointmax=0
for j,it in enumerate(items):
 wi=int(it['world'][1:]);ai=names.index(it['source']);h=int(it['horizon']);hi=[40,60].index(h);y=Y[wi,:,ai,hi];present=np.flatnonzero(np.isfinite(a['forecasts'][j]).all(axis=1));loss=np.zeros((N,len(present)))
 for k,t in enumerate(be.TAU):
  d=y[:,None]-a['forecasts'][j,present,k];loss+=2/5*np.where(d>=0,t*d,(t-1)*d)
 expected=(np.einsum('bn,nm->bm',weights[wi],loss,optimize=False)-a['floors'][:,j,None])/C[h]
 actual=a['scores'][:,j,present];assert expected.shape==actual.shape and np.isfinite(actual).all();mx=max(mx,float(np.max(abs(expected-actual))));assert np.allclose(expected,actual,atol=1e-11,rtol=1e-12)
 for b in [0,111,222,333,444,555,666,777,888,999]:
  ys=y[indices[wi][b]];floor=be.crps5(np.quantile(ys,be.TAU,method='inverted_cdf'),ys)
  assert np.isclose(floor,a['floors'][b,j],atol=1e-11)
  for m in present:
   ex=(be.crps5(a['forecasts'][j,m],ys)-floor)/C[h];directmax=max(directmax,abs(ex-a['scores'][b,j,m]));assert np.isclose(ex,a['scores'][b,j,m],atol=1e-11,rtol=1e-12)
 assert np.isfinite(a['quantiles'][:,j]).all() and np.isfinite(a['floors'][:,j]).all()
# Verify every combined-score MC interval from non-BLAS linear sums, and
# check selected bootstrap fitted scores through original iterative fitter.
sys.argv=['combined','--analysis-root',str(A),'--paper-root',str(P),'--out',str(R/'unused.json')]
g=runpy.run_path(str(P/'data/starsim/scripts/combined_score.py'),run_name='verify_import');star=g['starsim']('excess');M=len(g['MODELS']);records=list(csv.DictReader((R/'combined_scores_ranks.csv').open()));cm=0;fiterr=0
for fitname,others in [('six',[g['MICRO']]),('ten',[g['MICRO'],g['FREE']])]:
 columns=[{m:src[m][k] for m in g['MODELS']} for src in others for k in next(iter(src.values()))];columns.extend({m:star[m][k] for m in g['MODELS']} for k in next(iter(star.values())))
 L=np.array([[c[m] if c[m] is not None else np.nan for c in columns] for m in g['MODELS']]);BL=np.broadcast_to(L,(B,*L.shape)).copy();labels=list(next(iter(star.values())))
 for js,label in [(list(range(8)),'StarSim continuous excess CRPS'),(list(range(8,32)),'StarSim interventional excess CRPS')]:
  col=len(columns)-3+labels.index(label);ids=np.flatnonzero(np.isfinite(a['new'][js]).all(axis=0));vals=a['scores'][:,js][:,:,ids].mean(axis=1)
  for k,mi in enumerate(ids):BL[:,mi,col]=vals[:,k]
 mask=np.isfinite(L);coords=np.argwhere(mask);D=np.zeros((len(coords),L.shape[1]+M))
 for r,(mi,col) in enumerate(coords):D[r,col]=1;D[r,L.shape[1]+mi]=-1
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');transform=np.linalg.pinv(D)[L.shape[1]:]
 transform-=transform.mean(axis=0);assert np.isfinite(transform).all();logs=np.log(np.maximum(BL[:,mask],1e-4));assert np.isfinite(logs).all()
 theta=np.einsum('bn,mn->bm',logs,transform,optimize=False);assert np.isfinite(theta).all()
 for j,m in enumerate(g['MODELS']):
  r=next(r for r in records if r['fit']==fitname and r['model']==m);q=np.quantile(theta[:,j],[.025,.975]);cm=max(cm,abs(q[0]-float(r['theta_mc_lo'])),abs(q[1]-float(r['theta_mc_hi'])));assert np.allclose(q,[float(r['theta_mc_lo']),float(r['theta_mc_hi'])],atol=1e-11,rtol=1e-12)
 for b in [0,249,499,749,999]:
  ref=g['fit'](BL[b])[0];err=np.max(abs(ref-theta[b]));fiterr=max(fiterr,float(err));assert err<1e-9
for name in ['associations.csv','model_scores_ranks.csv','combined_scores_ranks.csv','truths_quantiles_floors.csv']:
 for r in csv.DictReader((R/name).open()):
  assert all(v.lower() not in ['nan','inf','-inf'] for v in r.values()),(name,r)
out=dict(status='PASS',all_available_bootstrap_scores_finite=True,max_nonblas_bootstrap_difference=mx,max_original_scorer_bootstrap_difference=directmax,original_scorer_bootstrap_items_checked=32*10,max_combined_ci_nonblas_difference=cm,max_combined_original_ALS_difference=fiterr,combined_ALS_bootstrap_draws_checked=10,warnings='Original NumPy matmul warnings retained in rescore.log; independent finite, non-BLAS, actual-scorer and ALS checks found no corresponding numerical error. Underlying library warning cause not established.')
(O/'NUMERIC_VERIFICATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
