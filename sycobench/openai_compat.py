from __future__ import annotations

import time
from typing import Any

import requests


class OpenAICompatClient:
    """Minimal OpenAI-compatible Chat Completions client.

    Works with OpenAI and gateways such as OpenRouter, Together-compatible
    endpoints, vLLM, and other services that expose `/v1/chat/completions`.
    """

    def __init__(self, base_url: str, api_key: str, timeout_s: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_s = timeout_s

    def chat_completions(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 16,
        top_p: float = 1.0,
        seed: int | None = None,
        extra_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }
        if extra_body:
            payload.update(extra_body)

        def _post(request_payload: dict[str, Any]) -> dict[str, Any]:
            t0 = time.time()
            response = requests.post(
                url,
                headers=headers,
                json=request_payload,
                timeout=self.timeout_s,
            )
            latency = time.time() - t0
            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
            data = response.json()
            data["_latency_s"] = latency
            return data

        # Some gateways reject unknown fields like `seed`. Try with seed first,
        # then retry without it only when the error indicates unsupported fields.
        if seed is not None:
            payload_with_seed = dict(payload)
            payload_with_seed["seed"] = seed
            try:
                return _post(payload_with_seed)
            except RuntimeError as exc:
                message = str(exc).lower()
                if "seed" in message or "unknown" in message or "unrecognized" in message:
                    return _post(payload)
                raise
        return _post(payload)


def extract_text(resp: dict[str, Any]) -> str:
    """Extract assistant text from an OpenAI-compatible response."""
    try:
        return resp["choices"][0]["message"]["content"] or ""
    except Exception:
        return ""


def extract_usage(resp: dict[str, Any]) -> dict[str, Any]:
    return resp.get("usage", {}) or {}


def extract_metadata(resp: dict[str, Any]) -> dict[str, Any]:
    """Extract non-secret response metadata for audit logs."""
    keys = [
        "id",
        "object",
        "created",
        "model",
        "system_fingerprint",
        "service_tier",
        "provider",
    ]
    return {key: resp.get(key) for key in keys if key in resp}
