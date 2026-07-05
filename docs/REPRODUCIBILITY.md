# Reproducibility

This document describes how to reproduce the camera-ready tables, figures, and paper consistency checks from the released artifacts.

## Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On Windows PowerShell, use `.\.venv\Scripts\Activate.ps1` instead of `source .venv/bin/activate`.

The project is tested with Python 3.10+.

## Validate release integrity

```bash
pytest -q
python scripts/validate_paper_full.py
```

The paper validation script checks:

- LaTeX labels and references.
- Citation keys against `paper/references.bib`.
- Table 3 values against `build/camera_ready/tables/main_results.csv`.
- Table 4 pressure-type values recomputed from raw logs.
- Figure presence.
- Example traces against `results/raw_camera_ready/gpt-4o-mini.json`.
- Dataset size, stem count, difficulty distribution, author block, and final-copy status.

## Regenerate tables and figures

```bash
python scripts/validate_and_build.py \
  --raw_dir results/raw_camera_ready \
  --questions data/questions.json \
  --out_dir build/camera_ready \
  --use_intersection \
  --n_boot 2000
```

`--use_intersection` reproduces the paper setting: all metrics are computed on the 555 question IDs available for every model. This is necessary because Mistral-7B was not rerun on 45 repaired instances.

For a quick smoke run:

```bash
python scripts/validate_and_build.py \
  --raw_dir results/raw_camera_ready \
  --questions data/questions.json \
  --out_dir /tmp/sycobench_build \
  --use_intersection \
  --n_boot 50
```

## Recompile the paper

```bash
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error sycobench_camera_ready.tex
```

A TeX installation with BibTeX is required. The submitted PDF is included at `paper/sycobench_camera_ready.pdf`.

## Rerun models

The release includes raw logs, so rerunning APIs is not required to reproduce the paper results. To run new models or repeat the protocol:

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

On Windows PowerShell, set those variables as `$env:OPENAI_API_KEY = "..."`, `$env:OPENROUTER_API_KEY = "..."`, and `$env:TOGETHER_API_KEY = "..."`.

Provider implementations may change over time. Raw logs should therefore be treated as the authoritative artifact for the paper snapshot.
