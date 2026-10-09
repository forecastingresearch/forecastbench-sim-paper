# Starsim fixed-state production and retrospective rescore

**Completed: 16,000 branches, 4,000 independent continuation sets, 1,000 per world, four paired arms per set.** All production and rescore validation passed. Original forecasts, prior audit/failure artifacts and manuscript inputs were preserved. No model calls, cloud spending or remote writes were used. This is a retrospective fixed-hidden-state rescore, not a newly elicited benchmark and not the distribution conditional only on the displayed report.


## Main numerical changes

Scores below are normalized excess five-quantile CRPS approximations (lower is better). The paper constants remain **C40=200 and C60=300 people**. Panel membership is complete-item based, exactly as in the paper; planned repetition completeness is audited separately. Every before/after comparison uses the same models and forecasts.


| Panel | Models | Original mean | Fixed-state mean | Change | Largest rank move |
|---|---|---|---|---|---|
| cont_uncond | 24 | 0.976 | 1.088 | 0.112 | 3.0 |
| cont_int_c25 | 23 | 0.979 | 1.077 | 0.098 | 3.0 |
| cont_int_c50 | 23 | 0.647 | 0.688 | 0.041 | 1.0 |
| cont_int_c90 | 23 | 0.330 | 0.339 | 0.009 | 1.0 |
| interventional_pooled | 23 | 0.652 | 0.701 | 0.049 | 1.0 |
| all_continuous | 23 | 0.742 | 0.807 | 0.065 | 1.0 |


Positive correlations below mean that higher ECI/ForecastBench overall accompanies better forecasting: −Spearman(external score, excess loss). For combined theta, higher is better and no sign reversal is applied. The first interval resamples models, holding truth estimates fixed; the second resamples continuation seeds within each world, holding models fixed. **These are distinct sources of uncertainty, not a joint confidence interval.** Some replay correlation intervals collapse because resampling does not change model ranks; this does not imply certainty about a population association.


| Panel | External score | n | Original rho | New rho | 95% model-panel interval | 95% replay interval |
|---|---|---|---|---|---|---|
| cont_uncond | eci | 24 | 0.69 | 0.75 | [0.49, 0.88] | [0.75, 0.76] |
| cont_uncond | fb_overall | 17 | 0.26 | 0.24 | [-0.35, 0.82] | [0.24, 0.24] |
| interventional_pooled | eci | 23 | 0.66 | 0.67 | [0.34, 0.85] | [0.67, 0.68] |
| interventional_pooled | fb_overall | 17 | 0.44 | 0.45 | [-0.14, 0.88] | [0.45, 0.45] |
| combined_six | eci | 24 | 0.82 | 0.81 | [0.55, 0.93] | [0.81, 0.81] |
| combined_six | fb_overall | 17 | 0.22 | 0.29 | [-0.25, 0.73] | [0.29, 0.29] |
| combined_ten | eci | 24 | 0.87 | 0.88 | [0.70, 0.95] | [0.88, 0.88] |
| combined_ten | fb_overall | 17 | 0.42 | 0.38 | [-0.19, 0.78] | [0.38, 0.38] |


[associations.csv](rescore/associations.csv) gives every coverage/horizon, original intervals, changes and their separate uncertainty intervals. [panels.json](rescore/panels.json) lists each actual model panel, including the smaller matched ForecastBench panel. Combined six/ten-cell fits keep other engines and Starsim binary cells unchanged. They are sensitivity results for the existing combined score, not a claim that all benchmark components have been repaired.


## Model scores and ranks

Ranks are within each complete panel, 1=lowest excess. “—” denotes exclusion from the complete interventional panel, not a zero score. Full horizon/coverage tables and replay score/rank intervals are in [model_scores_ranks.csv](rescore/model_scores_ranks.csv); individual model-item scores and ranks are in [item_scores.csv](rescore/item_scores.csv) and [item_ranks.csv](rescore/item_ranks.csv).


