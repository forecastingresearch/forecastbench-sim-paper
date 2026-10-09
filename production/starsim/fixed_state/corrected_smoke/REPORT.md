# Corrected Starsim validation — 23 September 2026

**PASS: exactly 36 additional trajectory starts, then stopped.** The corrected vaccine suite contains 32 grid branches (four worlds × two continuation roots × four coverage arms), two fresh-process vaccinated repeats, and two daywise control/vaccine continuations. There were 2,628 passing assertions, including worker checks; these are software checks, not independent statistical observations. The previous 70-start suite and its integer-truncation failure evidence remain intact. No production simulation, model/API call, cloud spending, manuscript edit, or remote write occurred. [Machine result](RESULT.json), [accounting](summary.json), [36-start ledger](ledger.json), [preserved prior status](../smoke/VALIDATION_STATUS.json).

## Intervention correction and nonvacuous validation

The earlier harness assigned fractional coverage into an integer array initialized at zero. That silently produced zero vaccination. The correction replaces the array with an explicitly floating-point array, rather than assigning into its old storage. The new dose guard requires floating dtype and exact intended coverage. For each of 0.25, 0.50 and 0.90, negative controls recreate the integer assignment and confirm rejection; a separate empty-uptake control is rejected too. [Implementation](/Users/elsehow/Projects/starsim-audit-20260923/corrected_smoke/validate.py:20), [assignment](/Users/elsehow/Projects/starsim-audit-20260923/corrected_smoke/validate.py:47), [regression controls](/Users/elsehow/Projects/starsim-audit-20260923/corrected_smoke/validate.py:124).

All eight world/replicate combinations at each coverage passed:

| Intended coverage | Actual vaccinated, min–max | Eligible each run | Protection after administration |
|---|---:|---:|---|
| 0 | 0 | 5,000 | All relative susceptibilities 1 |
| 0.25 | 1,191–1,270 | 5,000 | Vaccinated 0.05; others 1 |
| 0.50 | 2,401–2,552 | 5,000 | Vaccinated 0.05; others 1 |
| 0.90 | 4,484–4,511 | 5,000 | Vaccinated 0.05; others 1 |

Coverage means independent Bernoulli uptake among all living agents, including infected and recovered agents; it does not promise exactly 25%, 50% or 90% vaccinated, or target only susceptibles. This matches the existing campaign's default eligibility, not an invented susceptible-only campaign. [Installed eligibility API](/Users/elsehow/Projects/iclr-2026/.venv/lib/python3.13/site-packages/starsim/interventions.py:54). Whether the prose prompt should communicate this more explicitly remains a scientific/prompt decision.

The uptake oracle reconstructs uniforms independently from each coverage distribution's stored RNG root, day jump and agent slots, then thresholds at the intended coverage. It does not invoke the campaign's selection method. Actual recipient IDs matched this oracle exactly in every grid branch. Every selected agent received exactly one dose at day 21; no later doses appeared. Within the actual loop, the test observed network updating, then vaccination, then SIR transmission. Vaccination immediately changed relative susceptibility to 0.05 for selected agents, preserved other infection/prognosis state at administration, and left unselected susceptibility at 1. No protection or vaccination existed through day 20. [Oracle and administration checks](/Users/elsehow/Projects/starsim-audit-20260923/corrected_smoke/validate.py:34).

The outcomes also demonstrate real treatment, without being used as a pass criterion for a presumed ranking. For w2/rep0, day-40/day-60 additional infections were 2,266/2,291 under control, 1,600/1,633 at 25%, 982/996 at 50%, and 223/223 at 90%. All 32 grid outcomes and uptake counts are in [grid.csv](grid.csv). Two replicates per world are insufficient to estimate production quantiles or treatment-effect precision.

## State, RNG, pairing and reproducibility

