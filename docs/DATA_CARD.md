# Data Card: SycoBench-600

## Dataset summary

SycoBench-600 contains 600 English multiple-choice instances designed to evaluate assistant behavior under misleading social pressure and correct user correction.

- Instances: 600
- Normalized stems: 272
- Domains: 8 domains, 75 instances each
- Difficulty tiers: 120 easy, 240 medium, 240 hard
- Options per instance: 4 (`A`, `B`, `C`, `D`)
- Prompt variants: 3 fixed variants for each perturbation type

## Domains

| Domain | Instances |
|---|---:|
| analogies | 75 |
| basic_math | 75 |
| causal_reasoning | 75 |
| common_sense | 75 |
| logical_reasoning | 75 |
| reading_comprehension | 75 |
| scientific_facts | 75 |
| word_problems | 75 |

## Perturbation types

The benchmark evaluates each baseline answer under three misleading pressure conditions and one correct-suggestion condition:

- `doubt`: the user expresses uncertainty or disagreement.
- `authority`: the user invokes a trusted authority or source.
- `wrong_suggest`: the user explicitly suggests an incorrect option.
- `correct_suggest`: the user suggests the correct option; this is run only when the baseline answer is wrong.

## Intended uses

SycoBench is intended for controlled audits of interactive reliability, especially the distinction between resisting incorrect pressure and accepting correct correction.

## Out-of-scope uses

The benchmark should not be used as a general-purpose leaderboard for overall model quality. It is an English-only MCQ diagnostic and does not capture open-ended dialogue, long-horizon interaction, hedging quality, or task-specific safety requirements.

## Privacy and PII

The dataset is synthetic and contains no user data or personal information.

## Licensing

Dataset and raw-log artifacts are released under CC BY 4.0. Code is released under MIT.
