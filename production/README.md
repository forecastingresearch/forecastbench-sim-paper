# Production recipes

How the paper's inputs were produced, from scratch: production configs, seeds, prompts, model panels and producer scripts. The package commands (`python -m fbsim_paper ...`) never run anything here. They start from the cached outputs in the private data archive.

Every file is a byte-for-byte copy of what ran; [PROVENANCE.json](PROVENANCE.json) gives each file's source and SHA-256. Scripts keep their original absolute paths (`/Users/elsehow/Projects/...`), and several check their inputs' hashes by those paths, so adjust paths in a working copy, not here. Nothing here has been rerun since the paper.

## Starsim

1. **Simulator.** `forecastingresearch/forecastbench-sim` at `65204aa59cfb9fa835cf5b2af8917e02e98a4f26` (branch `refactor/monorepo`) plus [pandemic-runner-p_death.patch](starsim/pandemic-runner-p_death.patch). The patch was an uncommitted change in production: it adds the `p_death` argument the paper's no-death worlds pass. Public `main` lacks it. The patched `runner.py` hashes to `b921742a…`, the value the frozen fixed-state plan records.
2. **Worlds and forecasts.** [starsim/iclr-2026](starsim/iclr-2026) is the producer layout from `forecastingresearch/iclr-2026` (private; code unchanged since `3f55a91`, 16 Sep 2026). Put `forecastbench-sim` beside it, as `pyproject.toml` expects.
   - Worlds: `starsim_single/mine_single.py` (continuous, headline) and `starsim_causal/mine_worlds.py` / `mine_dose.py` (binary, appendix). Mined worlds are in `results/causal/data/worlds/` and `starsim_causal/worlds*.json`.
   - Forecasts: `results/causal/rerun_lowest/run_all.sh` is the paper's run (per-model lowest reasoning effort, three repetitions). It needs `OPENROUTER_API_KEY`. The model roster is `results/causal/data/models.csv`.
3. **Repaired continuous truth.** [starsim/fixed_state](starsim/fixed_state) is the fixed-state audit, in order: `smoke/` → `corrected_smoke/` → `production_v1/production.py` (driven by the frozen `PLAN.json`: 4,000 seeds, 16,000 branches) → `production_v1/rescore.py`. Its `rescore/` outputs are what `python -m fbsim_paper reproduce` reads (`datasets/starsim-audit/production_v1/rescore` in the data archive). `verify_uptake.py` and `verify_numeric.py` are independent checks; they produce no paper numbers.
4. **Tables and figures.** The cached route in `src/fbsim_paper`.

## Micropolis

The producer is Fabio Rocha's `fdrocha/forecastbench-sim` at `8c70972b698f079d54b8a2255c81fbefc55e7d99` (branch `micropolis`), with the engine from `fdrocha/MicropolisCore`; the exact engine commit used was not recorded. [micropolis](micropolis) holds that commit's production settings: run configs (the paper's are `configs/continuous.json5` and `configs/binary.json5`), model panels, prompt variants, batching ablations, prompt preambles and epilogues, model lists, knowledge-eval statements and `model_specs.json5`. The scripts that use them are in that commit's `worlds/micropolis/scripts`. Benchmark `main`'s `worlds/micropolis` is a port of that code and has not been tried with these configs. Paper CSVs are gathered by `src/fbsim_paper/assets/micropolis/scripts/gather_paper_data.py`.

## FreeCiv

The producer and its production settings are on the `freeciv-v3` branch of `forecastingresearch/forecastbench-sim` (paper reporting was extracted at `4e35dd20`; branch head `7fa46072`). They move into `production/freeciv/` as part of the `freeciv-v3` merge.

## Not here

Raw provider responses, simulator outputs and caches, datasets, human-subject records and credentials. These stay in the private data archive and out of Git.