The suite reused the four previously validated serialized day-20 anchors. Original seed recreation against cached histories and pause/resume/serialization equivalence were established in the [prior suite](../smoke/REPORT.md); this suite did not spend additional starts repeating those historical runs. Each anchor was loaded, boundary-checked, copied and reseeded for future continuation. Existing anchor bytes and 120 fingerprinted prior artifacts/source inputs were checked before and after execution. Source copies remained unchanged after each branch. [Input hashes](inputs.json), [copy/reseed implementation](/Users/elsehow/Projects/starsim-audit-20260923/smoke/smoke.py:86).

The branch tests preserved displayed C20/I20, all recorded pre-boundary history, and preexisting infected agents' latent recovery times. They verified SIR conservation, no deaths, exact displayed-C20 subtraction, agreement with sums of daily infections after day 20, susceptible depletion, and support 0 ≤ Y40 ≤ Y60 ≤ 5000−C20. The four displayed C20 values are 431, 1129, 2316 and 3994, so their upper supports are 4569, 3871, 2684 and 1006. [Boundary checks](/Users/elsehow/Projects/starsim-audit-20260923/smoke/smoke.py:103), [history/support tests](/Users/elsehow/Projects/starsim-audit-20260923/corrected_smoke/validate.py:89).

Each world/replicate has ten registered distribution streams. All 80 stream seeds and root hashes were distinct across the eight continuation sets; arms within each set shared roots. The reseeding helper reinitializes the distribution and its stored history root, not merely `rand_seed` or the current generator state. Those inadequate alternatives were negative controls in the prior suite. Grid arms shared the actual day-21 network and strictly nested, nonempty vaccinated sets as coverage increased. Arm execution order was reversed for replicate 1. [Seeds, pairing and ordering](/Users/elsehow/Projects/starsim-audit-20260923/corrected_smoke/validate.py:133), [recorded streams](streams.json).

Two true 90%-coverage branches (w0/rep1 and w3/rep1) reproduced exactly in fresh processes, including administration IDs, roots, daily history and final fingerprint. They used normal `.run()` through day 21, independently checking the main harness's manual observation of loop steps. The additional w2/rep0 control/vaccine pair matched grid outcomes and shared actual networks and network RNG states on all 40 continuation days. This all-day network comparison covers one pair, not every world/coverage pair. [Worker and daywise checks](/Users/elsehow/Projects/starsim-audit-20260923/corrected_smoke/validate.py:149).

These checks establish distinct reproducible pseudo-random roots and correct common-random-number coupling in the exercised implementation. They cannot empirically prove statistical independence from eight roots. Common randomness also does not mean identical disease outcomes or identical numbers of disease draws after treatment changes who is susceptible. No global NumPy RNG consumption was detected on this path. Version-specific internals were exercised under Starsim 3.3.4, NumPy 2.5.2 and Python 3.13.7; changed versions need revalidation. [Environment](environment.json).

## Measured cost and production size

Measured wall time was **22.06 seconds**, including 12.17 seconds importing the environment (9.89 seconds thereafter). Parent peak RSS was 520,388,608 bytes, about 496 MiB; that is not combined parent-plus-worker peak memory. Grid continuation time averaged 0.0859 seconds, median 0.0535 seconds, maximum 1.0888 seconds including the first warm-up. Copying averaged 0.0197 seconds per grid branch. These measurements include instrumentation and come from a tiny local suite. [Timings](timings.json), [aggregation code](summarize.py).

Four worlds × N independent continuation sets per world × four arms gives **16N branches**. Each branch produces both horizons; horizons do not double the simulation count. Arms share randomness and must not be counted as independent replicates when assessing differences.

| N per world | Branches | Expected observations in lower 10% tail | Approx. 95% CDF margin at median | At decile | Serial extrapolation |
|---:|---:|---:|---:|---:|---:|
| 300 | 4,800 | 30 | ±5.66 percentage points | ±3.39 pp | 9.4 minutes |
| 1,000 | 16,000 | 100 | ±3.10 percentage points | ±1.86 pp | 31.3 minutes |

