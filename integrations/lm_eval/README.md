# lm-evaluation-harness adapter

SycoBench-600 includes a baseline multiple-choice adapter for [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness).

This adapter intentionally covers only the single-turn baseline MCQ task. The full SycoBench protocol with misleading follow-up turns and correction-selectivity scoring is implemented in `sycobench/inspect_task.py` for Inspect AI.

- Dataset path: `dsinha/sycobench-600`
- Split: `test`
- Task: `sycobench_600_baseline`
- Config: `integrations/lm_eval/sycobench_600.yaml`

Example:

```bash
lm_eval \
  --include_path integrations/lm_eval \
  --tasks sycobench_600_baseline \
  --model hf \
  --model_args pretrained=EleutherAI/pythia-70m \
  --limit 10
```

For a prompt-format smoke check without installing lm-evaluation-harness:

```bash
pytest tests/test_lm_eval_adapter.py -q
```

To validate the adapter with lm-evaluation-harness installed:

```bash
lm_eval validate \
  --tasks sycobench_600_baseline \
  --include_path integrations/lm_eval
```
