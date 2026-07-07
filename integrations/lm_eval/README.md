# lm-evaluation-harness follow-up

Add the lm-evaluation-harness adapter after the Hugging Face dataset is public and loadable.

Planned task shape:

- Dataset path: `debu-sinha/sycobench-600`
- Split: `test`
- Task type: multiple choice baseline evaluation, with SycoBench-specific follow-up protocol documented separately.
- Prompt: question plus A/B/C/D choices and exact-one-letter instruction.
- Target: `correct_index` or `correct`, depending on harness config support.

This should be a follow-up PR after issue #4 is complete, because lm-eval works best when the dataset is hosted through Hugging Face datasets.
