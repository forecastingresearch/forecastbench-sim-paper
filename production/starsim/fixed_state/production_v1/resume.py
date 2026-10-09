import production as p
import oracle_precision as fix
import time,traceback
O=p.O
amend=p.json.loads((O/'ORACLE_AMENDMENT.json').read_text())
for name,h in amend['hashes'].items():assert p.sha(O/name)==h,name
assert p.sha(O/'PLAN.json')==amend['plan_sha256']
assert fix.tests()==amend['boundary_tests']
p.v.predict_uptake=fix.predict_uptake
start=time.time()
try:
 p.run()
 p.atomic(O/'RESUME_RESULT.json',dict(elapsed_s=time.time()-start,oracle_amendment_sha256=p.sha(O/'ORACLE_AMENDMENT.json'),sampling_plan_unchanged=True))
except Exception:
 p.atomic(O/f'RESUME_FAILURE_{int(time.time())}.json',dict(traceback=traceback.format_exc(),elapsed_s=time.time()-start));raise
