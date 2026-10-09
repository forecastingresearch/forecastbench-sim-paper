"""Independent array-only recipient audit over all saved production arms."""
from pathlib import Path
import json,gzip,hashlib
import numpy as np
O=Path(__file__).resolve().parent
assert json.loads((O/'SUCCESS.json').read_text())['branches']==16000
hashobj=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,allow_nan=True).encode()).hexdigest()
rows=[];arms=0
for p in sorted((O/'checkpoints').glob('*.json.gz')):
 with gzip.open(p,'rt') as f:r=json.load(f)
 roots=[v for k,v in r['roots'].items() if k.endswith('coverage_dist')];assert len(roots)==1
 root=roots[0];bg=np.random.default_rng(root['seed']).bit_generator;assert hashobj(bg.state)==root['root']
 u=np.random.Generator(bg.jumped(jumps=22000)).random(5000,dtype=np.float32)
 for a in r['arms']:
  cov=a['coverage'];ids=np.flatnonzero(u.astype(np.float64)<np.float64(cov))
  assert len(ids)==a['administered'] and hashobj(ids.tolist())==a['vaccinated_ids_sha256'],(r['job'],cov)
  arms+=1
  wrong=np.flatnonzero((u<cov)!=(u.astype(np.float64)<np.float64(cov)))
  if len(wrong):rows.append(dict(job=r['job'],coverage=cov,ids=wrong.tolist(),uniforms=u[wrong].tolist()))
assert arms==16000
out=dict(status='PASS',arms=arms,simulation_steps=0,weak_scalar_discrepancies=rows,method='PCG64 root hash verified; jump 22000; regenerate float32 uniforms; independently upcast to float64 before comparison; compare saved recipient ID hash and count')
(O/'UPTAKE_VERIFICATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
