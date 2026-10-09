"""Offline retrospective rescore through unmodified paper score_all; never simulates."""
import sys,json,csv,hashlib,gzip,time,statistics,collections,runpy,warnings
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr,rankdata,binom,ks_2samp
START=time.time();O=Path(__file__).resolve().parent;A=Path('/Users/elsehow/Projects/iclr-2026');P=Path('/Users/elsehow/Projects/iclr-score-refresh/paper');R=O/'rescore';R.mkdir(exist_ok=True)
sys.path.insert(0,str(P/'data/starsim/scripts'));sys.argv=['rescore','--analysis-root',str(A)]
import build_excess as be
be.use_cached_runs(be.bt,A/'results/causal/rerun_lowest')
def dump(n,x):(R/n).write_text(json.dumps(x,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)))
def table(n,rows):
 if not rows:return
 with (R/n).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rho(x,y):return float(spearmanr(x,y).statistic)
def ci(x):return [float(v) for v in np.nanquantile(x,[.025,.975])]
plan=json.loads((O/'PLAN.json').read_text());assert sha(O/'PLAN.json')==(O/'PLAN.sha256').read_text().strip()
assert json.loads((O/'SUCCESS.json').read_text())['branches']==16000
inputs=dict(plan['inputs']);inputs[str(O/'PLAN.json')]=sha(O/'PLAN.json')
for root in [P/'data/starsim/scripts',A/'results/table',A/'results/causal/starsim_causal']:
 for p in root.glob('*.py'):inputs[str(p)]=sha(p)
inputs[str(A/'results/causal/starsim_causal/models.csv')]=sha(A/'results/causal/starsim_causal/models.csv')
for p in [P/'data/micropolis/micropolis_model_scores.csv',P/'data/appendix_tables/freeciv_models.tex',P/'data/starsim/starsim_excess_long.csv']:
 inputs[str(p)]=sha(p)
for source in be.bt.SOURCES.values():
 for p in source[3:5]:inputs[str(p)]=sha(p)
dump('input_hashes.json',inputs)
N=1000;B=plan['analysis']['replay_bootstrap'];MB=plan['analysis']['model_panel_bootstrap'];rng=np.random.default_rng(plan['analysis']['bootstrap_seed'])
Y=np.zeros((4,N,4,2));daily=np.zeros((4,N,4,61),dtype=np.int64);uptake=np.zeros((4,N,4),int);checks=0;elapsed=0;rootset=set();validation=[]
manifest=json.loads((O/'checkpoint_hashes.json').read_text());assert len(manifest)==4000
for job in plan['seeds']:
 wid=job['world'];wi=int(wid[1:]);rep=job['rep'];p=O/'checkpoints'/f'{wid}_{rep:04d}.json.gz';assert sha(p)==manifest[p.name]
 with gzip.open(p,'rt') as f:r=json.load(f)
 assert r['job']==job and r['plan_sha256']==sha(O/'PLAN.json') and len(r['arms'])==4
 checks+=r['checks'];elapsed+=r['elapsed_s']
 for root in r['roots'].values():assert root['root'] not in rootset;rootset.add(root['root'])
 for ai,row in enumerate(r['arms']):
  assert row['coverage']==plan['coverages'][ai] and row['eligible_count']==5000
  assert 0<=row['new40']<=row['new60']<=5000-plan['worlds'][wi]['c20']
  assert sum(row['daily'][21:41])==row['new40'] and sum(row['daily'][21:61])==row['new60']
  assert row['administered']==0 if ai==0 else 0<row['administered']<5000
  Y[wi,rep,ai]=[row['new40'],row['new60']];daily[wi,rep,ai]=row['daily'];uptake[wi,rep,ai]=row['administered']
assert len(rootset)==40000
for wi in range(4):assert np.all(daily[wi,:,:,:21]==daily[wi,0,0,:21])
np.savez_compressed(R/'production_arrays.npz',outcomes=Y,daily=daily,uptake=uptake)
for wi in range(4):
 for ai,cov in enumerate(plan['coverages']):validation.append(dict(world='w'+str(wi),coverage=cov,n=N,vaccinated_min=uptake[wi,:,ai].min(),vaccinated_max=uptake[wi,:,ai].max(),vaccinated_mean=uptake[wi,:,ai].mean(),mean40=Y[wi,:,ai,0].mean(),mean60=Y[wi,:,ai,1].mean(),min40=Y[wi,:,ai,0].min(),max60=Y[wi,:,ai,1].max()))
