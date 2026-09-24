"""Per-item table for the StarSim appendix: one row per item of the five sets, with the
world's parameters, coverage, horizon, the ground truth, the floor and reference CRPS
(continuous) and the spread of model skill over the complete models.

  uv run python results/table/per_item_table.py --runs results/causal/rerun_lowest [--out <tex>]
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_table as bt  # noqa: E402

ORDER = [("binary_uncond", "Binary, unconditional"), ("cont_uncond", "Continuous, unconditional"),
         ("cont_int_c25", "Continuous, 25\\% coverage"), ("cont_int_c50", "Continuous, 50\\% coverage"),
         ("cont_int_c90", "Continuous, 90\\% coverage"), ("binary_int_c90", "Binary, 90\\% coverage"),
         ("binary_int_hold", "Binary, hold")]
R0 = {0.03: 1.8, 0.04: 2.4, 0.05: 3.0, 0.065: 3.9}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--runs", default=None); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.runs: bt.use_runs(Path(a.runs).resolve())
    roster = bt.load_roster(); rows = []; rec = []
    for name, label in ORDER:
        qtype, cond, rung, rfile, wfile, tkey, tmpl = bt.SOURCES[name]
        items = json.load(open(wfile))["items"]; reps = bt.load_rows(rfile)
        # complete models: every item answered at least once in this set
        complete = [m.openrouter_id for m in roster if all((m.openrouter_id, it["item_id"]) in reps for it in items)]
        for it in items:
            if qtype == "binary":
                truth = it[tkey]; floor = ref = None
                sk = [bt.item_scores_binary(reps[(m, it["item_id"])], truth)["excess_brier"] for m in complete]
                sk = [1 - x / 0.25 for x in sk]   # recovered share per item, perfect-forecaster reference
                if it["world_id"] in ("w0", "w1", "w2", "w3") and "beta_r" in json.load(open(wfile))["worlds"][0]:
                    W = {w["world_id"]: w for w in json.load(open(wfile))["worlds"]}[it["world_id"]]
                    world = f"{W['beta_r']:.3f} / {W['beta_s']:.3f}"; cov = W.get("coverage", 0.9 if rung == "c90" else None)
                else:
                    world = "?"; cov = None
                tr_txt = f"{truth:.2f}"
            else:
                s0 = bt.item_scores_cont(reps[(complete[0], it["item_id"])], it, tkey, name)
                floor, ref = s0["crps_oracle"], s0["crps_clim"]
                sk = [bt.item_scores_cont(reps[(m, it["item_id"])], it, tkey, name)["skill"] for m in complete]
                world = f"{it['beta']:.3f} ({R0[it['beta']]:.1f})"
                cov = {"c25": 0.25, "c50": 0.5, "c90": 0.9}.get(rung)
                tr_txt = f"{it[tkey]['p50']:.0f}"
            sk = np.array(sk)
            rows.append((label, it["item_id"], world, "--" if cov is None else f"{int(cov*100)}", it["horizon"], tr_txt,
                         "--" if floor is None else f"{floor:.0f}", "--" if ref is None else f"{ref:.0f}",
                         f"{np.median(sk):.2f}", f"{sk.min():.2f}", f"{sk.max():.2f}", len(complete)))
            rec.append(dict(set=name, item=it["item_id"], world=world, coverage=cov, horizon=it["horizon"], truth=tr_txt,
                            floor=floor, reference=ref, skill_median=float(np.median(sk)), skill_min=float(sk.min()), skill_max=float(sk.max()), n=len(complete)))
    out = Path(a.out) if a.out else (Path(a.runs) / "table" / "per_item_table.tex" if a.runs else Path(__file__).resolve().parent / "per_item_table.tex")
    lines = ["\\begin{tabular}{@{}l l l r r r r r r r r@{}}", "\\toprule",
             "Set & Item & $\\beta$ ($R_0$) or $\\beta_R$ / $\\beta_S$ & Cov.\\ \\% & Day & Truth & Floor & Ref.\\ & Skill med.\\ & Min & Max \\\\", "\\midrule"]
    last = None
    for r in rows:
        if r[0] != last:
            if last is not None: lines.append("\\addlinespace")
            last = r[0]
        cells = [r[0] if r == [x for x in rows if x[0] == r[0]][0] else ""] + [str(x) for x in r[1:11]]
        cells[1] = "\\texttt{" + cells[1].replace("_", "\\_") + "}"
        lines.append(" & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    out.write_text("\n".join(lines) + "\n")
    json.dump(rec, open(out.with_suffix(".json"), "w"), indent=1)
    ns = sorted({r[11] for r in rows})
    print(f"[saved] {out} ({len(rows)} rows; complete models per set: {ns})")
    # a few numbers for the caption
    for name, label in ORDER:
        rs = [x for x in rec if x["set"] == name]
        print(f"  {label:28s} skill median over items: {np.median([x['skill_median'] for x in rs]):.2f}; hardest item {min(rs, key=lambda x: x['skill_median'])['item']} ({min(x['skill_median'] for x in rs):.2f})")


if __name__ == "__main__":
    main()
