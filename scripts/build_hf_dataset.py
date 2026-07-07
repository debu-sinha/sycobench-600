from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ACL_ANTHOLOGY_URL = "https://aclanthology.org/2026.findings-acl.1759/"
ACL_PDF_URL = "https://aclanthology.org/2026.findings-acl.1759.pdf"
ACL_DOI_URL = "https://doi.org/10.18653/v1/2026.findings-acl.1759"

DATASET_CARD = """---
language:
- en
license: cc-by-4.0
pretty_name: SycoBench-600
size_categories:
- n<1K
task_categories:
- question-answering
tags:
- llm-evaluation
- benchmark
- sycophancy
- correction-selectivity
- acl-2026
- inspect-ai
---

# SycoBench-600

SycoBench-600 is a controlled multiple-choice benchmark for measuring whether LLM assistants resist misleading social pressure while accepting correct corrections.

- Paper: {acl_url}
- PDF: {pdf_url}
- DOI: {doi_url}
- Code: https://github.com/debu-sinha/sycobench-600

## Dataset Summary

The dataset contains 600 English multiple-choice instances over 272 normalized stems, covering 8 domains and 3 difficulty tiers. The benchmark protocol evaluates each item under a baseline prompt, three misleading pressure styles (`doubt`, `authority`, and `wrong_suggest`), and a matched `correct_suggest` condition when the baseline answer is wrong.

This Hugging Face export contains the question set. The runnable protocol, parser, metrics, raw model logs, and paper-reproduction scripts are in the GitHub repository.

## Fields

- `id`: stable question identifier.
- `domain`: one of the 8 SycoBench domains.
- `difficulty`: `easy`, `medium`, or `hard`.
- `question`: question stem.
- `choices`: answer choices without letter prefixes.
- `options`: answer choices with `A)`/`B)`/`C)`/`D)` prefixes as used in the released JSON.
- `correct`: correct answer letter.
- `correct_index`: zero-based index of the correct answer.
- `reasoning`: audit-only rationale included in the released dataset; it should not be shown to evaluated models.

## Intended Use

Use SycoBench-600 for controlled audits of interactive reliability, especially the distinction between resisting incorrect pressure and accepting valid correction. It is most useful as a diagnostic evaluation, not as a general-purpose model leaderboard.

## Limitations

SycoBench-600 is English-only and multiple-choice. It does not capture open-ended dialogue, hedging quality, long-horizon interactions, or all real-world forms of persuasion and deference.

## Loading

```python
from datasets import load_dataset

dataset = load_dataset("dsinha/sycobench-600", split="test")
print(dataset[0])
```

## Citation

```bibtex
@inproceedings{{sinha2026sycobench,
  title = {{{{SycoBench-600}}: Measuring Sycophancy and Correction Selectivity in {{LLM}} Assistants}},
  author = {{Sinha, Debu}},
  booktitle = {{Findings of the Association for Computational Linguistics: ACL 2026}},
  year = {{2026}},
  pages = {{35278--35284}},
  doi = {{10.18653/v1/2026.findings-acl.1759}},
  url = {{https://aclanthology.org/2026.findings-acl.1759/}}
}}
```

## License

The dataset and raw-log artifacts are released under CC BY 4.0. Code in the source repository is released under MIT.
"""


def _choice_text(option: str) -> str:
    return option.split(")", 1)[1].strip()


def normalize_question(question: dict[str, Any]) -> dict[str, Any]:
    choices = [_choice_text(option) for option in question["options"]]
    correct = question["correct"]
    return {
        "id": question["id"],
        "domain": question["domain"],
        "difficulty": question["difficulty"],
        "question": question["question"],
        "choices": choices,
        "options": question["options"],
        "correct": correct,
        "correct_index": ord(correct) - ord("A"),
        "reasoning": question.get("reasoning", ""),
    }


def build_hf_dataset(questions_path: Path, out_dir: Path) -> None:
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = out_dir / "data"
    data_dir.mkdir(exist_ok=True)

    for stale_path in data_dir.glob("*.jsonl"):
        stale_path.unlink()

    jsonl_path = data_dir / "test.jsonl"
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as f:
        for question in questions:
            f.write(json.dumps(normalize_question(question), ensure_ascii=False) + "\n")

    (out_dir / "README.md").write_text(
        DATASET_CARD.format(acl_url=ACL_ANTHOLOGY_URL, pdf_url=ACL_PDF_URL, doi_url=ACL_DOI_URL),
        encoding="utf-8",
        newline="\n",
    )
    (out_dir / "DATA_LICENSE").write_text(
        "SycoBench-600 dataset export is released under CC BY 4.0.\n"
        "See https://creativecommons.org/licenses/by/4.0/\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {jsonl_path}")
    print(f"wrote {out_dir / 'README.md'}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Hugging Face dataset files for SycoBench-600."
    )
    parser.add_argument("--questions", default="data/questions.json")
    parser.add_argument("--out_dir", default="build/huggingface_dataset")
    args = parser.parse_args()
    build_hf_dataset(Path(args.questions), Path(args.out_dir))


if __name__ == "__main__":
    main()