table('production_validation.csv',validation)
C,info=be.constants();assert C=={40:200.,60:300.};oldlong,oldpi=be.score_all(C)
saved=list(csv.DictReader((P/'data/starsim/starsim_excess_long.csv').open()));key=lambda r:tuple(str(r[k]) for k in ['model','question_type','condition','rung','horizon']);lookup={key(r):r for r in saved}
errors=[]
for r in oldlong:
 for k in ['excess','floor','crps','excess_raw']:
  if k in r and lookup[key(r)].get(k):errors.append(abs(float(f'{r[k]:.6g}')-float(lookup[key(r)][k])))
assert len(oldlong)==len(saved)==576 and max(errors)==0
roster=be.bt.load_roster();mids=[m.openrouter_id for m in roster];M=len(mids);dump('roster.json',[m.__dict__ for m in roster])
names=['cont_uncond','cont_int_c25','cont_int_c50','cont_int_c90'];items=[];forecasts=[];missing=[];coverage=[];dups=[];repeated=[];unknown=[]
for name,src in list(be.bt.SOURCES.items()):
 typ,cond,rung,rfile,wfile,tkey,tmpl=src;data=json.loads(wfile.read_text());rr=be.bt.load_rows(rfile);expected=3 if typ=='continuous' else 5
 for m in mids:
  for it in data['items']:
   rows=rr.get((m,it['item_id']),[]);reps=[r['rep'] for r in rows];counts=collections.Counter(reps)
   coverage.append(dict(source=name,model=m,item=it['item_id'],n=len(rows),expected=expected,distinct_reps=len(counts),reps=json.dumps(reps),included=bool(rows)))
   if len(rows)!=expected or len(counts)!=expected:missing.append(coverage[-1])
   for rep,n in counts.items():
    if n>1:dups.append(dict(source=name,model=m,item=it['item_id'],rep=rep,n=n))
   vals=[tuple(r[k] for k in be.QK) if typ=='continuous' else (r['p'],) for r in rows]
   if len(vals)>len(set(vals)):repeated.append(dict(source=name,model=m,item=it['item_id'],n=len(vals),distinct_answers=len(set(vals))))
 for m,iid in rr:
  if m not in mids or iid not in {i['item_id'] for i in data['items']}:unknown.append(dict(source=name,model=m,item=iid))
 if name not in names:continue
 ai=names.index(name)
 for it in data['items']:
  wi=int(it['world_id'][1:]);hi=[40,60].index(it['horizon']);ys=Y[wi,:,ai,hi];oldtruth=it[tkey].copy();tq=np.quantile(ys,be.TAU,method='inverted_cdf');it[tkey]=dict(samples=ys.tolist(),**dict(zip(be.QK,tq.tolist())))
  items.append(dict(source=name,item=it['item_id'],world=it['world_id'],wi=wi,ai=ai,hi=hi,horizon=it['horizon'],upper=it['upper'],oldtruth=oldtruth))
  forecasts.append([np.array([statistics.median(r[k] for r in rr[m,it['item_id']]) for k in be.QK]) if (m,it['item_id']) in rr else np.full(5,np.nan) for m in mids])
 wp=R/(name+'_worlds.json');wp.write_text(json.dumps(data,indent=2));be.bt.SOURCES[name]=(typ,cond,rung,rfile,wp,tkey,tmpl)
