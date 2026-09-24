"""Rep-bootstrap of the interventional capability gradient: how much does rho vs ECI
move under the run's own rep-to-rep noise? For each draw, pick one rep per (model, item)
instead of the median, score, take the mean skill over rungs, and compute Spearman rho
vs ECI over the models complete in every rung. Prints the rho distribution per run.

  uv run python results/table/rep_bootstrap.py [--runs results/causal/rerun_low] [--draws 400]
"""
import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_table as bt  # noqa: E402

RUNGS = ("cont_int_c25", "cont_int_c50", "cont_int_c90")


def load(name):
    qtype, cond, rung, rfile, wfile, truth_key, template = bt.SOURCES[name]
    items = {i["item_id"]: i for i in json.load(open(wfile))["items"]}
    reps = bt.load_rows(rfile)
    return items, reps, truth_key


def skill_of(q, item, truth_key, name):
    tr = item[truth_key]; ys = tr["samples"]
    ikey = (name, item["item_id"], truth_key)
    crps = bt.crps_vs_samples(q, ikey, ys)
    oracle = bt.crps_vs_samples({k: tr[k] for k in bt.QKEYS}, ikey, ys)
    clim = bt.crps_vs_samples({k: bt.CLIM[str(item["horizon"])][k] for k in bt.QKEYS}, ikey, ys)
    return 1 - (crps - oracle) / (clim - oracle)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=None)
    ap.add_argument("--draws", type=int, default=400)
    ap.add_argument("--rungs", default="c25,c50,c90")
    a = ap.parse_args()
    if a.runs:
        bt.use_runs(Path(a.runs).resolve())
    rungs = [f"cont_int_{r}" for r in a.rungs.split(",")]
    roster = bt.load_roster()
    eci = {m.openrouter_id: m.eci for m in roster}
    data = {name: load(name) for name in rungs}
    # models complete in every rung
    complete = [m.openrouter_id for m in roster
                if all(all((m.openrouter_id, iid) in data[n][1] for iid in data[n][0]) for n in rungs)]
    rng = random.Random(0)
    rhos = []; per_model = defaultdict(list)
    for d in range(a.draws):
        scores = {}
        for mid in complete:
            vals = []
            for n in rungs:
                items, reps, tk = data[n]
                for iid, it in items.items():
                    rs = reps[(mid, iid)]
                    r = rng.choice(rs)
                    vals.append(skill_of({k: r[k] for k in bt.QKEYS}, it, tk, n))
            scores[mid] = float(np.mean(vals)); per_model[mid].append(scores[mid])
        rhos.append(spearmanr([eci[m] for m in complete], [scores[m] for m in complete]).correlation)
    # the median-over-reps point estimate, as the table computes it
    point = {}
    for mid in complete:
        vals = []
        for n in rungs:
            items, reps, tk = data[n]
            for iid, it in items.items():
                vals.append(bt.item_scores_cont(reps[(mid, iid)], it, tk, n)["skill"])
        point[mid] = float(np.mean(vals))
    rho_point = spearmanr([eci[m] for m in complete], [point[m] for m in complete]).correlation
    lo, hi = np.percentile(rhos, [2.5, 97.5])
    print(f"runs={a.runs or 'locked'} rungs={a.rungs} n_models={len(complete)} draws={a.draws}")
    print(f"  rho (median-over-reps, as in the table) = {rho_point:.2f}")
    print(f"  rho under one-rep-per-item draws: mean {np.mean(rhos):.2f}, 95% [{lo:.2f}, {hi:.2f}]")
    sd = {m: float(np.std(per_model[m])) for m in complete}
    print(f"  per-model skill sd across draws: median {np.median(list(sd.values())):.3f}, max {max(sd.values()):.3f} ({max(sd, key=sd.get).split('/')[-1]})")


if __name__ == "__main__":
    main()