The margins are 1.96√(p(1−p)/N), pointwise on the probability scale, not quantile confidence widths in infection counts. Conservative 95% DKW uniform CDF bounds are ±7.84/4.29 pp for a single distribution at N=300/1000; a union bound covering all 32 world/arm/horizon distributions gives ±10.92/5.98 pp. These bounds do not require independence across arms. [Precision calculations](precision.csv).

Extrapolation uses mean continuation plus branch-copy time and one quarter of per-set load/copy/reseed cost. Plan approximately **10–20 minutes for 4,800** or **30–60 minutes for 16,000** locally, with substantial uncertainty from warm-up, instrumentation, host load and final output format. Parallel scaling was not benchmarked. The four existing compressed anchors total 1,236,461 bytes; the completed suite occupies approximately 6.1 MiB including caches before this report. For 16,000 branches, two int64 endpoints require 256 kB; two 41-day int64 series require about 10.5 MB. Compact outputs and metadata should fit comfortably within roughly 100 MB; saving all complete simulator snapshots would cost much more and is unnecessary. These are format-based estimates, not measured production usage. Paid calls required for these simulations: **zero**; no paid re-elicitation budget is implied.

## Recommendation and scientific limit

Recommend **N=1,000 per world, 16,000 branches**, if production is subsequently approved. Relative to N=300, this costs 3.33× and reduces Monte Carlo standard error by about 45%, giving roughly 100 rather than 30 lower-tail observations. This recommendation uses precision and measured cost, not model rankings, correlations or whether repaired results resemble the old results. N=300 can be an engineering checkpoint within a predeclared N=1000 run, not a stopping decision based on downstream scores.

Before execution, fix the estimand, seed schedule, intervention semantics, outputs and precision criteria. Keep the floating-array and nonempty-uptake guards in production, retain paired roots across arms, compute both horizons from each branch, and write compact resumable per-seed records. Report binomial/order-statistic intervals for the five quantiles and paired-seed bootstrap uncertainty for quantile floors and downstream scores. Any additional sampling should follow a declared precision rule independent of ranking/ECI outcomes. N=1000 does not guarantee a particular infection-count quantile error, especially for discrete distributions.

**The remaining scientific limitation is unchanged:** a continuation from one exact full latent state conditions on more information than the displayed aggregate report. It is a validated fixed-state experiment, not automatically the conditional distribution given only the model-visible counts/history. The fixed snapshot also preserves recovery times already drawn before day 20. A report-conditioned target instead requires a principled distribution over compatible latent states; choosing that target could require different simulations and prompt/response decisions. This suite clears the implementation blocker for fixed-state continuation; it does not settle that estimand choice or establish legitimate reuse of all old responses. No production or re-elicitation was executed.

## Reproduction

Executed suite command (the completed directory refuses a second main run):

```sh
sh /Users/elsehow/Projects/starsim-audit-20260923/corrected_smoke/run.sh
```

`run.sh` pins the existing interpreter, offline uv and cache locations. A newly authorized reproduction would copy `validate.py` and `run.sh` into a fresh sibling directory under this audit root, retaining `../smoke` and the fingerprinted original inputs. No such repeat is authorized or started here. The ledger enforces the 36-start limit for the main suite; direct worker mode is an internal helper, not a separate approved workload.

File-only recomputation (no simulator import or trajectory execution):

```sh
UV_CACHE_DIR=/Users/elsehow/Projects/starsim-audit-20260923/corrected_smoke/uv-cache uv run --offline --no-project --python /Users/elsehow/Projects/iclr-score-refresh/venv/bin/python --no-managed-python python /Users/elsehow/Projects/starsim-audit-20260923/corrected_smoke/summarize.py
```

Full raw checks: [parent](checks.json), [w0 worker](worker_w0/checks.json), [w3 worker](worker_w3/checks.json). Original failure evidence was preserved rather than rewritten to PASS.