table('forecast_coverage.csv',coverage);dump('forecast_audit.json',dict(nonstandard_cells=missing,duplicate_rep_keys=dups,repeated_answer_cells=repeated,unknown_cells=unknown))
newlong,newpi=be.score_all(C);table('paper_original_long.csv',oldlong);table('paper_fixed_state_long.csv',newlong)
# Independently vectorized losses are checked against the actual scoring function.
F=np.array(forecasts);K=len(items);assert K==32
old=np.full((K,M),np.nan);new=old.copy();boot=np.full((B,K,M),np.nan);bq=np.zeros((B,K,5));bf=np.zeros((B,K));pointq=np.zeros((K,5));pointfloor=np.zeros(K)
indices={wi:rng.integers(0,N,(B,N)) for wi in range(4)}
weights={wi:np.apply_along_axis(lambda a:np.bincount(a,minlength=N),1,ix)/N for wi,ix in indices.items()}
truthrows=[];itemrows=[];convergence=[]
for j,it in enumerate(items):
 ys=Y[it['wi'],:,it['ai'],it['hi']];qs=np.quantile(ys,be.TAU,method='inverted_cdf');floor=be.crps5(qs,ys);pointq[j]=qs;pointfloor[j]=floor
 by=ys[indices[it['wi']]];bqs=np.quantile(by,be.TAU,axis=1,method='inverted_cdf').T;bq[:,j]=bqs
 bfloor=np.zeros(B)
 for t,x in zip(be.TAU,bqs.T):
  d=by-x[:,None];bfloor+=2/5*np.where(d>=0,t*d,(t-1)*d).mean(axis=1)
 bf[:,j]=bfloor
 loss=np.zeros((N,M))
 for qi,t in enumerate(be.TAU):
  d=ys[:,None]-F[j,:,qi];loss+=2/5*np.where(d>=0,t*d,(t-1)*d)
 boot[:,j]=(weights[it['wi']]@loss-bfloor[:,None])/C[it['horizon']]
 ot=it['oldtruth'];oq=np.quantile(ot['samples'],be.TAU,method='inverted_cdf');of=be.crps5(oq,ot['samples'])
 tr=dict(source=it['source'],item=it['item'],world=it['world'],horizon=it['horizon'],n=N,old_n=len(ot['samples']),old_floor=of,new_floor=floor,floor_delta=floor-of,floor_mc_lo=ci(bfloor)[0],floor_mc_hi=ci(bfloor)[1],old_mean=np.mean(ot['samples']),new_mean=ys.mean(),old_sd=np.std(ot['samples'],ddof=1),new_sd=ys.std(ddof=1),support_upper=it['upper'])
 sy=np.sort(ys)
 for qi,(k,t) in enumerate(zip(be.QK,be.TAU)):
  # Distribution-free order-statistic interval; discrete distributions conservative.
  lo=max(0,int(binom.ppf(.025,N,t))-1);hi=min(N-1,int(binom.ppf(.975,N,t)))
  tr.update({k+'_old':oq[qi],k+'_new':qs[qi],k+'_delta':qs[qi]-oq[qi],k+'_order_lo':sy[lo],k+'_order_hi':sy[hi],k+'_mc_lo':ci(bqs[:,qi])[0],k+'_mc_hi':ci(bqs[:,qi])[1]})
 truthrows.append(tr)
 for mi,m in enumerate(mids):
  if np.isnan(F[j,mi]).any():continue
  a=oldpi[it['source']][m][it['item']];b=newpi[it['source']][m][it['item']];old[j,mi]=a['excess'];new[j,mi]=b['excess'];assert np.isclose(loss[:,mi].mean(),b['crps'],atol=1e-10)
  itemrows.append(dict(source=it['source'],item=it['item'],model=m,C=C[it['horizon']],old_excess=a['excess'],new_excess=b['excess'],delta=b['excess']-a['excess'],new_crps=b['crps'],new_floor=b['floor'],new_excess_raw=b['excess_raw'],mc_lo=ci(boot[:,j,mi])[0],mc_hi=ci(boot[:,j,mi])[1],forecast_above_support=int(sum(F[j,mi]>it['upper']))))
 for n in plan['checkpoints']:
  qn=np.quantile(ys[:n],be.TAU,method='inverted_cdf');fn=be.crps5(qn,ys[:n]);row=dict(source=it['source'],item=it['item'],N=n,floor=fn,floor_delta_final=fn-floor,max_quantile_delta_final=np.max(abs(qn-qs)))
  for k,val in zip(be.QK,qn):row[k]=val
  if n==1000:row['split_half_ks']=ks_2samp(ys[:500],ys[500:]).statistic
  convergence.append(row)
 print('truth+bootstrap',it['source'],it['item'],flush=True)
