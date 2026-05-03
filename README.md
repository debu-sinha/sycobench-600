# SycoBench-600

[![CI](https://github.com/debu-sinha/sycobench-600/actions/workflows/ci.yml/badge.svg)](https://github.com/debu-sinha/sycobench-600/actions/workflows/ci.yml)

**SycoBench-600: Measuring Sycophancy and Correction Selectivity in LLM Assistants**  
ACL 2026 Findings camera-ready artifact.

SycoBench-600 is a controlled multiple-choice benchmark for evaluating whether LLM assistants can resist misleading user pressure while still accepting correct corrections. The benchmark includes 600 English MCQ instances across 8 domains and 3 difficulty tiers, evaluated under three misleading pressure styles and one matched correct-suggestion condition.

## What is released

- `data/questions.json` - the final SycoBench-600 dataset.
- `results/raw_camera_ready/` - raw model logs, parsed answers, correctness flags, provider metadata, and prompt records.
- `sycobench/` - parser, prompt construction, metric, validation, and OpenAI-compatible client utilities.
- `scripts/validate_and_build.py` - regenerates the result table, confidence intervals, and figures from raw logs.
- `scripts/validate_paper_full.py` - checks paper tables, figures, citations, references, dataset statistics, and example traces against the release artifacts.
- `paper/` - ACL source files and the submitted camera-ready PDF.

## Headline results

All numbers below are computed on the 555-question intersection available for all seven evaluated models. Mistral-7B could not be rerun on 45 repaired items because the original provider retired the model, so the paper reports the common intersection for comparability.

| Model | Acc | PRA_all | Syco | Stub_nc | Sel |
|---|---:|---:|---:|---:|---:|
| Claude-3.5-Haiku | 72.9 | 28.5 | 36.4 [33.2-39.6] | 0.2 [0.0-0.7] | 52.2 |
| Claude-Sonnet-4 | 92.9 | 57.4 | 19.4 [17.3-21.6] | 17.8 [7.1-30.0] | 62.8 |
| Gemini-2.5-Flash | 95.3 | 81.7 | 7.1 [5.7-8.6] | 41.0 [26.1-57.4] | 54.3 |
| GPT-4o | 83.3 | 64.8 | 14.3 [11.9-16.9] | 19.8 [13.9-26.3] | 71.6 |
| GPT-4o-mini | 79.1 | 29.8 | 34.7 [32.1-37.4] | 64.7 [59.1-69.8] | 27.7 |
| Llama-4-Maverick | 67.7 | 58.1 | 5.9 [4.6-7.2] | 45.8 [38.5-53.1] | 33.5 |
| Mistral-7B | 63.2 | 17.4 | 50.5 [46.7-54.4] | 17.0 [13.6-21.0] | 13.4 |

Definitions:

- **Acc**: baseline accuracy.
- **PRA_all**: pressure-robust accuracy, requiring baseline correctness and correctness under all misleading pressure styles.
- **Syco**: macro-average flip-to-wrong rate across doubt, authority, and wrong-suggestion pressure, conditioned on baseline correctness.
- **Stub_nc**: no-change rate under a correct suggestion, conditioned on baseline-wrong runs.
- **Sel**: correction selectivity, defined as Update - WrongFlip.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest -q
python scripts/validate_paper_full.py
python scripts/validate_and_build.py \
  --raw_dir results/raw_camera_ready \
  --questions data/questions.json \
  --out_dir build/camera_ready \
  --use_intersection \
  --n_boot 2000
```

For a faster smoke rebuild, use `--n_boot 50`. The published table was generated with `--n_boot 2000`.

## Running new model evaluations

The evaluation runner supports OpenAI-compatible Chat Completions APIs, including OpenAI, OpenRouter, Together-compatible endpoints, and local vLLM-style deployments.

```bash
export OPENAI_API_KEY=...
export OPENROUTER_API_KEY=...
export TOGETHER_API_KEY=...

python scripts/run_eval.py \
  --config configs/models.yaml \
  --questions data/questions.json \
  --out results/new_run \
  --variants 3 \
  --seed 0 \
  --temperature 0 \
  --max_tokens 128
```

The runner records raw responses, parsed choices, correctness flags, prompt variants, usage metadata when available, and provider response metadata. API keys are read only from environment variables and are not written to logs.

## Reproducibility notes

- The parser extracts the last standalone uppercase `A`/`B`/`C`/`D` in a response, with an exact-one-letter fallback for lowercase single-letter responses.
- Confidence intervals use a cluster bootstrap over question IDs, preserving all three prompt variants for each sampled question.
- Reported results use the 555-question intersection across all models.
- Raw logs are intentionally included so alternate parsers or metrics can be audited without rerunning model APIs.

See `docs/REPRODUCIBILITY.md`, `docs/DATA_CARD.md`, and `docs/METRICS.md` for details.

## Repository layout

```text
sycobench-600/
├── data/                       # final benchmark dataset
├── results/raw_camera_ready/    # raw logs for the paper results
├── sycobench/                  # reusable package code
├── scripts/                    # evaluation, validation, and artifact build scripts
├── build/camera_ready/          # generated CSV/table/figure artifacts
├── paper/                      # ACL source and submitted PDF
├── tests/                      # reproducibility and unit tests
└── docs/                       # data card, metrics, and reproducibility docs
```

## Citation

```bibtex
@inproceedings{sinha2026sycobench,
  title = {{SycoBench-600}: Measuring Sycophancy and Correction Selectivity in {LLM} Assistants},
  author = {Sinha, Debu},
  booktitle = {Findings of the Association for Computational Linguistics},
  year = {2026}
}
```

## License

Code is released under the MIT License. Dataset and raw-log artifacts are released under CC BY 4.0; see `DATA_LICENSE` and `NOTICE.md`.
