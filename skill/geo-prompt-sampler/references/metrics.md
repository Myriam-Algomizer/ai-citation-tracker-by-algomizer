# Metrics

Why repeated runs: one LLM answer is one draw from a distribution. The same prompt returns different brands and different sources each time. Every figure below is a rate across runs, reported with the run count behind it.

## In the sheet

| Column | Formula |
|---|---|
| Citations | Times the page was cited, summed over the runs in the tab |
| Citation % | Page citations / all citations in the tab |
| Appearance rate | Runs that cited the page / runs in the tab. A page cited 3 times in one answer and never again scores high on Citation % and low here. Appearance rate is the steadier signal. |

## In summary.json and the chat summary

**Brand mention rate**: answers naming the brand / runs. Range: Wilson 95% interval, which behaves at small n and at 0% or 100% where the plain formula fails. With z = 1.96:

```
centre = (p + z²/2n) / (1 + z²/n)
half   = z·sqrt(p(1−p)/n + z²/4n²) / (1 + z²/n)
```

At 8 runs a 63% rate spans about 31% to 86%. Two brands whose ranges overlap are level; the script lists those pairs under `overlap_notes` once a prompt-LLM pair has 7 runs.

**Named first / average position**: order of first appearance in the answer text.

**Domain citation share**: domain citations / all citations. Range: bootstrap over answers, 1,000 resamples, recomputing numerator and denominator each time (Sielinski, "Quantifying Uncertainty in AI Visibility", arXiv 2603.08924). Computed from 8 runs up. Differences under 5 to 7 points are usually noise.

**Stability**: mean pairwise Jaccard overlap between runs, for the set of brands named and for the set of pages cited. 1 means every run returned the same set, 0 means no overlap. Source stability sits far below brand stability in practice.

**Pages seen in one run only**: how much of the source list a single run would have missed or overstated.

**Shared pages between LLMs**: count of pages cited by both.

## Run counts

Floors from Schulte, Bleeker and Kaufmann, "Don't Measure Once" (arXiv 2604.07585): 7 runs per prompt and LLM for brand figures, 8 when sources matter. The script warns under 8. Fix the run count before collecting; adding runs until the number looks good biases it.

Budget guidance from the variance-components work (arXiv 2607.13304): past 5 to 8 repeats of one prompt, extra budget does more when spent on paraphrases of the prompt and on more LLMs than on further repeats.

Aggregate over a rolling 2 to 4 week window when tracking over time, since source sets drift day to day.