table('truths_quantiles_floors.csv',truthrows);table('item_scores.csv',itemrows);table('convergence.csv',convergence)
assert np.nanmin(new)>-1e-10
np.savez_compressed(R/'bootstrap_arrays.npz',scores=boot,quantiles=bq,floors=bf,old=old,new=new,forecasts=F)
# Panels and paired model bootstrap: uncertainty about selected models, NOT replay error.
groups={s:[j for j,it in enumerate(items) if it['source']==s] for s in names};groups['interventional_pooled']=list(range(8,32));groups['all_continuous']=list(range(32))
# Do not rely on order silently.
assert all(items[j]['source']!='cont_uncond' for j in groups['interventional_pooled'])
aggregate=[];associations=[];panels={};group_arrays={};convscore=[]
def association(label,x,a,b,bb,ids,horizon,kind='loss'):
 # Positive skill association means higher external score accompanies lower loss.
 sign=-1 if kind=='loss' else 1;ro=rho(x,a)*sign;rn=rho(x,b)*sign
 ii=rng.integers(0,len(x),(MB,len(x)));ob=[];nb=[]
 with warnings.catch_warnings():
  warnings.simplefilter('ignore')
  for ix in ii:ob.append(sign*rho(x[ix],a[ix]));nb.append(sign*rho(x[ix],b[ix]))
 rb=np.array([sign*rho(x,br) for br in bb]);nb=np.array(nb);ob=np.array(ob)
 panelkey=f'{label}|{horizon}|{kind}';panels[panelkey]=[mids[i] for i in ids]
 associations.append(dict(group=label,horizon=horizon,against=kind,n=len(x),old_skill_rho=ro,new_skill_rho=rn,delta=rn-ro,old_panel_lo=ci(ob)[0],old_panel_hi=ci(ob)[1],new_panel_lo=ci(nb)[0],new_panel_hi=ci(nb)[1],delta_panel_lo=ci(nb-ob)[0],delta_panel_hi=ci(nb-ob)[1],new_replay_lo=ci(rb)[0],new_replay_hi=ci(rb)[1],delta_replay_lo=ci(rb-ro)[0],delta_replay_hi=ci(rb-ro)[1],panel=panelkey))
for group,jj in groups.items():
 for h in [40,60,'pooled']:
  js=[j for j in jj if h=='pooled' or items[j]['horizon']==h];ids=np.flatnonzero(np.isfinite(old[js]).all(axis=0)&np.isfinite(new[js]).all(axis=0))
  a=old[js][:,ids].mean(axis=0);b=new[js][:,ids].mean(axis=0);bb=boot[:,js][:,:,ids].mean(axis=1);ra=rankdata(a);rb=rankdata(b);br=rankdata(bb,axis=1)
  group_arrays[group,h]=(ids,a,b,bb);panels[f'{group}|{h}|scores']=[mids[i] for i in ids]
  for k,mi in enumerate(ids):aggregate.append(dict(group=group,horizon=h,model=mids[mi],name=roster[mi].name,n_models=len(ids),n_items=len(js),old_excess=a[k],new_excess=b[k],delta=b[k]-a[k],old_rank=ra[k],new_rank=rb[k],rank_move=ra[k]-rb[k],score_mc_lo=ci(bb[:,k])[0],score_mc_hi=ci(bb[:,k])[1],rank_mc_lo=ci(br[:,k])[0],rank_mc_hi=ci(br[:,k])[1]))
  for against in ['eci','fb_overall']:
   valid=np.array([k for k,i in enumerate(ids) if getattr(roster[i],against) is not None]);si=ids[valid];x=np.array([getattr(roster[i],against) for i in si]);before=len(associations)
   association(group,x,a[valid],b[valid],bb[:,valid],si,h,'loss');associations[-1]['against']=against;oldkey=associations[-1]['panel'];newkey=oldkey+'|'+against;panels[newkey]=panels[oldkey];associations[-1]['panel']=newkey
  for n in plan['checkpoints']:
   v0=[]
   for j in js:
    it=items[j];ys=Y[it['wi'],:n,it['ai'],it['hi']];floor=be.crps5(np.quantile(ys,be.TAU,method='inverted_cdf'),ys)
    v0.append([(be.crps5(F[j,i],ys)-floor)/C[it['horizon']] for i in ids])
   v0=np.mean(v0,axis=0);convscore.append(dict(group=group,horizon=h,N=n,n_models=len(ids),max_score_delta_final=np.max(abs(v0-b)),rank_agreement_final=rho(v0,b)))
