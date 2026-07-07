from __future__ import annotations

import os
from pathlib import Path

from inspect_ai import eval as inspect_eval

from sycobench.inspect_task import sycobench_600


def main() -> None:
    model = os.environ.get("INSPECT_EVAL_MODEL")
    if not model:
        raise SystemExit("Set INSPECT_EVAL_MODEL to run the live Inspect API smoke test.")

    log_dir = Path("build") / "inspect_api_smoke"
    logs = inspect_eval(
        sycobench_600,
        model=model,
        task_args={"limit": 1, "variants": 1},
        log_dir=str(log_dir),
        display="plain",
        max_connections=1,
        temperature=0,
        log_samples=True,
    )
    if not logs or not logs[0].samples:
        raise SystemExit("Inspect API smoke test produced no samples.")

    sample = logs[0].samples[0]
    scores = sample.scores or {}
    if "sycobench_protocol_scorer" not in scores:
        raise SystemExit("Inspect API smoke test did not produce the SycoBench score.")

    print(f"wrote Inspect API smoke log to {log_dir}")
    print(f"sample_id={sample.id} score={scores['sycobench_protocol_scorer'].value}")


if __name__ == "__main__":
    main()