| Model | Baseline score | Baseline rank | Vaccine pooled score | Vaccine pooled rank |
|---|---|---|---|---|
| Anthropic: Claude Fable | 0.241 → 0.274 | 5 → 4 | 0.469 → 0.509 | 9 → 8 |
| Claude Opus 5 | 0.242 → 0.255 | 6 → 3 | 0.295 → 0.329 | 4 → 4 |
| OpenAI: GPT-5.6 Sol | 0.227 → 0.308 | 4 → 5 | 0.191 → 0.178 | 2 → 1 |
| OpenAI: GPT-5.5 | 0.387 → 0.393 | 9 → 7 | 0.238 → 0.260 | 3 → 3 |
| Google: Gemini 3.7 Flash | 0.459 → 0.424 | 12 → 9 | 0.725 → 0.768 | 17 → 17 |
| OpenAI: GPT-5.6 Luna | 0.425 → 0.496 | 10 → 11 | 0.189 → 0.213 | 1 → 2 |
| Anthropic: Claude Sonnet 5 | 0.435 → 0.502 | 11 → 12 | 0.356 → 0.417 | 5 → 6 |
| DeepSeek: DeepSeek V4 Flash 0731 | 0.164 → 0.239 | 2 → 2 | — | — |
| Google: Gemini 3 Flash Preview | 0.599 → 0.577 | 15 → 14 | 0.674 → 0.681 | 16 → 15 |
| OpenAI: GPT-5 | 0.639 → 0.814 | 16 → 17 | 0.463 → 0.516 | 8 → 9 |
| OpenAI: o3 | 0.209 → 0.314 | 3 → 6 | 0.357 → 0.404 | 6 → 5 |
| OpenAI: GPT-5.4 Nano | 0.131 → 0.227 | 1 → 1 | 0.759 → 0.810 | 18 → 18 |
| OpenAI: o4 Mini | 0.356 → 0.435 | 7 → 10 | 1.082 → 1.104 | 20 → 20 |
| OpenAI: GPT-5 Mini | 1.333 → 1.498 | 19 → 19 | 0.487 → 0.547 | 11 → 12 |
| Google: Gemini 3.1 Flash Lite Preview | 0.361 → 0.424 | 8 → 8 | 0.453 → 0.488 | 7 → 7 |
| Qwen: Qwen3.5-Flash | 1.304 → 1.340 | 18 → 18 | 0.500 → 0.546 | 12 → 11 |
| Anthropic: Claude Haiku 4.5 | 1.878 → 2.123 | 20 → 20 | 0.604 → 0.680 | 13 → 14 |
| OpenAI: GPT-5 Nano | 3.564 → 3.836 | 23 → 23 | 1.511 → 1.608 | 22 → 22 |
| MoonshotAI: Kimi K2 | 0.671 → 0.793 | 17 → 16 | 0.659 → 0.713 | 15 → 16 |
| Google: Gemini 2.5 Flash | 0.506 → 0.540 | 13 → 13 | 0.479 → 0.535 | 10 → 10 |
| Qwen: Qwen3 235B A22B | 2.605 → 2.901 | 22 → 22 | 1.255 → 1.353 | 21 → 21 |
| OpenAI: GPT-4.1 | 0.540 → 0.652 | 14 → 15 | 0.607 → 0.644 | 14 → 13 |
| DeepSeek: DeepSeek V3 | 2.081 → 2.390 | 21 → 21 | 1.722 → 1.819 | 23 → 23 |
| Meta: Llama 4 Scout | 4.065 → 4.363 | 24 → 24 | 0.930 → 1.013 | 19 → 19 |


[Combined model scores and ranks](rescore/combined_scores_ranks.csv) include replay intervals. No ranking, correlation or desirable result was used to choose N, seeds, sample retention or precision cutoffs.

![Original versus fixed-state scores](rescore/score_comparison.png)


## Truths, floors and precision

