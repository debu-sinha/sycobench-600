# Adoption Notes

This document records public, independently verifiable adoption and integration events for SycoBench-600.

## Inspect Evals Register

- Register entry: https://github.com/UKGovernmentBEIS/inspect_evals/tree/main/register/sycobench-600
- Merged PR: https://github.com/UKGovernmentBEIS/inspect_evals/pull/1901
- Merge commit: `6a1edbccc4fc25b4c22132c9d70f1aac0e72bb2b`
- Merged at: `2026-07-08T01:25:33Z`
- Merged by: `celiawaggoner`
- Pinned SycoBench commit: `5219abda88de91300adcfefa37c3a824f0f103de`
- Registered task: `sycobench_600`

The Inspect Evals Register entry links the ACL Findings benchmark to a runnable external Inspect AI evaluation.

## Dataset

- Hugging Face dataset: https://huggingface.co/datasets/dsinha/sycobench-600
- ACL Anthology paper: https://aclanthology.org/2026.findings-acl.1759/
- DOI: https://doi.org/10.18653/v1/2026.findings-acl.1759

## Local Verification

The pinned SycoBench commit includes deterministic tests and a live API smoke path. The live smoke run recorded in GitHub issue #4 used `openai/gpt-4o-mini`, sample `analogies_0_v0`, scorer `sycobench_protocol_scorer`, `accuracy=1.00`, zero HTTP retries, and clean git metadata.

- Evidence issue: https://github.com/debu-sinha/sycobench-600/issues/4
