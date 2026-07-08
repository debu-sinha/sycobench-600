# Inspect Evals Register

SycoBench-600 is listed as an external evaluation in the Inspect Evals Register:

- Register entry: https://github.com/UKGovernmentBEIS/inspect_evals/tree/main/register/sycobench-600
- Merged PR: https://github.com/UKGovernmentBEIS/inspect_evals/pull/1901
- Merge commit: `6a1edbccc4fc25b4c22132c9d70f1aac0e72bb2b`
- Merged at: `2026-07-08T01:25:33Z`
- Pinned SycoBench commit: `5219abda88de91300adcfefa37c3a824f0f103de`

The Register entry points to the Inspect AI task in this repository:

- Methodology source: https://aclanthology.org/2026.findings-acl.1759/
- DOI: https://doi.org/10.18653/v1/2026.findings-acl.1759
- Task: `sycobench_600`

Run directly from this repository with:

```bash
inspect eval sycobench/inspect_task.py@sycobench_600 --model openai/gpt-4o-mini -T limit=10
```
