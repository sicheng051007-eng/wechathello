from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from love_push.compose import (
    compose_card_summary,
    compose_message,
    compose_period_care_message,
    render_preview,
)
from love_push.details import detail_page_url, write_detail_site
from love_push.models import Recipient, TemplateMessage, WeatherSnapshot
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
    preview: bool = True,
    site_dir: str | Path | None = None,
    page_base_url: str = "",
    message_kind: str = "daily",
    care_style: str = "温柔关心",
    extra_words: str = "",
) -> PushSummary:
    if message_kind not in {"daily", "period-care"}:
        raise ValueError("message_kind 必须是 daily 或 period-care")

    token = ""
    if not dry_run:
        if wechat_client is None or not template_id:
            raise ValueError("实际发送需要 wechat_client 和 template_id")
        token = wechat_client.get_access_token()

    sent = failed = degraded = 0
    detail_pages: list[tuple[Recipient, TemplateMessage]] = []
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
        if message_kind == "period-care":
            message = compose_period_care_message(
                recipient,
                weather,
                care_style,
                now,
                extra_words,
            )
        else:
            message = compose_message(recipient, weather, period, now)
        detail_pages.append((recipient, message))

        if dry_run:
            if preview:
                preview_message = message
                if page_base_url:
                    preview_message = compose_card_summary(
                        recipient,
                        weather,
                        period,
                        message,
                        detail_page_url(page_base_url, recipient.id, message_kind),
                        message_kind,
                    )
                print(f"\n===== {recipient.id} / {recipient.name} =====")
                print(render_preview(preview_message))
            sent += 1
            continue

        try:
            assert wechat_client is not None
            send_message = message
            if page_base_url:
                send_message = compose_card_summary(
                    recipient,
                    weather,
                    period,
                    message,
                    detail_page_url(page_base_url, recipient.id, message_kind),
                    message_kind,
                )
            msgid = wechat_client.send_template(
                token, recipient.openid, template_id, send_message
            )
            LOGGER.info("已向 %s 发送成功，msgid=%s", recipient.id, msgid or "(无)")
            sent += 1
        except Exception as exc:
            # 一个收件人失败时继续给其他人发送，最后以非零状态退出。
            LOGGER.error("向 %s 发送失败：%s", recipient.id, exc)
            failed += 1

    if site_dir is not None:
        write_detail_site(site_dir, detail_pages, page_kind=message_kind)
        LOGGER.info("完整内容页已生成到 %s", site_dir)

    return PushSummary(sent=sent, failed=failed, degraded_weather=degraded)
