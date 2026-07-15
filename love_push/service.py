from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from love_push.compose import compose_message, render_preview
from love_push.models import Recipient, WeatherSnapshot
from love_push.weather import OpenMeteoWeather
from love_push.wechat import WeChatClient


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PushSummary:
    sent: int
    failed: int
    degraded_weather: int


def run_push(
    recipients: list[Recipient],
    period: str,
    now: datetime,
    weather_client: OpenMeteoWeather,
    *,
    wechat_client: WeChatClient | None = None,
    template_id: str = "",
    dry_run: bool = False,
) -> PushSummary:
    token = ""
    if not dry_run:
        if wechat_client is None or not template_id:
            raise ValueError("实际发送需要 wechat_client 和 template_id")
        token = wechat_client.get_access_token()

    sent = failed = degraded = 0
    weather_cache: dict[tuple[float, float, str], WeatherSnapshot | None] = {}
    for recipient in recipients:
        cache_key = (
            recipient.location.latitude,
            recipient.location.longitude,
            recipient.location.timezone,
        )
        if cache_key not in weather_cache:
            try:
                weather_cache[cache_key] = weather_client.fetch(recipient.location)
            except Exception as exc:  # 天气失败不应阻断问候推送
                LOGGER.warning("%s 的天气获取失败，将发送降级消息：%s", recipient.location.name, exc)
                weather_cache[cache_key] = None
        weather = weather_cache[cache_key]
        if weather is None:
            degraded += 1
        message = compose_message(recipient, weather, period, now)

        if dry_run:
            print(f"\n===== {recipient.id} / {recipient.name} =====")
            print(render_preview(message))
            sent += 1
            continue

        try:
            assert wechat_client is not None
            msgid = wechat_client.send_template(
                token, recipient.openid, template_id, message
            )
            LOGGER.info("已向 %s 发送成功，msgid=%s", recipient.id, msgid or "(无)")
            sent += 1
        except Exception as exc:
            # 一个收件人失败时继续给其他人发送，最后以非零状态退出。
            LOGGER.error("向 %s 发送失败：%s", recipient.id, exc)
            failed += 1

    return PushSummary(sent=sent, failed=failed, degraded_weather=degraded)

