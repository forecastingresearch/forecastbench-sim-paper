**Outcome: partial validation, with a blocker before production.** We used the full authorized limit of **70 trajectory starts** and stopped. Historical recreation, end-of-day20 snapshot handling, serialization, and replacement of future RNG roots worked. The first intervention harness silently truncated fractional vaccine coverage to zero because its probability array had integer dtype. Reviewing the actual outcomes caught this despite the original assertions passing. Replacing the array with floating-point probabilities worked in two final tests, but there was insufficient authorized budget to validate the corrected full intervention grid. **Do not use the initial fractional-arm outcomes as vaccine data, and do not start production yet.**

The issue is in this newly written smoke harness, not evidence that the original vaccine simulations used zero coverage. All twelve original fractional-vaccine recreation runs matched their historical caches; the original factory initialized probabilities with fractional values.

Everything is isolated under `/Users/elsehow/Projects/starsim-audit-20260923/smoke`. No paid calls, cloud spending, manuscript edits, remote writes, or production run occurred. Input fingerprints remain unchanged. Existing modified files in the shared repository were left untouched; the runner hash agrees with the prior feasibility inventory. The authoritative overall status is [VALIDATION_STATUS.json](/Users/elsehow/Projects/starsim-audit-20260923/smoke/VALIDATION_STATUS.json). Earlier `SUCCESS.json` files record the automated checks that passed at that stage; they do **not** certify correct intervention delivery and are superseded by this diagnosis.

**What ran.** [trajectory_ledger.json](/Users/elsehow/Projects/starsim-audit-20260923/smoke/trajectory_ledger.json) records every claimed start, including prefix-only anchors and repeated diagnostic branches; these are not 70 independent Monte Carlo samples.

| Work | Starts |
|---|---:|
| Original full historical trajectories: 4 worlds × control/c25/c50/c90 | 16 |
| Independent no-vaccine pause/resume trajectories | 4 |
| Dormant-campaign snapshot prefixes | 4 |
| Copied/serialized no-reseed scaffold controls | 4 |
| Two new continuation seeds × 4 worlds × 4 nominal arms | 32 |
| Fresh-process reproducibility branches | 2 |
| `rand_seed`-only and global-NumPy-seed-only negative controls | 2 |
| Full-population vaccine positive control | 1 |
| Daywise nominal control/c90 pair | 2 |
| Current-RNG-state-only negative control | 1 |
| Corrected floating-probability c25/c90 tests in w2 | 2 |
| **Total** | **70** |

The 24 fractional arms in the 32-branch block, both nominal c90 fresh-process repeats, and the nominal c90 daywise branch actually received zero vaccine. Their evidence remains useful for snapshot/RNG reproducibility, not intervention efficacy or coverage comparisons. The 100% coverage control was valid because integer 1 is representable, so it did not catch fractional truncation.

**Verified state recreation and boundary accounting.** The environment was Python 3.13.7, Starsim 3.3.4, NumPy 2.5.2 and Sciris 3.3.0 on macOS arm64, `single_rng=False` ([environment.json](/Users/elsehow/Projects/starsim-audit-20260923/smoke/environment.json)). Source hashes and dependency metadata are in [inputs.json](/Users/elsehow/Projects/starsim-audit-20260923/smoke/inputs.json) and the earlier [feasibility manifest](/Users/elsehow/Projects/starsim-audit-20260923/feasibility/source_manifest.json).

All four displayed seeds—27, 33, 62, 47—reproduced exact displayed C20/I20 of **431/327, 1129/911, 2316/1944, 3994/3389**. Baseline and 90%-vaccine runs matched all cached cumulative checkpoints at days 0/5/10/15/20/40/60, initial infection counts, and cached day0/day20 active counts. Original 25%/50% trajectories matched the full cached 91-point cumulative arrays. The four no-vaccine pause/resume trajectories equaled their independently run uninterrupted trajectories through day90, including named physical arrays at the endpoint. See [cached_check](/Users/elsehow/Projects/starsim-audit-20260923/smoke/smoke.py:110) and [checks.json](/Users/elsehow/Projects/starsim-audit-20260923/smoke/checks.json).