table('model_scores_ranks.csv',aggregate);table('score_convergence.csv',convscore)
# Combined fit: unchanged other engines/binary. Use exact linear least-squares map
# of logged observed cells for fast replay propagation; verify against paper ALS.
sys.argv=['combined','--analysis-root',str(A),'--paper-root',str(P),'--out',str(R/'unused.json')]
g=runpy.run_path(str(P/'data/starsim/scripts/combined_score.py'),run_name='rescore_import');star=g['starsim']('excess');short=g['fg'].SHORT;combined=[]
for fitname,others in [('six',[g['MICRO']]),('ten',[g['MICRO'],g['FREE']])]:
 columns=[{m:src[m][k] for m in g['MODELS']} for src in others for k in next(iter(src.values()))]
 columns.extend({m:star[m][k] for m in g['MODELS']} for k in next(iter(star.values())))
 L=np.array([[c[m] if c[m] is not None else np.nan for c in columns] for m in g['MODELS']]);newL=L.copy();BL=np.broadcast_to(L,(B,*L.shape)).copy();labels=list(next(iter(star.values())))
 for group,k in [('cont_uncond','StarSim continuous excess CRPS'),('interventional_pooled','StarSim interventional excess CRPS')]:
  col=len(columns)-3+labels.index(k);ids,a,b,bb=group_arrays[group,'pooled']
  for j,mi in enumerate(ids):
   row=g['MODELS'].index(short[mids[mi]]);newL[row,col]=b[j];BL[:,row,col]=bb[:,j]
 oldtheta=g['fit'](L)[0];theta=g['fit'](newL)[0];mask=np.isfinite(L);coords=np.argwhere(mask);D=np.zeros((len(coords),L.shape[1]+M))
 for r,(mi,col) in enumerate(coords):D[r,col]=1;D[r,L.shape[1]+mi]=-1
 transform=np.linalg.pinv(D)[L.shape[1]:];transform-=transform.mean(axis=0)
 calc=lambda losses:np.log(np.maximum(losses[...,mask],1e-4))@transform.T
 assert np.allclose(calc(L),oldtheta,atol=1e-9) and np.allclose(calc(newL),theta,atol=1e-9)
 bt=calc(BL);oldrank=rankdata(-oldtheta);nr=rankdata(-theta);btr=rankdata(-bt,axis=1)
 for mi,m in enumerate(g['MODELS']):combined.append(dict(fit=fitname,model=m,old_theta=oldtheta[mi],new_theta=theta[mi],delta=theta[mi]-oldtheta[mi],old_rank=oldrank[mi],new_rank=nr[mi],theta_mc_lo=ci(bt[:,mi])[0],theta_mc_hi=ci(bt[:,mi])[1],rank_mc_lo=ci(btr[:,mi])[0],rank_mc_hi=ci(btr[:,mi])[1]))
 assert [short[m] for m in mids]==g['MODELS']
 for against in ['eci','fb_overall']:
  ids=np.array([i for i,m in enumerate(roster) if getattr(m,against) is not None]);x=np.array([getattr(roster[i],against) for i in ids]);association('combined_'+fitname,x,oldtheta[ids],theta[ids],bt[:,ids],ids,'pooled','theta');associations[-1]['against']=against;pk=associations[-1]['panel'];panels[pk+'|'+against]=panels[pk];associations[-1]['panel']=pk+'|'+against
# Delete intermediate alias panel keys; only explicit references needed.
used={a['panel'] for a in associations}|{k for k in panels if k.endswith('|scores')};panels={k:v for k,v in panels.items() if k in used}
table('combined_scores_ranks.csv',combined);table('associations.csv',associations);dump('panels.json',panels)
for p,h in inputs.items():assert sha(p)==h,p
scales={h:be.one_sig(float(np.median([np.quantile(Y[it['wi'],:,it['ai'],it['hi']],.95)-np.quantile(Y[it['wi'],:,it['ai'],it['hi']],.05) for it in items if it['horizon']==h]))) for h in [40,60]}
dump('SUCCESS.json',dict(status='PASS',production_branches=16000,production_checks=checks,checkpoint_elapsed_sum_s=elapsed,distinct_roots=len(rootset),original_paper_rows_reproduced=576,max_serialized_error=max(errors),C_fixed=C,C_if_reestimated_diagnostic_only=scales,replay_bootstrap=B,model_panel_bootstrap=MB,elapsed_s=time.time()-START,nonstandard_repetition_cells=len(missing),duplicate_rep_keys=len(dups),repeated_answer_cells=len(repeated),new_calls=0,retrospective=True,fixed_hidden_state=True))
print(json.dumps(json.loads((R/'SUCCESS.json').read_text())),flush=True)