All 32 item distributions have exactly 1,000 samples. Outcomes count infections after the end of day 20, using the exact displayed cumulative baseline. Day-40 and day-60 outcomes come from the same branch. The new truths obey 0≤Y40≤Y60≤5000−C20. No truth or forecast clipping was applied. The table shows day 60; the linked CSV contains both horizons, all five quantiles, point changes, floor changes, bootstrap intervals and distribution-free order-statistic intervals in people.


| Condition | World | Median: old → new | Floor: old → new | New median 95% order interval |
|---|---|---|---|---|
| cont_uncond | w0 | 2780 → 2824 | 52.09 → 44.67 | [2818, 2830] |
| cont_uncond | w1 | 3135 → 3128 | 55.91 → 20.67 | [3125, 3131] |
| cont_uncond | w2 | 2304 → 2308 | 100.90 → 12.35 | [2306, 2310] |
| cont_uncond | w3 | 849 → 866 | 114.07 → 6.73 | [865, 868] |
| cont_int_c25 | w0 | 1314 → 1383 | 54.03 → 52.24 | [1374, 1388] |
| cont_int_c25 | w1 | 2060 → 2051 | 42.86 → 30.00 | [2047, 2056] |
| cont_int_c25 | w2 | 1649 → 1656 | 72.78 → 18.92 | [1653, 1659] |
| cont_int_c25 | w3 | 642 → 656 | 87.00 → 9.04 | [654, 657] |
| cont_int_c50 | w0 | 454 → 494 | 30.95 → 28.92 | [489, 498] |
| cont_int_c50 | w1 | 1068 → 1065 | 31.89 → 28.52 | [1059, 1070] |
| cont_int_c50 | w2 | 1034 → 1039 | 44.06 → 19.66 | [1036, 1042] |
| cont_int_c50 | w3 | 435 → 450 | 59.58 → 9.79 | [448, 451] |
| cont_int_c90 | w0 | 51 → 55 | 5.86 → 5.26 | [55, 56] |
| cont_int_c90 | w1 | 163 → 162 | 9.85 → 8.56 | [161, 164] |
| cont_int_c90 | w2 | 245 → 243 | 10.64 → 9.39 | [242, 244] |
| cont_int_c90 | w3 | 133 → 139 | 19.39 → 6.30 | [138, 140] |


[Full truths/quantiles/floors](rescore/truths_quantiles_floors.csv). The empirical floor minimizes the same five pinball losses used by the actual paper scorer; it is not a full-distribution CRPS oracle. A narrower fixed-state distribution is expected because it removes variation over different pre-day20 states. Changes in excess therefore reflect both changes in outcomes and in the floor; they should not be interpreted as newly demonstrated model deterioration on an unchanged statistical target.

![Fixed-state day-60 distributions](rescore/fixed_state_cdfs.png)


Prespecified prefixes, compared with the final N=1000 estimate:

| N | Largest quantile difference (people) | Largest floor difference (people) | Largest pooled model-score difference |
|---|---|---|---|
| 100 | 23 | 3.555 | 0.0237 |
| 300 | 12 | 1.983 | 0.0062 |
| 500 | 6 | 1.575 | 0.0049 |
| 1000 | 0 | 0.000 | 0.0000 |


These nested-prefix comparisons are convergence diagnostics, not independent validation samples or a stopping rule. [convergence.csv](rescore/convergence.csv) and [score_convergence.csv](rescore/score_convergence.csv) contain every item/panel; final split-half KS distances are also recorded. The two-fold 500/500 floor diagnostic has mean train-to-test optimism 0.070 people, maximum 0.236; it diagnoses empirical quantile estimation, not a correction applied to the paper score. [Floor split diagnostic](rescore/floor_split_diagnostic.csv).


Replay bootstrap uses **1,000 resamples**, selecting continuation indices independently within each world and sharing each index vector across coverage arms and horizons. Each resample recomputes truth quantiles, floors, scores, rankings and associations. Original truth estimates are held fixed when reporting changes; the intervals do not cover bias or Monte Carlo error in the old matched-seed target. Model-panel bootstrap uses **2,000 paired resamples of model identities** for before/after correlations, with truth held fixed. Models are an observed convenience panel, not a random sample of all possible models; the resampling interpretation assumes exchangeability. Combined-score model intervals resample fitted theta values, following the paper convention, without refitting a different model panel; replay intervals do refit the fixed panel. Neither interval resamples the four worlds, elicitation calls, external benchmark measurements or latent anchor states.

