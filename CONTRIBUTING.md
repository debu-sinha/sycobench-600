# Contributing

Contributions that improve reproducibility, validation coverage, documentation clarity, or evaluation extensions are welcome.

Please keep changes auditable:

1. Include a concise description of the change and why it is needed.
2. Add or update tests for parser, metric, data, or validation changes.
3. Avoid changing released camera-ready raw logs unless the change is explicitly a new release snapshot.
4. Do not commit API keys, local environment files, or provider credentials.

Run before opening a pull request:

```bash
pytest -q
python scripts/validate_paper_full.py
python scripts/validate_and_build.py --raw_dir results/raw_camera_ready --questions data/questions.json --out_dir /tmp/sycobench_build --use_intersection --n_boot 50
```
