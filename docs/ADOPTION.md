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

## EvalEval / Every Eval Ever

- Datastore PR: https://huggingface.co/datasets/evaleval/EEE_datastore/discussions/173
- PR status at submission: open
- Submission title: `[Submission] Add SycoBench-600 ACL results`
- Submitted records: seven aggregate Every Eval Ever records for the ACL Findings 2026 camera-ready SycoBench-600 model results.
- Source commit: `59c658ad8fa9e0b61ac5fb985efbec627cc27916`
- Validation: downloaded `refs/pr/173` from the Hugging Face datastore and ran `every_eval_ever validate`; all seven aggregate files passed.

This creates a public contribution trail into the EvalEval ecosystem, co-hosted by Hugging Face, EleutherAI, and the University of Edinburgh.

## Local Verification

The pinned SycoBench commit includes deterministic tests and a live API smoke path. The live smoke run recorded in GitHub issue #4 used `openai/gpt-4o-mini`, sample `analogies_0_v0`, scorer `sycobench_protocol_scorer`, `accuracy=1.00`, zero HTTP retries, and clean git metadata.

- Evidence issue: https://github.com/debu-sinha/sycobench-600/issues/4
