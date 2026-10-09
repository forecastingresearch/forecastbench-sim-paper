#!/bin/sh
# 2026-09-16 13:45: the protocol run (--reasoning lowest = Fabio's lowest_effort per model, budget 1024 for
# the four budget-only models). Seeded with rerun_low rows of the 15 models whose setting is unchanged; the
# nine corrected models and the Kimi/DeepSeek tails are elicited here. Each runner is resumable.
cd /Users/elsehow/Projects/iclr-2026
rm -f results/causal/rerun_lowest/ALL_DONE
uv run python results/causal/starsim_causal/run.py --reasoning lowest --concurrency 10 --out-dir results/causal/rerun_lowest/causal >> results/causal/rerun_lowest/causal/full_run.log 2>&1 &
uv run python results/causal/starsim_causal/run.py --reasoning lowest --concurrency 10 --out-dir results/causal/rerun_lowest/causal --tag hold --worlds results/causal/starsim_causal/worlds_hold.json >> results/causal/rerun_lowest/causal/hold_run.log 2>&1 &
uv run python results/causal/starsim_single/run.py --reasoning lowest --reps 3 --concurrency 10 --class baseline --out-dir results/causal/rerun_lowest/single --worlds results/causal/data/worlds/worlds_c90.json >> results/causal/rerun_lowest/single/baseline_run.log 2>&1 &
uv run python results/causal/starsim_single/run.py --reasoning lowest --reps 3 --concurrency 10 --tag c90 --out-dir results/causal/rerun_lowest/single --worlds results/causal/data/worlds/worlds_c90.json >> results/causal/rerun_lowest/single/c90_run.log 2>&1 &
uv run python results/causal/starsim_single/run.py --reasoning lowest --reps 3 --concurrency 10 --tag c50 --out-dir results/causal/rerun_lowest/single --worlds results/causal/data/worlds/worlds_c50.json >> results/causal/rerun_lowest/single/c50_run.log 2>&1 &
uv run python results/causal/starsim_single/run.py --reasoning lowest --reps 3 --concurrency 10 --tag c25 --out-dir results/causal/rerun_lowest/single --worlds results/causal/data/worlds/worlds_c25.json >> results/causal/rerun_lowest/single/c25_run.log 2>&1 &
wait
echo "ALL DONE $(date)" > results/causal/rerun_lowest/ALL_DONE
