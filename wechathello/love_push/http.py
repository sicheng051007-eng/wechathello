from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class HttpRequestError(RuntimeError):
    """远端接口请求失败。"""


class JsonHttpClient:
    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    def get_json(
        self,
        url: str,
        params: dict[str, str | int | float] | None = None,
        *,
        retries: int = 2,
    ) -> dict[str, Any]:
        target = f"{url}?{urlencode(params)}" if params else url
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                return self._request_json(Request(target, method="GET"))
            except HttpRequestError as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(0.5 * (2**attempt))
        raise HttpRequestError(f"GET 请求在重试后仍失败：{last_error}")

    def post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        # 消息发送不自动重试：响应丢失时重试可能造成重复推送。
        return self._request_json(request)

    def _request_json(self, request: Request) -> dict[str, Any]:
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise HttpRequestError(f"HTTP {exc.code}: {detail[:300]}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise HttpRequestError(str(exc)) from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HttpRequestError("远端接口返回了无效 JSON") from exc
        if not isinstance(data, dict):
            raise HttpRequestError("远端接口 JSON 顶层不是对象")
        return data

