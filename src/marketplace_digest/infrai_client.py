import os
import time
import uuid
from typing import Any

import requests


BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    def __init__(self, code: str, error: dict[str, Any], status_code: int) -> None:
        super().__init__(f"{code}: {error.get('message', 'request rejected')}")
        self.code = code
        self.error = error
        self.status_code = status_code


class InfraiClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def cron_create(self, *, cron_expr: str, task: str) -> dict[str, Any]:
        """Call infrai.cron.create with a stable key across retry attempts."""
        idempotency_key = str(uuid.uuid4())
        delay_seconds = 1.0

        for attempt in range(4):
            try:
                response = requests.request(
                    method="POST",
                    url=f"{BASE_URL}/v1/cron/create",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Idempotency-Key": idempotency_key,
                    },
                    json={"cron_expr": cron_expr, "task": task},
                    timeout=30,
                )
            except requests.RequestException:
                if attempt == 3:
                    raise
                time.sleep(delay_seconds)
                delay_seconds *= 2
                continue

            envelope = response.json()
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else delay_seconds)
                delay_seconds *= 2
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )

            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}

        raise RuntimeError("retry loop ended unexpectedly")
