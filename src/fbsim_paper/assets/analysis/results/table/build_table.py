"""StarSim results table for the FBSim paper (deliverable of 2026-09-08).

Reads the locked StarSim runs under results/causal/ and writes, per model:
scores decomposed by question type x condition x horizon (day 40 / day 60 /
pooled), plus calls and OpenRouter cost per cell. Nothing is re-elicited.

Question types and where they come from
  binary        starsim_causal v2, baseline condition (unconditional). Two-region
                world; "Will Riverton have more cumulative infections than
                Southbay at day t?"; 4 worlds x 2 horizons = 8 items; K = 5 reps.
                Truth P* in {0, 1}. Template: cases_comparative.
  continuous    starsim_single v4, baseline condition (unconditional). One
                region; "How many people will be newly infected between day 20
                and day t?"; quantiles p10..p90; 8 items; K = 3. Truth = the
                matched-seed distribution. Template: new_infections.
  interventional (continuous, headline)  starsim_single v4, intervention
                condition: same items + "vaccination on day 21, 95% efficacy,
                c% coverage", c in {25, 50, 90}; pooled over rungs and per rung.
  interventional (binary, supplementary)  starsim_causal v2 intervention at 90%
                coverage (full flip) and the v3 "hold" rung (largest campaign
                that does not flip the answer).

Scores (per item the median over reps first, then the mean over items)
  binary       excess_brier = (p - P*)^2, i.e. Brier minus the perfect
               forecaster's P*(1-P*) (0 here). recovered = 1 - sum (p-P*)^2 /
               sum (1/2-P*)^2: share of the recoverable Brier score.
  continuous   crps = quantile-pinball CRPS (fbsim_core.metrics.compute_crps)
               averaged over the truth samples; crps_oracle = the truth's own
               quantiles scored the same way (irreducible noise floor);
               excess_crps = crps - crps_oracle; skill = 1 - excess_crps /
               (crps_clim - crps_oracle) with the fixed climatology of
               results/causal/data/worlds/climatology.json; crps_norm = crps /
               median over models of crps for that template x horizon (the
               FreeCiv paper's normalisation).

Usage (repo root):
  uv run python results/table/build_table.py
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CAUSAL = ROOT / "results" / "causal"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(CAUSAL / "starsim_causal"))
from models import load_roster  # noqa: E402
from fbsim_core.metrics import compute_crps  # noqa: E402

QKEYS = ("p10", "p25", "p50", "p75", "p90")
HORIZONS = (40, 60)
CLIM = json.load(open(CAUSAL / "data" / "worlds" / "climatology.json"))

SOURCES = {
    # name: (question_type, condition, rung, results file, worlds file, truth key, template)
    "binary_uncond": ("binary", "unconditional", "-", CAUSAL / "starsim_causal/results/baseline.jsonl",
                      CAUSAL / "starsim_causal/worlds.json", "truth_base", "cases_comparative"),
    "binary_int_c90": ("binary", "interventional", "c90", CAUSAL / "starsim_causal/results/intervention.jsonl",
                       CAUSAL / "starsim_causal/worlds.json", "truth_int", "cases_comparative"),
    "binary_int_hold": ("binary", "interventional", "hold", CAUSAL / "starsim_causal/results/intervention_hold.jsonl",
                        CAUSAL / "starsim_causal/worlds_hold.json", "truth_int", "cases_comparative"),
    "cont_uncond": ("continuous", "unconditional", "-", CAUSAL / "data/results/baseline.jsonl",
                    CAUSAL / "data/worlds/worlds_c90.json", "truth_base", "new_infections"),
    "cont_int_c25": ("continuous", "interventional", "c25", CAUSAL / "data/results/intervention_c25.jsonl",
                     CAUSAL / "data/worlds/worlds_c25.json", "truth_int", "new_infections"),
    "cont_int_c50": ("continuous", "interventional", "c50", CAUSAL / "data/results/intervention_c50.jsonl",
                     CAUSAL / "data/worlds/worlds_c50.json", "truth_int", "new_infections"),
    "cont_int_c90": ("continuous", "interventional", "c90", CAUSAL / "data/results/intervention_c90.jsonl",
                     CAUSAL / "data/worlds/worlds_c90.json", "truth_int", "new_infections"),
}

# A rerun written by the same runners into <runs>/causal and <runs>/single
# (e.g. results/causal/rerun_low, reasoning.effort=low, 2026-09-16): same worlds
# and truths, different results files. --runs <dir> swaps the files; the table
# goes to <dir>/table/ so the locked 2026-09-08 table is never overwritten.
RERUN_FILES = {
    "binary_uncond": "causal/baseline.jsonl",
    "binary_int_c90": "causal/intervention.jsonl",
    "binary_int_hold": "causal/intervention_hold.jsonl",
    "cont_uncond": "single/baseline.jsonl",
    "cont_int_c25": "single/intervention_c25.jsonl",
    "cont_int_c50": "single/intervention_c50.jsonl",
    "cont_int_c90": "single/intervention_c90.jsonl",
}


def use_runs(runs: Path) -> None:
    global OUT
    for name, rel in RERUN_FILES.items():
        qtype, cond, rung, _, wfile, tkey, tmpl = SOURCES[name]
        SOURCES[name] = (qtype, cond, rung, runs / rel, wfile, tkey, tmpl)
    OUT = runs / "table"
    OUT.mkdir(parents=True, exist_ok=True)


def load_rows(path: Path) -> dict[tuple[str, str], list[dict]]:
    reps: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for line in open(path):
        if line.strip():
            r = json.loads(line)
            reps[(r["model"], r["item_id"])].append(r)
    return reps


def item_scores_binary(reps: list[dict], p_star: float) -> dict:
    p = statistics.median(r["p"] for r in reps)
    return {"forecast": p, "excess_brier": (p - p_star) ** 2, "uninformed": (0.5 - p_star) ** 2}


_crps_cache: dict = {}


def crps_vs_samples(q: dict, key, samples) -> float:
    k = (key, tuple(q[x] for x in QKEYS))
    if k not in _crps_cache:
        _crps_cache[k] = float(np.mean([compute_crps(q, y) for y in samples]))
    return _crps_cache[k]


def item_scores_cont(reps: list[dict], item: dict, truth_key: str, source: str) -> dict:
    tr = item[truth_key]
    ys = tr["samples"]
    q = {k: statistics.median(r[k] for r in reps) for k in QKEYS}
    ikey = (source, item["item_id"], truth_key)   # the rung changes truth_int; key the cache on the source too
    crps = crps_vs_samples(q, ikey, ys)
    oracle = crps_vs_samples({k: tr[k] for k in QKEYS}, ikey, ys)
    clim = crps_vs_samples({k: CLIM[str(item["horizon"])][k] for k in QKEYS}, ikey, ys)
    return {"forecast_p50": q["p50"], "truth_p50": tr["p50"], "crps": crps, "crps_oracle": oracle,
            "crps_clim": clim, "excess_crps": crps - oracle,
            "skill": 1 - (crps - oracle) / (clim - oracle)}


def cell_meta(rows: list[dict]) -> dict:
    return {"n_calls": len(rows), "cost_usd": sum(r["cost_usd"] or 0.0 for r in rows),
            "reasoning_tokens_mean": float(np.mean([r["reasoning_tokens"] or 0 for r in rows])),
            "completion_tokens_mean": float(np.mean([r["completion_tokens"] or 0 for r in rows]))}


def score_source(name: str, roster) -> list[dict]:
    """Long rows: one per model x horizon (40, 60, pooled)."""
    qtype, cond, rung, rfile, wfile, truth_key, template = SOURCES[name]
    items = {i["item_id"]: i for i in json.load(open(wfile))["items"]}
    reps = load_rows(rfile)
    per_item: dict[str, dict[str, dict]] = defaultdict(dict)   # model -> item -> scores
    per_item_rows: dict[str, dict[str, list]] = defaultdict(dict)
    for (mid, iid), rs in reps.items():
        if iid not in items:
            continue
        it = items[iid]
        if qtype == "binary":
            s = item_scores_binary(rs, it[truth_key])
        else:
            s = item_scores_cont(rs, it, truth_key, name)
        per_item[mid][iid] = s
        per_item_rows[mid][iid] = rs

    # FreeCiv-style normalisation: model mean CRPS / median across models, per template x horizon
    norm_ref: dict[int, float] = {}
    if qtype == "continuous":
        for h in HORIZONS:
            means = [np.mean([s["crps"] for iid, s in per_item[m.openrouter_id].items() if items[iid]["horizon"] == h])
                     for m in roster if any(items[iid]["horizon"] == h for iid in per_item[m.openrouter_id])]
            norm_ref[h] = float(np.median(means)) if means else float("nan")

    out = []
    for m in roster:
        mid = m.openrouter_id
        for h in (*HORIZONS, "pooled"):
            iids = [iid for iid in per_item[mid] if h == "pooled" or items[iid]["horizon"] == h]
            n_total = sum(1 for iid in items if h == "pooled" or items[iid]["horizon"] == h)
            row = {"model": mid, "name": m.name, "eci": m.eci, "fb_overall": m.fb_overall,
                   "question_type": qtype, "condition": cond, "rung": rung, "template": template,
                   "horizon": h, "n_items": len(iids), "n_items_total": n_total,
                   "complete": len(iids) == n_total}
            rows = [r for iid in iids for r in per_item_rows[mid][iid]]
            row.update(cell_meta(rows) if rows else {"n_calls": 0, "cost_usd": 0.0,
                                                     "reasoning_tokens_mean": float("nan"),
                                                     "completion_tokens_mean": float("nan")})
            if not iids:
                out.append(row); continue
            ss = [per_item[mid][iid] for iid in iids]
            if qtype == "binary":
                row["excess_brier"] = float(np.mean([s["excess_brier"] for s in ss]))
                row["recovered"] = 1 - sum(s["excess_brier"] for s in ss) / sum(s["uninformed"] for s in ss)
                row["direction_hits"] = sum((s["forecast"] > 0.5) == (items[iid][truth_key] > 0.5)
                                            for iid, s in zip(iids, ss))
            else:
                for k in ("crps", "crps_oracle", "crps_clim", "excess_crps", "skill"):
                    row[k] = float(np.mean([s[k] for s in ss]))
                row["median_rel_err_p50"] = float(np.median(
                    [abs(s["forecast_p50"] - s["truth_p50"]) / max(s["truth_p50"], 1) for s in ss]))
                if h == "pooled":
                    row["crps_norm"] = float(np.mean(
                        [np.mean([per_item[mid][iid]["crps"] for iid in iids if items[iid]["horizon"] == hh]) / norm_ref[hh]
                         for hh in HORIZONS if any(items[iid]["horizon"] == hh for iid in iids)]))
                else:
                    row["crps_norm"] = row["crps"] / norm_ref[h]
            out.append(row)
    return out


def pooled_rungs(long: list[dict], roster) -> list[dict]:
    """Interventional (continuous) pooled over the three coverage rungs: mean of the
    per-rung scores (the locked headline); cost and calls summed."""
    by = defaultdict(list)
    for r in long:
        if r["question_type"] == "continuous" and r["condition"] == "interventional":
            by[(r["model"], r["horizon"])].append(r)
    out = []
    for m in roster:
        for h in (*HORIZONS, "pooled"):
            rs = [r for r in by[(m.openrouter_id, h)] if r["n_items"]]
            row = {"model": m.openrouter_id, "name": m.name, "eci": m.eci, "fb_overall": m.fb_overall,
                   "question_type": "continuous", "condition": "interventional", "rung": "pooled(c25,c50,c90)",
                   "template": "new_infections", "horizon": h,
                   "n_items": sum(r["n_items"] for r in rs), "n_items_total": sum(r["n_items_total"] for r in by[(m.openrouter_id, h)]),
                   "complete": all(r["complete"] for r in by[(m.openrouter_id, h)]) and len(rs) == 3,
                   "n_calls": sum(r["n_calls"] for r in rs), "cost_usd": sum(r["cost_usd"] for r in rs),
                   "reasoning_tokens_mean": float(np.mean([r["reasoning_tokens_mean"] for r in rs])) if rs else float("nan"),
                   "completion_tokens_mean": float(np.mean([r["completion_tokens_mean"] for r in rs])) if rs else float("nan")}
            if rs:
                for k in ("crps", "crps_oracle", "crps_clim", "excess_crps", "skill", "crps_norm", "median_rel_err_p50"):
                    row[k] = float(np.mean([r[k] for r in rs]))
            out.append(row)
    return out


def rho(rows: list[dict], metric: str, against: str = "eci") -> tuple[float | None, float | None, int]:
    pts = [(r[against], r[metric]) for r in rows if r.get("complete") and r.get(metric) is not None
           and r.get(against) is not None and not np.isnan(r[metric])]
    if len(pts) < 4:
        return None, None, len(pts)
    x, y = zip(*pts)
    s = spearmanr(x, y)
    return float(s.statistic), float(s.pvalue), len(pts)


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    return f"{x:.{nd}f}"


def main():
    import argparse
    ap = argparse.ArgumentParser(description="StarSim results table")
    ap.add_argument("--runs", default=None, help="score a rerun directory (see RERUN_FILES) instead of the locked runs")
    a = ap.parse_args()
    if a.runs:
        use_runs(Path(a.runs).resolve())
    roster = load_roster()
    long: list[dict] = []
    for name in SOURCES:
        long += score_source(name, roster)
    long += pooled_rungs(long, roster)

    cols = ["model", "name", "eci", "fb_overall", "question_type", "condition", "rung", "template", "horizon",
            "n_items", "n_items_total", "complete", "n_calls", "cost_usd", "reasoning_tokens_mean",
            "completion_tokens_mean", "excess_brier", "recovered", "direction_hits",
            "crps", "crps_oracle", "crps_clim", "excess_crps", "skill", "crps_norm", "median_rel_err_p50"]
    with open(OUT / "starsim_results_long.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in long:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()})

    # ---- wide table: one row per model, the pooled cells of each column group
    def pick(qtype, cond, rung, horizon="pooled"):
        return {r["model"]: r for r in long if r["question_type"] == qtype and r["condition"] == cond
                and r["rung"] == rung and r["horizon"] == horizon}

    groups = [  # (label, qtype, cond, rung, metric, lower_is_better)
        ("binary", "binary", "unconditional", "-"),
        ("continuous", "continuous", "unconditional", "-"),
        ("interventional_pooled", "continuous", "interventional", "pooled(c25,c50,c90)"),
        ("interventional_c25", "continuous", "interventional", "c25"),
        ("interventional_c50", "continuous", "interventional", "c50"),
        ("interventional_c90", "continuous", "interventional", "c90"),
        ("binary_interventional_c90", "binary", "interventional", "c90"),
        ("binary_interventional_hold", "binary", "interventional", "hold"),
    ]
    tables = {g[0]: {h: pick(g[1], g[2], g[3], h) for h in (40, 60, "pooled")} for g in groups}

    wide_rows = []
    for m in roster:
        mid = m.openrouter_id
        row = {"model": mid, "eci": m.eci, "fb_overall": m.fb_overall}
        total_cost = 0.0; total_calls = 0
        for label, qtype, *_ in groups:
            for h in (40, 60, "pooled"):
                r = tables[label][h].get(mid)
                tag = f"{label}_d{h}" if h != "pooled" else label
                if r is None or not r["n_items"]:
                    row[f"{tag}_score"] = None; continue
                if qtype == "binary":
                    row[f"{tag}_excess_brier"] = r["excess_brier"]
                    row[f"{tag}_recovered"] = r["recovered"]
                else:
                    row[f"{tag}_crps"] = r["crps"]
                    row[f"{tag}_excess_crps"] = r["excess_crps"]
                    row[f"{tag}_skill"] = r["skill"]
                    row[f"{tag}_crps_norm"] = r["crps_norm"]
                if h == "pooled":
                    row[f"{label}_n_items"] = f"{r['n_items']}/{r['n_items_total']}"
                    row[f"{label}_calls"] = r["n_calls"]
                    row[f"{label}_cost_usd"] = r["cost_usd"]
                    total_cost += r["cost_usd"]; total_calls += r["n_calls"]
        row["total_calls"] = total_calls
        row["total_cost_usd"] = total_cost
        wide_rows.append(row)
    wide_cols = []
    for r in wide_rows:
        for k in r:
            if k not in wide_cols:
                wide_cols.append(k)
    with open(OUT / "starsim_results_wide.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=wide_cols)
        w.writeheader()
        for r in wide_rows:
            w.writerow({k: (f"{v:.4g}" if isinstance(v, float) else v) for k, v in r.items()})

    # ---- markdown summary (pooled + per-horizon for the three headline columns)
    md = []
    md.append("# StarSim results table — FBSim paper (built %s)\n" % __import__("datetime").date.today().isoformat())
    md.append("Per model, median over reps per item, mean over items. Binary: excess Brier vs the perfect "
              "forecaster (lower is better) and `recov` = share of the recoverable Brier score (1 = perfect, 0 = always 0.5). "
              "Continuous: CRPS skill vs the fixed climatology after subtracting the simulator's noise floor "
              "(1 = matches the simulator's distribution, 0 = climatology, <0 worse). Interventional = the continuous "
              "question with a vaccination campaign, pooled over 25/50/90% coverage. Cost = OpenRouter USD for the calls in that column.\n")
    hdr = ("| ECI | model | binary d40 | binary d60 | **binary** (recov) | cont d40 | cont d60 | **continuous** (skill) | "
           "int d40 | int d60 | **interventional** (skill) | calls | cost $ |")
    md.append(hdr)
    md.append("|" + "---|" * (hdr.count("|") - 1))
    for m in sorted(roster, key=lambda m: -m.eci):
        mid = m.openrouter_id
        b = tables["binary"]; c = tables["continuous"]; i = tables["interventional_pooled"]
        def g(tbl, h, k):
            r = tbl[h].get(mid); return fmt(r.get(k)) if r and r["n_items"] else "–"
        flag = "" if all(tbl["pooled"].get(mid, {}).get("complete") for tbl in (b, c, i)) else " ⚠"
        calls = sum(tbl["pooled"][mid]["n_calls"] for tbl in (b, c, i))
        cost = sum(tbl["pooled"][mid]["cost_usd"] for tbl in (b, c, i))
        md.append(f"| {m.eci:.1f} | {mid}{flag} | {g(b,40,'recovered')} | {g(b,60,'recovered')} | **{g(b,'pooled','recovered')}** | "
                  f"{g(c,40,'skill')} | {g(c,60,'skill')} | **{g(c,'pooled','skill')}** | "
                  f"{g(i,40,'skill')} | {g(i,60,'skill')} | **{g(i,'pooled','skill')}** | {calls} | {cost:.2f} |")
    md.append("\n⚠ = at least one item or rep missing in one of the three columns (see `starsim_results_long.csv`, column `n_items`/`n_calls`).\n")

    md.append("## Capability gradient (Spearman ρ vs ECI, complete models only)\n")
    md.append("| column | metric | ρ | p | n |")
    md.append("|---|---|---|---|---|")
    for label, qtype, *_ in groups:
        for h in (40, 60, "pooled"):
            rows = list(tables[label][h].values())
            metric = "recovered" if qtype == "binary" else "skill"
            r_, p_, n_ = rho(rows, metric)
            md.append(f"| {label} d{h} | {metric} | {fmt(r_, 2) if r_ is not None else '–'} | {fmt(p_, 3) if p_ is not None else '–'} | {n_} |")

    md.append("\n## Interventional by coverage rung (skill, pooled horizons)\n")
    md.append("| ECI | model | c25 | c50 | c90 | pooled | binary c90 (recov) | binary hold (recov) |")
    md.append("|---|---|---|---|---|---|---|---|")
    for m in sorted(roster, key=lambda m: -m.eci):
        mid = m.openrouter_id
        def g2(label, k):
            r = tables[label]["pooled"].get(mid); return fmt(r.get(k)) if r and r["n_items"] else "–"
        md.append(f"| {m.eci:.1f} | {mid} | {g2('interventional_c25','skill')} | {g2('interventional_c50','skill')} | "
                  f"{g2('interventional_c90','skill')} | {g2('interventional_pooled','skill')} | "
                  f"{g2('binary_interventional_c90','recovered')} | {g2('binary_interventional_hold','recovered')} |")

    md.append("\n## Cost by column (USD, all models)\n")
    md.append("| column | calls | cost $ |")
    md.append("|---|---|---|")
    grand = 0.0
    for label, *_ in groups:
        rs = tables[label]["pooled"].values()
        c_ = sum(r["cost_usd"] for r in rs); n_ = sum(r["n_calls"] for r in rs)
        if label != "interventional_pooled":
            grand += c_
        md.append(f"| {label} | {n_} | {c_:.2f} |")
    md.append(f"| **total (distinct calls)** | | **{grand:.2f}** |")
    (OUT / "starsim_results_table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\n[saved] starsim_results_long.csv, starsim_results_wide.csv, starsim_results_table.md -> {OUT}")


if __name__ == "__main__":
    main()