`run(until=2020)` stopped after all day20 functions: sim/module clocks were 21 and the next bound function was `sim.start_step`. The simulations were neither complete nor finalized. Dormant-campaign anchors matched the original controls' common physical arrays, recorded prefix, and common RNG paths/states. Cached summaries do not preserve historical latent arrays, so this is strong reproducibility evidence under the recreated implementation, not a direct comparison with an archived original full state.

The paused-run cumulative-array trap was handled correctly. [ever()](/Users/elsehow/Projects/starsim-audit-20260923/smoke/smoke.py:66) reconstructs ever-infected from daily new infections plus the initial cases. Post-day20 outcomes sum `new_infections[21:t+1]`, checked against endpoint cumulative minus the exact displayed count and against susceptible depletion. They obeyed 0≤Y40≤Y60≤5000−C20; S+I+R remained 5000. All pre-day21 recorded histories remained unchanged, and already-infected agents retained their sampled recovery times during continuation.

**Copying and serialization.** All four unshrunk snapshots were saved, reloaded, compared by physical/history/RNG fingerprints, and checked for correct module and bound-method references. Deep copies shared neither named state-array storage nor RNG objects with their sources. Anchors remained unchanged after branches. Compressed snapshots are 299,785–319,015 bytes each, **1,236,461 bytes total** ([snapshot_sizes.json](/Users/elsehow/Projects/starsim-audit-20260923/smoke/snapshot_sizes.json)). They contain the integer-zero dormant campaign configuration; any future use must replace its probability array explicitly with float values.

**Future RNG support established, within limits.** The adapter [reseed()](/Users/elsehow/Projects/starsim-audit-20260923/smoke/smoke.py:94) reinitializes each existing distribution using its saved trace, module and slot links. It replaces both its generator and stored initial history, preserving physical arrays, recorded history, clocks and distribution parameters. The module's next timestep jump then operates from the new root. The registry had ten distributions: contact count, initial prevalence, infection duration, death probability, network permutation, source and target transmission, campaign uptake, age and sex. Some are initialization-only or degenerate in this scenario, but all were tracked.

The eight `(world,replicate)` child seeds produced **80 distinct distribution seeds and 80 distinct initial-root hashes**, without collision in this suite. Relevant sim/module/slot links remained intact. The two fresh-process runs reproduced complete daily outcomes and recorded physical/RNG fingerprints exactly, after reloading from disk. These were actually control-dose branches, so fresh-process reproducibility for the corrected fractional interventions remains to be checked. Both independent continuation seeds yielded different baseline trajectories in every world. The four nominal arm duplicates must not be counted as independent corroboration.

Three negative controls reproduced the original future unchanged: changing only `sim.pars.rand_seed`; changing only `np.random.seed`; or replacing current generator state while retaining the saved initial RNG history. The last control demonstrates why altering current state alone fails: the next module timestep resets/jumps from the old saved root. See [extended_checks.py](/Users/elsehow/Projects/starsim-audit-20260923/smoke/extended_checks.py:1).

These are code-level and reproducibility checks. Two child seeds per world do not statistically establish independence, Monte Carlo accuracy, correct tail quantiles, or distributional equivalence to an observation-conditioned sampler. Distinct seed/root hashes are necessary engineering evidence, not a statistical proof. No new quantile scores or rankings should be inferred from this smoke sample.

**The blocker and nonvacuous correction.** [smoke.py:125](/Users/elsehow/Projects/starsim-audit-20260923/smoke/smoke.py:125) assigned `campaign.prob[:] = cov`. Because the dormant campaign had been initialized with integer `0`, the array was integer-valued; .25/.50/.90 became zero. The original efficacy check tested `.05` susceptibility only on vaccinated IDs; with an empty set, that condition passed vacuously. Nested uptake sets also passed because every set was empty. This is why successful assertion counts alone were not accepted as validation.