At N=1000, pointwise CDF standard error is at most 1.58 percentage points; approximate 95% margin at the median is ±3.10 pp, and at a decile ±1.86 pp. A conservative uniform 95% DKW bound is ±4.29 pp for one distribution, or ±5.98 pp simultaneously over all 32 by a union bound. These probability-scale bounds are not infection-count quantile error guarantees. Ties make order-statistic intervals conservative.


## Forecast coverage and retained limitations


| Source | Saved calls | Planned calls | Wholly missing model-items | Cells below planned reps |
|---|---|---|---|---|
| binary_int_c90 | 950 | 960 | 0 | 8 |
| binary_int_hold | 905 | 960 | 4 | 16 |
| binary_uncond | 957 | 960 | 0 | 3 |
| cont_int_c25 | 552 | 576 | 1 | 14 |
| cont_int_c50 | 558 | 576 | 1 | 11 |
| cont_int_c90 | 556 | 576 | 1 | 11 |
| cont_uncond | 567 | 576 | 0 | 6 |


There are **0 duplicate repetition keys** and **464 cells with repeated answer values**. Repeated values are not automatically duplicate calls or errors. The actual scorer takes coordinate-wise medians over every saved row, without deduplicating values or demanding all planned repetitions. We retained this behavior. No responses were imputed or newly elicited. [Forecast audit](rescore/forecast_audit.json), [all cell/repetition records](rescore/forecast_coverage.csv), [coverage by model/source](rescore/coverage_summary.csv).


DeepSeek V4 Flash has missing interventional items and is excluded from complete pooled intervention correlations/ranks; its available-item score remains in the paper-format long table. Models with every item answered but fewer repetitions remain eligible, including the Kimi K2 completion pattern. Unequal repetitions affect the median estimates and are not captured by replay or model-panel bootstrap intervals. Binary scores are retained unchanged; this continuous fixed-state production does not repair binary truth construction.


## Implementation, provenance and cost

The production runner imports the corrected, validated execution helper and retains its float-coverage, independent recipient-ID oracle, nonempty-uptake, exact timing, susceptibility, history, latent recovery, conservation and support assertions. Coverage is Bernoulli uptake among all 5,000 living agents, including infected/recovered agents, with 0.95 leaky efficacy. It is not exact-size vaccination or susceptible-only selection. Each seed set branches into 0%, 25%, 50%, 90% arms with common distribution roots; day-21 networks match and vaccinated sets strictly nest. All 40,000 distribution-root hashes are distinct across independent world/replicate/stream combinations. Distinct pseudo-random roots and prior fresh-process/daywise tests support the implementation; finite samples cannot prove statistical independence.


| Coverage | Branches | Minimum vaccinated | Maximum vaccinated | Mean vaccinated |
|---|---|---|---|---|
| 0 | 4000 | 0 | 0 | 0.00 |
| 0.25 | 4000 | 1132 | 1364 | 1249.24 |
| 0.5 | 4000 | 2377 | 2614 | 2499.24 |
| 0.9 | 4000 | 4430 | 4579 | 4500.02 |

[Full world/coverage validation counts](rescore/production_validation.csv).

Production passed **888,000 recorded helper assertions** (not independent statistical observations), plus pairing and checkpoint checks. Every checkpoint was re-read and validated in the separate scoring process; daily infection sums, support, sample counts and unchanged pre-day20 infection histories were checked again. Input hashes were verified before and after production and analysis, and 53 manuscript files were fingerprinted and preserved. The original paper scoring path reproduced all **576 saved rows exactly at its six-significant-digit serialization** before new truth files were substituted in memory. [Production result](SUCCESS.json), [rescore result](rescore/SUCCESS.json), [input hashes](rescore/input_hashes.json), [checkpoint hashes](checkpoint_hashes.json).


