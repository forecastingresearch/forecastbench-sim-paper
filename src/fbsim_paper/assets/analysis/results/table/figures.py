"""The three StarSim figures of the FBSim paper, from a table build's long CSV.

  fig_starsim_interventional.pdf   main panel: interventional skill pooled over rungs vs ECI;
                                   side panels: one per coverage rung
  fig_starsim_unconditional.pdf    binary recovered share and continuous skill vs ECI
  fig_starsim_horizon.pdf          interventional skill at day 40 vs day 60 by rung

Style follows the 2026-09-08 figures (dark green points, serif, dashed zero line labelled
"climatology"). Spearman rho with a 95 percent percentile bootstrap over models, 10,000
draws, complete models only. Prints the numbers the captions quote.

  uv run python results/table/figures.py --runs results/causal/rerun_lowest [--out <dir>]
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

GREEN = "#102b23"
GREY = "#9a9a9a"
plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
                     "mathtext.fontset": "stix", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "pdf.fonttype": 42})

SHORT = {"meta-llama/llama-4-scout": "Llama 4 Scout", "deepseek/deepseek-chat": "DeepSeek V3", "openai/gpt-4.1": "GPT-4.1",
         "qwen/qwen3-235b-a22b": "Qwen3 235B", "google/gemini-2.5-flash": "Gemini 2.5 Flash", "moonshotai/kimi-k2": "Kimi K2",
         "openai/gpt-5-nano": "GPT-5 Nano", "anthropic/claude-haiku-4.5": "Haiku 4.5", "qwen/qwen3.5-flash-02-23": "Qwen3.5 Flash",
         "google/gemini-3.1-flash-lite-preview": "Gemini 3.1 Flash Lite", "openai/gpt-5-mini": "GPT-5 Mini", "openai/o4-mini": "o4-mini",
         "openai/gpt-5.4-nano": "GPT-5.4 Nano", "openai/o3": "o3", "openai/gpt-5": "GPT-5", "google/gemini-3-flash-preview": "Gemini 3 Flash",
         "deepseek/deepseek-v4-flash-0731": "DeepSeek V4 Flash", "anthropic/claude-sonnet-5": "Sonnet 5", "openai/gpt-5.6-luna": "GPT-5.6 Luna",
         "google/gemini-3.7-flash": "Gemini 3.7 Flash", "openai/gpt-5.5": "GPT-5.5", "openai/gpt-5.6-sol": "GPT-5.6 Sol",
         "anthropic/claude-opus-5": "Opus 5", "anthropic/claude-fable-5": "Fable"}


def load(long_csv: Path):
    cells = defaultdict(dict)
    for r in csv.DictReader(open(long_csv)):
        cells[(r["question_type"], r["condition"], r["rung"], r["horizon"])][r["model"]] = r
    return cells


def series(rows, metric):
    """(model, eci, value, complete) for every model with a value."""
    out = []
    for m, r in rows.items():
        try:
            v = float(r[metric])
        except (TypeError, ValueError):
            continue
        out.append((m, float(r["eci"]), v, r["complete"] == "True"))
    return sorted(out, key=lambda t: t[1])


def rho_ci(pts, draws=10000, seed=0):
    full = [p for p in pts if p[3]]
    e = np.array([p[1] for p in full]); v = np.array([p[2] for p in full])
    rho = spearmanr(e, v).correlation
    rng = np.random.default_rng(seed); bs = []
    for _ in range(draws):
        i = rng.integers(0, len(full), len(full)); bs.append(spearmanr(e[i], v[i]).correlation)
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    return rho, lo, hi, len(full)


def pick_labels(pts, n_top=5, n_resid=6, n_low=0):
    """Label the top models by ECI, the largest residuals from a linear fit, and the lowest values."""
    full = [p for p in pts if p[3]]
    e = np.array([p[1] for p in full]); v = np.array([p[2] for p in full])
    a, b = np.polyfit(e, v, 1); resid = np.abs(v - (a * e + b))
    chosen = {p[0] for p in sorted(full, key=lambda p: -p[1])[:n_top]}
    chosen |= {full[i][0] for i in np.argsort(-resid)[:n_resid]}
    chosen |= {p[0] for p in sorted(full, key=lambda p: p[2])[:n_low]}
    chosen |= {p[0] for p in pts if not p[3]}
    return chosen


def scatter(ax, pts, labels=True, fontsize=6, n_top=5, n_resid=6, n_low=0):
    for m, e, v, complete in pts:
        ax.scatter(e, v, s=14 if labels else 8, facecolor=GREEN if complete else "white", edgecolor=GREEN, linewidth=0.7, zorder=3)
    if not labels:
        return
    chosen = pick_labels(pts, n_top, n_resid, n_low)
    # Greedy placement in axes coordinates: try four offsets, keep the one farthest from
    # every label and point already on the axes. Points and labels are compared in a
    # normalised frame so the two axes weigh equally.
    ax.margins(x=0.10, y=0.12)   # room for labels at the edges
    ax.figure.canvas.draw()
    to_ax = lambda e, v: ax.transAxes.inverted().transform(ax.transData.transform((e, v)))
    occupied = [to_ax(e, v) for _, e, v, _ in pts]
    placed = []
    slots = [((4, 3), "left", "bottom"), ((-4, 3), "right", "bottom"), ((4, -3), "left", "top"), ((-4, -3), "right", "top"),
             ((0, 6), "center", "bottom"), ((0, -6), "center", "top")]
    for m, e, v, complete in sorted(pts, key=lambda p: -p[2]):
        if m not in chosen:
            continue
        name = SHORT.get(m, m)
        best = None
        x, y = to_ax(e, v)
        # near an edge, only the inward slots are allowed
        allowed = [sl for sl in slots if not (x < 0.15 and sl[1] == "right") and not (x > 0.90 and sl[1] == "left")
                   and not (y < 0.10 and sl[2] == "top") and not (y > 0.90 and sl[2] == "bottom")] or slots
        for (dx, dy), ha, va in allowed:
            # label centre estimate: ~0.011 axes units per character horizontally
            w = 0.011 * len(name) * 6 / fontsize * 0.9
            cx = x + {"left": 0.012 + w / 2, "right": -0.012 - w / 2, "center": 0.0}[ha]
            cy = y + (0.03 if va == "bottom" else -0.03) * (1.6 if ha == "center" else 1.0)
            d_lab = min([np.hypot((cx - a) / max(w, 0.05), (cy - b) / 0.05) for a, b, w2 in placed] + [9])
            d_pt = min([np.hypot((cx - a) / max(w, 0.05), (cy - b) / 0.05) for a, b in occupied if (a, b) != (x, y)] + [9])
            score = min(d_lab, 0.6 * d_pt)
            if best is None or score > best[0]:
                best = (score, (dx, dy), ha, va, cx, cy, w)
        _, (dx, dy), ha, va, cx, cy, w = best
        ax.annotate(name, (e, v), xytext=(dx, dy), textcoords="offset points", fontsize=fontsize, ha=ha, va=va)
        placed.append((cx, cy, w))


def fig_interventional(cells, out):
    pooled = series(cells[("continuous", "interventional", "pooled(c25,c50,c90)", "pooled")], "skill")
    fig = plt.figure(figsize=(7.2, 3.1))
    gs = fig.add_gridspec(3, 2, width_ratios=[2.6, 1.0], hspace=0.55, wspace=0.28)
    ax = fig.add_subplot(gs[:, 0])
    scatter(ax, pooled)
    rho, lo, hi, n = rho_ci(pooled)
    ax.axhline(0, ls="--", lw=0.6, color=GREY)
    ax.set_xlabel("Epoch Capabilities Index"); ax.set_ylabel("Interventional CRPS skill (higher is better)")
    ax.set_title("All rungs pooled", fontsize=8, loc="left")
    inc = [p for p in pooled if not p[3]]
    note = f"Spearman $\\rho$ = {rho:.2f}  [{lo:.2f}, {hi:.2f}],  $n$ = {n}"
    if inc:
        note += "\nopen marker: incomplete, not in $\\rho$"
    ax.text(0.98, 0.03, note, transform=ax.transAxes, ha="right", va="bottom", fontsize=7)
    stats = {"pooled": (rho, lo, hi, n)}
    for i, rung in enumerate(("c25", "c50", "c90")):
        axs = fig.add_subplot(gs[i, 1])
        pts = series(cells[("continuous", "interventional", rung, "pooled")], "skill")
        scatter(axs, pts, labels=False)
        r2, l2, h2, n2 = rho_ci(pts); stats[rung] = (r2, l2, h2, n2)
        axs.axhline(0, ls="--", lw=0.6, color=GREY)
        axs.set_title(f"{rung[1:]}% coverage:  $\\rho$ = {r2:.2f} [{l2:.2f}, {h2:.2f}], $n$ = {n2}", fontsize=6, pad=2)
        if i == 2:
            axs.set_xlabel("Epoch Capabilities Index", fontsize=7)
        else:
            axs.set_xticklabels([])
    fig.savefig(out / "fig_starsim_interventional.pdf", bbox_inches="tight")
    plt.close(fig)
    return stats


def fig_unconditional(cells, out):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.9))
    fig.subplots_adjust(wspace=0.32)
    b = series(cells[("binary", "unconditional", "-", "pooled")], "recovered")
    scatter(a1, b, n_top=2, n_resid=0, n_low=5); rho, lo, hi, n = rho_ci(b)
    a1.set_title("Binary, unconditional", fontsize=8)
    a1.set_xlabel("Epoch Capabilities Index"); a1.set_ylabel("Recovered Brier share (higher is better)")
    vals = [p[2] for p in b if p[3]]
    n997 = sum(v >= 0.997 for v in vals); n1000 = sum(round(v, 3) >= 1.0 for v in vals)
    a1.text(0.98, 0.20, f"{n997} of {len(vals)} models at $\\geq$ 0.997;\n{n1000} print 1.000", transform=a1.transAxes, ha="right", fontsize=6, color=GREY)
    a1.text(0.98, 0.03, f"Spearman $\\rho$ = {rho:.2f}  [{lo:.2f}, {hi:.2f}],  $n$ = {n}", transform=a1.transAxes, ha="right", fontsize=7.5)
    c = series(cells[("continuous", "unconditional", "-", "pooled")], "skill")
    scatter(a2, c, n_top=3, n_resid=3, n_low=4); rho2, lo2, hi2, n2 = rho_ci(c)
    a2.axhline(0, ls="--", lw=0.6, color=GREY); a2.text(0.99, 0.0, "climatology", transform=a2.get_yaxis_transform(), ha="right", va="bottom", fontsize=6, color=GREY)
    a2.set_title("Continuous, unconditional", fontsize=8)
    a2.set_xlabel("Epoch Capabilities Index"); a2.set_ylabel("CRPS skill (higher is better)")
    a2.text(0.98, 0.55, f"Spearman $\\rho$ = {rho2:.2f}  [{lo2:.2f}, {hi2:.2f}],  $n$ = {n2}", transform=a2.transAxes, ha="right", fontsize=7.5)
    fig.savefig(out / "fig_starsim_unconditional.pdf", bbox_inches="tight")
    plt.close(fig)
    cv = sorted(p[2] for p in c if p[3])
    return {"binary": (rho, lo, hi, n, n997, n1000, min(vals)), "continuous": (rho2, lo2, hi2, n2, cv)}


def fig_horizon(cells, out):
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.4), sharey=True)
    fig.subplots_adjust(wspace=0.12)
    stats = {}
    for ax, rung in zip(axes, ("c25", "c50", "c90")):
        d40 = cells[("continuous", "interventional", rung, "40")]; d60 = cells[("continuous", "interventional", rung, "60")]
        ms = [m for m in d40 if d40[m]["complete"] == "True" and d60.get(m, {}).get("complete") == "True"]
        s40 = np.array([float(d40[m]["skill"]) for m in ms]); s60 = np.array([float(d60[m]["skill"]) for m in ms])
        for a, b in zip(s40, s60):
            ax.plot([40, 60], [a, b], color=GREY, lw=0.5, alpha=0.7, zorder=1)
        q40 = np.percentile(s40, [25, 75]); q60 = np.percentile(s60, [25, 75])
        ax.fill_between([40, 60], [q40[0], q60[0]], [q40[1], q60[1]], color="#d9d9d9", alpha=0.6, zorder=0, lw=0)
        ax.plot([40, 60], [s40.mean(), s60.mean()], color=GREEN, lw=2.2, marker="o", ms=4, zorder=3)
        ax.text(39.2, s40.mean(), f"{s40.mean():.2f}", ha="right", va="center", fontsize=6.5)
        ax.text(60.8, s60.mean(), f"{s60.mean():.2f}", ha="left", va="center", fontsize=6.5)
        ax.axhline(0, ls="--", lw=0.6, color=GREY)
        ax.set_xticks([40, 60]); ax.set_xlim(36, 64); ax.set_ylim(-1.0, 1.05); ax.set_xlabel("Forecast horizon (day)")
        ax.set_title(f"{rung[1:]}% coverage", fontsize=8)
        clipped = int(((s40 < -1.0) | (s60 < -1.0)).sum())
        stats[rung] = (s40.mean(), s60.mean(), int((s60 < s40).sum()), len(ms), clipped)
    axes[0].set_ylabel("Interventional CRPS skill\n(higher is better)")
    axes[2].text(0.98, 0.0, "climatology", transform=axes[2].get_yaxis_transform(), ha="right", va="bottom", fontsize=6, color=GREY)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    axes[2].legend(handles=[Line2D([], [], color=GREEN, lw=2.2, marker="o", ms=4, label="mean over models"),
                            Patch(facecolor="#d9d9d9", label="interquartile range"),
                            Line2D([], [], color=GREY, lw=0.6, label="one model")], loc="lower right", fontsize=6, frameon=False)
    fig.savefig(out / "fig_starsim_horizon.pdf", bbox_inches="tight")
    plt.close(fig)
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=None, help="rerun dir (uses <runs>/table/starsim_results_long.csv); default = the locked table")
    ap.add_argument("--out", default=None, help="output dir; default <runs>/figures or results/table/figures")
    a = ap.parse_args()
    here = Path(__file__).resolve().parent
    long_csv = (Path(a.runs) / "table" if a.runs else here) / "starsim_results_long.csv"
    out = Path(a.out) if a.out else (Path(a.runs) / "figures" if a.runs else here / "figures")
    out.mkdir(parents=True, exist_ok=True)
    cells = load(long_csv)
    si = fig_interventional(cells, out); su = fig_unconditional(cells, out); sh = fig_horizon(cells, out)
    print("interventional rho [lo, hi] n:", {k: tuple(round(x, 2) if isinstance(x, float) else x for x in v) for k, v in si.items()})
    b = su["binary"]; c = su["continuous"]
    print(f"binary: rho={b[0]:.2f} [{b[1]:.2f}, {b[2]:.2f}] n={b[3]}; {b[4]} of {b[3]} >= 0.997, {b[5]} print 1.000, min={b[6]:.3f}")
    print(f"continuous: rho={c[0]:.2f} [{c[1]:.2f}, {c[2]:.2f}] n={c[3]}; skills={[round(x, 2) for x in c[4]]}")
    print("horizon (mean d40, mean d60, worse at d60, n, below -1):", {k: (round(v[0], 2), round(v[1], 2), v[2], v[3], v[4]) for k, v in sh.items()})
    print(f"[saved] three PDFs -> {out}")


if __name__ == "__main__":
    main()
