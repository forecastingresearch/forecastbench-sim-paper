"""Post-rescore reporting diagnostics; no simulation or external calls."""
import json,csv,hashlib,time
from pathlib import Path
import numpy as np
from scipy.stats import rankdata,spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent;R=O/'rescore'
read=lambda n:list(csv.DictReader((R/n).open()))
def table(name,rows):
 with (R/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
success=json.loads((R/'SUCCESS.json').read_text());assert success['status']=='PASS'
arr=np.load(R/'bootstrap_arrays.npz');old=arr['old'];new=arr['new'];boot=arr['scores'];F=arr['forecasts'];roster=json.loads((R/'roster.json').read_text());truth=read('truths_quantiles_floors.csv');ranks=[]
assert len(truth)==32 and np.all(np.diff(F,axis=2)[np.isfinite(np.diff(F,axis=2))]>=0)
for j,it in enumerate(truth):
 ids=np.flatnonzero(np.isfinite(new[j]));a=rankdata(old[j,ids]);b=rankdata(new[j,ids]);bb=rankdata(boot[:,j,ids],axis=1)
 for k,mi in enumerate(ids):ranks.append(dict(source=it['source'],item=it['item'],model=roster[mi]['openrouter_id'],old_rank=a[k],new_rank=b[k],rank_move=a[k]-b[k],new_rank_mc_lo=np.quantile(bb[:,k],.025),new_rank_mc_hi=np.quantile(bb[:,k],.975)))
table('item_ranks.csv',ranks)
# Half-sample oracle generalization diagnostic: quantile estimation optimism.
Y=np.load(R/'production_arrays.npz')['outcomes'];taus=[.1,.25,.5,.75,.9]
def loss(q,y):return sum(2/5*np.mean(np.where(y-x>=0,t*(y-x),(t-1)*(y-x))) for x,t in zip(q,taus))
optim=[]
for wi in range(4):
 for ai in range(4):
  for hi,h in enumerate([40,60]):
   y=Y[wi,:,ai,hi];a=y[:500];b=y[500:];qa=np.quantile(a,taus,method='inverted_cdf');qb=np.quantile(b,taus,method='inverted_cdf')
   optim.append(dict(world=f'w{wi}',coverage=[0,.25,.5,.9][ai],horizon=h,full_empirical_floor=loss(np.quantile(y,taus,method='inverted_cdf'),y),half_training_floor=(loss(qa,a)+loss(qb,b))/2,half_cross_evaluated_floor=(loss(qa,b)+loss(qb,a))/2,half_optimism=(loss(qa,b)+loss(qb,a)-loss(qa,a)-loss(qb,b))/2))
table('floor_split_diagnostic.csv',optim)
coverage=read('forecast_coverage.csv');rows=[]
for s in sorted({r['source'] for r in coverage}):
 for m in roster:
  cells=[r for r in coverage if r['source']==s and r['model']==m['openrouter_id']]
  rows.append(dict(source=s,model=m['openrouter_id'],expected_calls=sum(int(r['expected']) for r in cells),actual_calls=sum(int(r['n']) for r in cells),items_with_answer=sum(int(r['n'])>0 for r in cells),expected_items=len(cells),cells_below_planned_reps=sum(int(r['n'])<int(r['expected']) for r in cells),cells_with_duplicate_rep=sum(int(r['n'])>int(r['distinct_reps']) for r in cells)))
table('coverage_summary.csv',rows)
# Two score/rank panels and distributions: point estimates plus fixed-panel MC intervals.
scores=read('model_scores_ranks.csv');fig,axes=plt.subplots(1,2,figsize=(11,4.5))
for ax,group,title in zip(axes,['cont_uncond','interventional_pooled'],['Continuous baseline','Vaccine arms pooled']):
 rs=[r for r in scores if r['group']==group and r['horizon']=='pooled'];a=np.array([float(r['old_excess']) for r in rs]);b=np.array([float(r['new_excess']) for r in rs]);lo=np.array([float(r['score_mc_lo']) for r in rs]);hi=np.array([float(r['score_mc_hi']) for r in rs]);ax.errorbar(a,b,yerr=[b-lo,hi-b],fmt='o',ms=4,capsize=2,alpha=.8);end=max(a.max(),b.max())*1.07;ax.plot([0,end],[0,end],'--',color='grey');ax.set(xlabel='Original normalized excess',ylabel='Fixed-state normalized excess',title=title+f' (n={len(rs)})');ax.grid(alpha=.15)
fig.suptitle('Retrospective rescore; bars: 95% replay-bootstrap intervals');fig.tight_layout();fig.savefig(R/'score_comparison.png',dpi=180);fig.savefig(R/'score_comparison.pdf');plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(11,7));colors=['#333333','#4477aa','#228833','#cc6677']
for wi,ax in enumerate(axes.flat):
 for ai,(cov,col) in enumerate(zip([0,25,50,90],colors)):
  sy=np.sort(Y[wi,:,ai,1]);ax.step(sy,np.arange(1,1001)/1000,label=f'{cov}% coverage',color=col)
 ax.set(title=f'World {wi}: day-60 additional infections',xlabel='People infected after day 20',ylabel='Empirical CDF');ax.grid(alpha=.15)
axes[0,0].legend(fontsize=8);fig.tight_layout();fig.savefig(R/'fixed_state_cdfs.png',dpi=180);fig.savefig(R/'fixed_state_cdfs.pdf');plt.close(fig)
for p,h in json.loads((O/'analysis_and_manuscript_hashes.json').read_text()).items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
print(json.dumps(dict(status='PASS',item_ranks=len(ranks),quantile_forecasts_monotone=True,manuscript_and_frozen_analysis_unchanged=True)))
