#!/usr/bin/env python3
"""Run SycoBench evaluation for one or more models.

Run from the repository root, for example:

    python scripts/run_eval.py \
      --config configs/models.yaml \
      --questions data/questions.json \
      --out results/new_run \
      --variants 3 --seed 0 --temperature 0 --max_tokens 128
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import yaml
from tqdm import tqdm

# Ensure `import sycobench` works when running as a script.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sycobench.openai_compat import (  # noqa: E402
    OpenAICompatClient,
    extract_metadata,
    extract_text,
    extract_usage,
)
from sycobench.parse import is_exact_one_letter, parse_mcq_letter  # noqa: E402
from sycobench.prompts import (  # noqa: E402
    PRESSURE_TYPES,
    deterministic_wrong_letter,
    format_question_prompt,
    get_user_perturbation_message,
    make_messages_for_baseline,
    make_messages_for_followup,
)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_seed(base_seed: int, *parts: object, modulo: int = 100_000) -> int:
    """Derive a deterministic provider seed from stable string parts.

    Python's built-in `hash()` is process-randomized, so it should not be used
    for reproducible experimental seeds.
    """
    joined = "\u241f".join(str(part) for part in parts)
    digest = hashlib.sha256(joined.encode("utf-8")).digest()
    return base_seed + (int.from_bytes(digest[:8], "big") % modulo)


def load_questions(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    import re

    opt_re = re.compile(r"^\s*([ABCD])\)\s*(.*)\s*$")
    for q in data:
        assert "id" in q and "question" in q and "options" in q and "correct" in q
        if isinstance(q["options"], list):
            opts: dict[str, str] = {}
            for option in q["options"]:
                match = opt_re.match(str(option))
                assert match, f"Bad option format for {q['id']}: {option}"
                opts[match.group(1)] = match.group(2).strip()
            assert set(opts) == {"A", "B", "C", "D"}, f"Missing options for {q['id']}"
            q["options"] = opts
        else:
            assert isinstance(q["options"], dict), f"options must be list or dict for {q['id']}"
            assert set(q["options"]) == {"A", "B", "C", "D"}, f"Bad option keys for {q['id']}"
        assert q["correct"] in ["A", "B", "C", "D"], f"Bad correct letter for {q['id']}"
    return data


def call_with_retry(
    client: OpenAICompatClient,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    seed: int,
    retries: int = 3,
    backoff: float = 1.5,
    extra_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            return client.chat_completions(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                seed=seed,
                extra_body=extra_body,
            )
        except Exception as exc:  # noqa: BLE001 - preserve provider errors in retry wrapper
            last_err = exc
            time.sleep(backoff**attempt + random.random() * 0.25)
    raise RuntimeError(f"Failed after {retries} retries: {last_err}")


def parse_or_retry(
    client: OpenAICompatClient,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    seed: int,
    extra_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resp = call_with_retry(client, model, messages, temperature, max_tokens, seed, extra_body=extra_body)
    text = extract_text(resp)
    parsed = parse_mcq_letter(text)
    if parsed is not None:
        return {"resp": resp, "text": text, "parsed": parsed, "retry": False}

    retry_messages = messages + [
        {"role": "user", "content": "Format reminder: Reply with exactly one letter: A, B, C, or D."}
    ]
    resp2 = call_with_retry(
        client,
        model,
        retry_messages,
        temperature,
        max_tokens,
        seed + 1,
        extra_body=extra_body,
    )
    text2 = extract_text(resp2)
    parsed2 = parse_mcq_letter(text2)
    return {"resp": resp2, "text": text2, "parsed": parsed2, "retry": True, "first_text": text}


def response_record(
    result: dict[str, Any],
    parsed: str | None,
    correct_letter: str,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = result["text"]
    record: dict[str, Any] = {
        "response_text": text,
        "parsed": parsed,
        "correct": parsed == correct_letter,
        "usage": extract_usage(result["resp"]),
        "latency_s": result["resp"].get("_latency_s"),
        "retry": result.get("retry", False),
        "first_text": result.get("first_text"),
        "metadata": extract_metadata(result["resp"]),
        "exact_one_letter": is_exact_one_letter(text),
    }
    if extra_fields:
        record.update(extra_fields)
    return record


def run_model(
    model_cfg: dict[str, Any],
    questions: list[dict[str, Any]],
    questions_sha256: str,
    out_path: str,
    variants: int,
    limit: int | None,
    seed: int,
    temperature: float,
    max_tokens: int = 128,
) -> None:
    provider = model_cfg["provider"]
    if provider != "openai_compatible":
        raise ValueError(f"Only provider=openai_compatible is implemented. Got {provider}")

    base_url = model_cfg["base_url"]
    api_key = os.environ.get(model_cfg["api_key_env"], "")
    if not api_key:
        raise RuntimeError(f"Missing API key env var: {model_cfg['api_key_env']}")

    client = OpenAICompatClient(base_url=base_url, api_key=api_key)
    extra_body = model_cfg.get("extra_body")
    run_id = f"{model_cfg['name']}_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    items: list[dict[str, Any]] = []
    q_iter = questions[:limit] if limit else questions
    for q in tqdm(q_iter, desc=f"Running {model_cfg['name']}"):
        qid = q["id"]
        qprompt = format_question_prompt(q["question"], q["options"])
        for vid in range(variants):
            baseline_messages = make_messages_for_baseline(qprompt)
            b = parse_or_retry(
                client,
                model_cfg["name"],
                baseline_messages,
                temperature,
                max_tokens=max_tokens,
                seed=stable_seed(seed, qid, vid, "baseline"),
                extra_body=extra_body,
            )
            b_parsed = b["parsed"]
            b_correct = b_parsed == q["correct"]

            baseline_record = response_record(
                b,
                b_parsed,
                q["correct"],
                {"question_prompt": qprompt, "messages": baseline_messages},
            )

            perts: dict[str, Any] = {}
            for ptype in PRESSURE_TYPES:
                user_msg = get_user_perturbation_message(ptype, vid, q["correct"])
                follow_messages = make_messages_for_followup(
                    qprompt, baseline_record["response_text"], user_msg
                )
                r = parse_or_retry(
                    client,
                    model_cfg["name"],
                    follow_messages,
                    temperature,
                    max_tokens=max_tokens,
                    seed=stable_seed(seed, qid, vid, ptype),
                    extra_body=extra_body,
                )
                parsed = r["parsed"]
                perts[ptype] = response_record(
                    r,
                    parsed,
                    q["correct"],
                    {
                        "type": ptype,
                        "variant_id": vid,
                        "user_prompt": user_msg,
                        "messages": follow_messages,
                        "suggested_letter": (
                            deterministic_wrong_letter(q["correct"])
                            if ptype == "wrong_suggest"
                            else None
                        ),
                    },
                )

            ptype = "correct_suggest"
            user_msg = get_user_perturbation_message(ptype, vid, q["correct"])
            if b_correct:
                perts[ptype] = {
                    "type": ptype,
                    "variant_id": vid,
                    "user_prompt": user_msg,
                    "messages": None,
                    "response_text": None,
                    "parsed": None,
                    "correct": None,
                    "usage": None,
                    "latency_s": None,
                    "retry": False,
                    "first_text": None,
                    "metadata": None,
                    "exact_one_letter": None,
                    "skipped": True,
                    "suggested_letter": q["correct"],
                }
            else:
                follow_messages = make_messages_for_followup(
                    qprompt, baseline_record["response_text"], user_msg
                )
                r = parse_or_retry(
                    client,
                    model_cfg["name"],
                    follow_messages,
                    temperature,
                    max_tokens=max_tokens,
                    seed=stable_seed(seed, qid, vid, ptype),
                    extra_body=extra_body,
                )
                parsed = r["parsed"]
                perts[ptype] = response_record(
                    r,
                    parsed,
                    q["correct"],
                    {
                        "type": ptype,
                        "variant_id": vid,
                        "user_prompt": user_msg,
                        "messages": follow_messages,
                        "skipped": False,
                        "suggested_letter": q["correct"],
                    },
                )

            items.append(
                {
                    "question_id": qid,
                    "variant_id": vid,
                    "domain": q.get("domain"),
                    "difficulty": q.get("difficulty"),
                    "correct": q["correct"],
                    "baseline": baseline_record,
                    "perturbations": perts,
                }
            )

    out = {
        "schema_version": "sycobench.v2",
        "questions_sha256": questions_sha256,
        "model": model_cfg["name"],
        "provider": provider,
        "base_url": base_url,
        "model_config": model_cfg,
        "run_id": run_id,
        "n_questions": len(q_iter),
        "variants": variants,
        "seed": seed,
        "temperature": temperature,
        "items": items,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="configs/models.yaml")
    parser.add_argument("--questions", required=True, help="data/questions.json")
    parser.add_argument("--out", required=True, help="output directory for raw logs")
    parser.add_argument("--variants", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max_tokens", type=int, default=128)
    args = parser.parse_args()

    questions_sha256 = sha256_file(args.questions)
    questions = load_questions(args.questions)
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    for model_cfg in cfg["models"]:
        out_path = os.path.join(args.out, f"{model_cfg['name']}.json")
        run_model(
            model_cfg,
            questions,
            questions_sha256,
            out_path,
            args.variants,
            args.limit,
            args.seed,
            args.temperature,
            args.max_tokens,
        )


if __name__ == "__main__":
    main()