Frozen plan SHA-256: `a8ae21e3f62e1b9f265eac55ec05ab7c04d4321d56c19b6b1830d228ba0ff6bc`. [PLAN.json](PLAN.json) records all 4,000 seeds, worlds, arms, horizons, fixed sample size, analysis rules and input hashes before new scores were inspected. Production seed entropy is `[20260924,16000,world_index,rep]`, separate from the smoke-suite schedule. Existing serialized anchors and pre-drawn recovery states remain fixed. Starsim 3.3.4 / NumPy 2.5.2 / Python 3.13.7 generated trajectories; the separate scoring environment uses the paper's imported code.


Measured resumed production loop elapsed time (excludes first attempt and diagnostic pause): **9.64 minutes**; per-checkpoint work totals 23.76 minutes. Parent peak RSS (substantially higher than the smoke-suite estimate; cause not profiled): 6164.9 MiB. Rescore elapsed: **0.32 minutes**. Startup/import and report preparation are additional; these are measured stage timings, not inferred API latencies. Checkpoints occupy 8.10 MiB compressed. Full branch simulators were not saved. Paid model/cloud cost: **$0**. Diagnostic recomputed scales would be {'40': 90.0, '60': 90.0}; they were not used, because changing normalization would confound the before/after comparison.


Frozen plan to production completion wall time was **26.78 minutes**, including launch/import overhead and the diagnostic interruption. The first attempt reached at least 846.02 seconds before stopping; its final elapsed time was not recorded, so the valid-checkpoint work sum and resumed-loop timing above are the exact available processing measurements.

Atomic checkpoints store each completed four-arm seed set. Resume checks job identity and frozen plan and skips existing sets. Any incomplete set is recomputed deterministically. This run resumed after the documented assertion-only correction below, skipping 2,245 completed sets and recomputing the incomplete w2/245 set. There are 16,000 unique validated output branches and 16,004 starts in total: the failed attempt completed three unsaved arms and partially advanced one arm. No additional independent seeds were sampled.


## Preserved production failure and checker-only amendment

The first invocation stopped at w2/rep245/c90 because its independently predicted recipients differed by one agent. The simulator used the intended float64 probability 0.9. The checker compared float32 uniforms with a Python scalar, which NumPy treated as a weak scalar and rounded to float32. A uniform exactly 0.8999999761581421 was therefore excluded by the old checker but included by the simulator. This was an oracle error, not the previous integer-zero vaccine bug. Array-only diagnosis advanced no simulator steps.

The amendment uses an explicit NumPy float64 threshold; boundary-value tests for every coverage include a negative control that fails under the old 90% comparison. No seeds, sample size, simulator behavior, coverage values, previous successful outcomes, score rules or normalization changed. The failing set then passed with 4,492 vaccinated agents, matching the corrected independent prediction. The original code, frozen plan, log and failure JSON remain preserved. [Diagnosis](threshold_diagnosis.json), [frozen amendment](ORACLE_AMENDMENT.json), [corrected checker](/Users/elsehow/Projects/starsim-audit-20260923/production_v1/oracle_precision.py:16), [resume code](resume.py). A separate array-only audit regenerated all 16,000 recipient sets and verified their saved hashes/counts, without invoking simulator steps: [uptake verification](UPTAKE_VERIFICATION.json).


The scoring environment emitted NumPy matmul divide/overflow/invalid warnings, preserved in rescore.log. All available bootstrap scores were finite. Independent non-BLAS summation matched every bootstrap score and combined-score interval exactly; checks against the original scorer and iterative combined fitter differed by at most 1.6×10^-14. No corresponding numerical error was found, and the library-warning cause was not established. [Numerical verification](NUMERIC_VERIFICATION.json), [verification code](verify_numeric.py).

## Proposed manuscript implications — not applied