The static diagnosis reproduced truncation on a standalone array, without simulation. The final two authorized trajectories used [coverage_diagnosis.py:31](/Users/elsehow/Projects/starsim-audit-20260923/smoke/coverage_diagnosis.py:31):

```python
campaign.prob = np.full(campaign.prob.shape, coverage, dtype=float)
assert np.all(campaign.prob == coverage)
```

They explicitly checked dtype/value, nonzero and plausible realized uptake, day21 vaccination dates, leaky susceptibility .05 for vaccinated agents and 1 otherwise, fixed prehistory/recovery times, shared day21 network and initial RNG roots with their baseline, and feasible outcomes. Results for the same w2 state and r0 continuation seed:

| Actual coverage | Vaccinated on day21 | New infections to day40 | To day60 |
|---|---:|---:|---:|
| Control | 0 | 2266 | 2291 |
| 25% | 1270 | 1600 | 1633 |
| 90% | 4511 | 223 | 223 |

See [coverage_fix/RESULT.json](/Users/elsehow/Projects/starsim-audit-20260923/smoke/coverage_fix/RESULT.json) and its [checks](/Users/elsehow/Projects/starsim-audit-20260923/smoke/coverage_fix/checks.json). These outcomes are examples, not probability/quantile estimates. Do not impose pathwise monotonic treatment effects as a universal simulator invariant; this particular pair showed the expected reduction.

The 40-day network equality test and absence of global NumPy draws were established for two actual control branches, not a real control/vaccine pair. The corrected treatments matched the paired baseline's day21 network and root hashes; shared realized network draws over their full horizons were not recorded in this corrected subset. This, full-grid coverage testing, and corrected-treatment process reproducibility remain open. The hard start budget is exhausted, so no further simulations were attempted.

**Next validation—not production.** I recommend a separately approved **36-start corrected suite using the validated saved anchors**: 32 branches covering all four worlds × two continuation seeds × four real doses, two fresh-process fractional-treatment repeats, and a two-branch daywise control/vaccine pairing check. No need to repeat historical recreations unless the environment/factory changes. It should replace the probability array with float values and independently assert configured dose, nonempty uptake for these fractional-dose fixtures, vaccination timing, susceptibility change, preserved anchors, and correct pairing. The old harness should be retained as failure evidence; the corrected suite gets a new directory and explicit budget. A candidate patch is [coverage_fix.patch.txt](/Users/elsehow/Projects/starsim-audit-20260923/smoke/coverage_fix.patch.txt), not an executed full-grid validation.

After that gate, a defensible production plan is 1,000 independent future-seed sets per world, each cloned into control/c25/c50/c90: **16,000 branches**, recording both horizons per branch. Stop/checkpoint at 300 per world to inspect Monte Carlo diagnostics, not to choose favorable rankings. Keep treatment pairing and bootstrap at the replicate/world level; store actual configured/realized dose and raw outcomes. Recompute empirical quantiles, floors and scales under the new reference, with uncertainty and independent-batch checks. Do not optimize selection or sample size to preserve old model rankings. Binary probabilities and old hold/flip certifications would need separate review; this suite did not validate those outcomes.

**Measured resources and qualified production estimates.** Measurements are in [timings.json](/Users/elsehow/Projects/starsim-audit-20260923/smoke/timings.json), [coverage_fix/timings.json](/Users/elsehow/Projects/starsim-audit-20260923/smoke/coverage_fix/timings.json), and the pre-diagnosis [summary.json](/Users/elsehow/Projects/starsim-audit-20260923/smoke/summary.json). The latter's automatic estimates mostly measure actual control branches and must not be treated as a complete intervention benchmark.

