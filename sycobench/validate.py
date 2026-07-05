from __future__ import annotations

import hashlib
from typing import Any

PRESSURE_TYPES = ["doubt", "authority", "wrong_suggest"]
ALL_TYPES = ["doubt", "authority", "wrong_suggest", "correct_suggest"]


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def validate_model_log(model_data: dict[str, Any], question_ids: list[str]) -> list[str]:
    errors = []
    # Check coverage
    seen = set(it["question_id"] for it in model_data["items"])
    missing = [q for q in question_ids if q not in seen]
    if missing:
        errors.append(
            f"Missing {len(missing)} question_ids: {missing[:10]}{'...' if len(missing) > 10 else ''}"
        )

    # Check each item schema
    for it in model_data["items"]:
        qid = it["question_id"]
        # baseline parse must exist
        if "baseline" not in it or "parsed" not in it["baseline"]:
            errors.append(f"{qid}: baseline missing parsed")
            continue
        # perturbations dict must have all keys
        perts = it.get("perturbations", {})
        for p in ALL_TYPES:
            if p not in perts:
                errors.append(f"{qid}: missing perturbation {p}")
                continue
            rec = perts[p]
            if p == "correct_suggest":
                # After reparsing, baseline correctness may have changed.
                # Accept _missing_data flag for items where the old parser
                # said baseline was correct (so correct_suggest was skipped
                # at runtime) but the new parser says baseline is wrong.
                if it["baseline"]["correct"] and not rec.get("skipped", False):
                    errors.append(f"{qid}: correct_suggest should be skipped when baseline correct")
                if (
                    (not it["baseline"]["correct"])
                    and rec.get("skipped", False)
                    and not rec.get("_missing_data", False)
                ):
                    errors.append(f"{qid}: correct_suggest is skipped but baseline is wrong")
        # wrong_suggest should not suggest correct letter
        ws = perts.get("wrong_suggest", {})
        if "suggested_letter" in ws and ws["suggested_letter"] == it["correct"]:
            errors.append(f"{qid}: wrong_suggest suggested correct letter {it['correct']}")
        cs = perts.get("correct_suggest", {})
        if (
            (not it["baseline"]["correct"])
            and ("suggested_letter" in cs)
            and cs["suggested_letter"] != it["correct"]
        ):
            errors.append(
                f"{qid}: correct_suggest suggested {cs.get('suggested_letter')} but correct is {it['correct']}"
            )

    return errors


def validate_prompt_identity(all_models: dict[str, dict[str, Any]]) -> list[str]:
    """
    For each (question_id, variant_id, perturbation_type), the *user perturbation message* should be identical across models.
    Baseline assistant answer will differ; that's OK.
    """
    errors = []
    # build map: key -> set(prompt_text)
    mp = {}
    for _model_name, md in all_models.items():
        for it in md["items"]:
            qid = it["question_id"]
            vid = it["variant_id"]
            # baseline prompt
            bprompt = it["baseline"]["question_prompt"]
            mp.setdefault((qid, vid, "baseline"), set()).add(bprompt)
            # perturbation user prompts
            for ptype, rec in it["perturbations"].items():
                up = rec.get("user_prompt", "")
                mp.setdefault((qid, vid, ptype), set()).add(up)
    # check all sets size 1
    for key, s in mp.items():
        if len(s) > 1:
            qid, vid, ptype = key
            errors.append(
                f"Prompt mismatch for (qid={qid}, variant={vid}, type={ptype}): {len(s)} distinct prompts"
            )
    return errors
