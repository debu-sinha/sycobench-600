# Inspect Evals Register submission

Inspect Evals moved community eval submissions to the Register model on May 8, 2026. The SycoBench implementation should stay in this repository, while the Inspect Evals repo should contain a register entry pointing to a pinned commit.

Open process question: https://github.com/UKGovernmentBEIS/inspect_evals/issues/1896

Submission inputs after the adapter lands on `main`:

- Methodology source: https://aclanthology.org/2026.findings-acl.1759/
- DOI: https://doi.org/10.18653/v1/2026.findings-acl.1759
- Source URL: GitHub blob URL to `sycobench/inspect_task.py` at a 40-character commit SHA, anchored to `sycobench_600`.
- Task: `sycobench_600`

Do not submit the Register issue until the source URL points to a pushed commit that includes the Inspect adapter and passing e2e tests.