- Main import/cache setup: 15.4 seconds. First full historical run: 1.15 seconds; remaining full historical runs averaged .154 seconds. Main suite active time after import was 13.5 seconds, including its two fresh-process repeats; this excludes human review and later diagnostic stages.
- Day20 prefix: .059–.101 seconds. Main 40-step branches: mean .061 seconds, median .058, with copy mean .026 seconds. Pair preparation/reseed added about .050 seconds per four-arm set, including associated checks.
- Corrected treatment continuations took .317 seconds (c25) and .053 seconds (c90). There are only two such timings, with possible warm-up/process effects; no precise treated-branch throughput claim is warranted.
- Peak main-process RSS: 494,616,576 bytes (~472 MiB); compressed anchors total ~1.24 MB. This is not a measured multiworker peak.

For planning, allow **.1–.4 seconds per branch** including copy/amortized reseed, before production reporting/validation overhead: roughly **8–32 minutes serial for 4,800 branches**, or **27–107 minutes for 16,000**. Reserve about two hours locally for the latter plus checkpoint/report overhead until the corrected suite refines the estimate. These are extrapolations, not guarantees; no multiprocess speedup has been benchmarked. Reuse a warm process rather than paying ~1.7–2.0 seconds of startup per branch.

At N=1,000/world, endpoint-only float64 data need 256 KB; 41-step infection and active-count arrays together need about 10.5 MB, plus provenance and checkpoints. Reserving 100 MB for compact production outputs should be ample absent full per-agent logs. Retain four anchors and selected diagnostic snapshots, not 16,000 complete objects. No cloud resources are required by this plan.

No paid model calls were made or are needed for further simulator validation. If a changed task/report requires fresh continuous elicitation, the previous artifact-based projection remains approximately **$23.11 for 2,304 successful calls**, excluding retries, pricing changes and longer prompts; this is historical-cost arithmetic, not current pricing or an approved budget. Proper task design comes first. We should not choose a misleading reference merely to reuse old answers.

**Scientific caveat still unchanged.** Validated branching would fix the exact displayed physical state—including hidden infection/recovery schedules—while resampling future innovations. That is P(Y|full state), not P(Y|aggregate report). Reusing responses under a disclosed snapshot benchmark convention is possible, but does not make the full-state oracle attainable from the report alone. If exact report-conditioning is required, new compatible-state sampling or a redesigned elicitation protocol remains necessary. A new explanatory prompt does not itself remove hidden information. This smoke suite addresses engineering feasibility, not that target-definition decision.

**Reproduction and evidence preservation.** Code as actually executed is [smoke.py](/Users/elsehow/Projects/starsim-audit-20260923/smoke/smoke.py), [extended_checks.py](/Users/elsehow/Projects/starsim-audit-20260923/smoke/extended_checks.py), and [coverage_diagnosis.py](/Users/elsehow/Projects/starsim-audit-20260923/smoke/coverage_diagnosis.py). The shared ledger has a hard limit of 70. Completed-stage guards and the exhausted ledger intentionally prevent automatic repetition in this directory.

The recorded main command was:

```sh
sh /Users/elsehow/Projects/starsim-audit-20260923/smoke/run_smoke.sh
```

The extension and diagnosis used the same offline environment/cache variables as that launcher, running respectively `extended_checks.py` and `coverage_diagnosis.py` via:

```sh
uv run --offline --no-project \
  --python /Users/elsehow/Projects/iclr-2026/.venv/bin/python \
  --no-managed-python python PATH_TO_SCRIPT
```

A later authorized reproduction must use a fresh isolated directory and update the launcher's audit path, preserving the existing evidence and budget. The source manifest and [artifact_manifest.json](/Users/elsehow/Projects/starsim-audit-20260923/smoke/artifact_manifest.json) identify original inputs and saved outputs. [finalize_report.py](/Users/elsehow/Projects/starsim-audit-20260923/smoke/finalize_report.py) performs only file validation and accounting; it imports no simulator. The immediate next decision is approval of the corrected 36-start validation gate, **not** production or paid elicitation.
