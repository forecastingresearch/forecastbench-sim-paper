"""Compare two StarSim table builds (long CSVs): the locked 2026-09-08 run at
vendor-default reasoning vs a rerun (e.g. results/causal/rerun_low, effort=low).

  uv run python results/table/compare_runs.py results/table results/causal/rerun_low/table
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

from scipy.stats import spearmanr

METRIC = {"binary": "recovered", "continuous": "skill"}
COLS = [("binary", "unconditional", "-"), ("continuous", "unconditional", "-"),
        ("continuous", "interventional", "pooled(c25,c50,c90)"), ("continuous", "interventional", "c25"),
        ("continuous", "interventional", "c50"), ("continuous", "interventional", "c90"),
        ("binary", "interventional", "c90"), ("binary", "interventional", "hold")]


def load(d: Path):
    rows = list(csv.DictReader(open(d / "starsim_results_long.csv")))
    out = defaultdict(dict)   # (qtype, cond, rung, horizon) -> model -> row
    for r in rows:
        out[(r["question_type"], r["condition"], r["rung"], r["horizon"])][r["model"]] = r
    return out


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main(a: Path, b: Path):
    A, B = load(a), load(b)
    print(f"A = {a}\nB = {b}\n")
    print(f"{'column':44s} {'rho_A':>7s} {'rho_B':>7s} {'n':>3s} {'mean_A':>7s} {'mean_B':>7s} {'rt_A':>7s} {'rt_B':>7s} {'$A':>7s} {'$B':>7s}")
    for qtype, cond, rung in COLS:
        key = (qtype, cond, rung, "pooled")
        ra, rb = A.get(key, {}), B.get(key, {})
        models = [m for m in ra if m in rb and ra[m]["complete"] == "True" and rb[m]["complete"] == "True"]
        met = METRIC[qtype]
        xa = [f(ra[m][met]) for m in models]; xb = [f(rb[m][met]) for m in models]
        eci = [f(ra[m]["eci"]) for m in models]
        rho_a = spearmanr(eci, xa).correlation if len(models) > 3 else float("nan")
        rho_b = spearmanr(eci, xb).correlation if len(models) > 3 else float("nan")
        rt = lambda R: sum(f(R[m]["reasoning_tokens_mean"]) or 0 for m in models) / max(len(models), 1)
        cost = lambda R: sum(f(R[m]["cost_usd"]) or 0 for m in R)
        print(f"{qtype+' '+cond+' '+rung:44s} {rho_a:7.2f} {rho_b:7.2f} {len(models):3d} "
              f"{sum(xa)/len(xa):7.3f} {sum(xb)/len(xb):7.3f} {rt(ra):7.0f} {rt(rb):7.0f} {cost(ra):7.2f} {cost(rb):7.2f}")
    print("\nPer-model deltas (B - A), pooled headline columns; * = incomplete in B")
    heads = [("binary", "unconditional", "-"), ("continuous", "unconditional", "-"),
             ("continuous", "interventional", "pooled(c25,c50,c90)")]
    ref = A[("binary", "unconditional", "-", "pooled")]
    print(f"{'model':40s} {'eci':>6s} " + " ".join(f"{'d_'+h[0][:3]+'_'+h[2][:4]:>12s}" for h in heads) + "   rt_A -> rt_B")
    for m in sorted(ref, key=lambda m: -f(ref[m]["eci"])):
        cells = []
        for qtype, cond, rung in heads:
            ra = A[(qtype, cond, rung, "pooled")].get(m); rb = B[(qtype, cond, rung, "pooled")].get(m)
            va = f(ra[METRIC[qtype]]) if ra else None; vb = f(rb[METRIC[qtype]]) if rb else None
            flag = "*" if rb and rb["complete"] != "True" else " "
            cells.append(f"{(vb - va):+11.3f}{flag}" if va is not None and vb is not None else f"{'–':>12s}")
        rta = f(A[("continuous", "interventional", "c50", "pooled")].get(m, {}).get("reasoning_tokens_mean")) or 0
        rtb = f(B[("continuous", "interventional", "c50", "pooled")].get(m, {}).get("reasoning_tokens_mean")) or 0
        print(f"{m:40s} {f(ref[m]['eci']):6.1f} " + " ".join(cells) + f"   {rta:6.0f} -> {rtb:6.0f}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