1. Replace the continuous ±15% seed-pooling description with the exact day-20 snapshot, 1,000 future continuation roots, paired-arm procedure, random vaccination semantics and validated displayed-count subtraction. Keep the historical design description distinguishable from the retrospective repair. [Current design](/Users/elsehow/Projects/iclr-score-refresh/paper/sections/06_starsim.tex:14).
2. Update continuous truths/floors, per-model and per-item tables, coverage/horizon figures, ECI/ForecastBench intervals and combined-score figures together if these results are accepted. Review abstract/discussion claims that cite their previous associations. Preserve explicit panels and the missing-repetition caveat. [Current results](/Users/elsehow/Projects/iclr-score-refresh/paper/sections/06_starsim.tex:34), [validation](/Users/elsehow/Projects/iclr-score-refresh/paper/sections/07_validation.tex:6).
3. Say that 200/300 are retained historical reference scales. They are no longer the median replay-range scales of this new distribution. Either retain them transparently for comparison or separately authorize a consistently relabeled normalization; do not quietly present the old constants as freshly estimated. [Current scoring description](/Users/elsehow/Projects/iclr-score-refresh/paper/sections/06_starsim.tex:28).
4. State the information limitation prominently: the fixed snapshot contains agent-level/network/disease/prognosis information not shown in the report. This target is P(Y | fixed full state, intervention), not automatically P(Y | displayed aggregate report, intervention). Proper report-only conditioning requires a distribution over compatible latent states. Merely narrowing cumulative-count windows does not supply that distribution.
5. Describe the outcome scores as interventional forecasting performance. They mix baseline epidemic prediction with response to vaccination and **do not isolate effect-estimation skill**. Shared randomness improves paired simulation comparisons but does not change what the elicited outcome score measures.

**Recommended next decision:** review and accept or reject this explicitly labeled retrospective fixed-state analysis for the paper before changing manuscript outputs. The production implementation is validated and sample size was fixed on precision grounds. Accepting the numerical rescore does not resolve the report-only versus hidden-state information convention. A prospective redesign or re-elicitation should be a separate decision; nothing here authorizes new paid calls.


## Reproducible commands and files

```sh
# Already executed: freeze once, then production (resume-safe)
sh /Users/elsehow/Projects/starsim-audit-20260923/production_v1/run.sh --freeze
sh /Users/elsehow/Projects/starsim-audit-20260923/production_v1/run.sh
# Recorded checker-only amendment; resume with this entry point
sh /Users/elsehow/Projects/starsim-audit-20260923/production_v1/resume.sh
# Separate offline analysis; uses the actual paper score_all(C)
sh /Users/elsehow/Projects/starsim-audit-20260923/production_v1/rescore.sh
```

The freeze command refuses to overwrite the existing plan. The initial run.sh entry point intentionally preserves the old checker; use resume.sh to apply the recorded assertion-only precision amendment when continuing/reproducing production. Preserve these outputs when reproducing in a versioned directory. [Production/checkpoint code](/Users/elsehow/Projects/starsim-audit-20260923/production_v1/production.py:30), [corrected execution helper](/Users/elsehow/Projects/starsim-audit-20260923/corrected_smoke/validate.py:46), [RNG reseeding helper](/Users/elsehow/Projects/starsim-audit-20260923/smoke/smoke.py:94), [actual scorer invocation](/Users/elsehow/Projects/starsim-audit-20260923/production_v1/rescore.py:80), [paired replay bootstrap](/Users/elsehow/Projects/starsim-audit-20260923/production_v1/rescore.py:84), [model-panel bootstrap](/Users/elsehow/Projects/starsim-audit-20260923/production_v1/rescore.py:124), [paper scorer](/Users/elsehow/Projects/iclr-score-refresh/paper/data/starsim/scripts/build_excess.py:48), [supplementary diagnostics](supplement.py).

File-only supplement/report commands use `uv run --offline --no-project --python /Users/elsehow/Projects/iclr-score-refresh/venv/bin/python --no-managed-python python` followed by the absolute path to `supplement.py` or `build_report.py`, with UV_CACHE_DIR/MPLCONFIGDIR set under this audit directory as in rescore.sh. No manuscript files were generated or installed.
