from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from love_push.config import (
    ConfigurationError,
    load_recipients,
    load_wechat_credentials,
)
from love_push.service import run_push
from love_push.weather import OpenMeteoWeather
from love_push.wechat import WeChatClient


DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "recipients.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="清浙小报微信天气推送")
    parser.add_argument(
        "--period",
        choices=("auto", "morning", "evening"),
        default="auto",
        help="消息时段；auto 按北京时间判断",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="收件人 JSON 配置")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只预览，不读取微信凭据，也不发送",
    )
    parser.add_argument(
        "--site-dir",
        help="把完整消息生成成静态网页到指定目录",
    )
    parser.add_argument(
        "--site-only",
        action="store_true",
        help="只生成完整内容页，不发送也不在日志打印消息",
    )
    parser.add_argument(
        "--page-base-url",
        default="",
        help="完整内容页的公开根地址；设置后发送精简卡片并附带跳转链接",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    if args.site_only and not args.site_dir:
        logging.error("--site-only 必须同时提供 --site-dir")
        return 2
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    period = _resolve_period(args.period, now)
    no_send = args.dry_run or args.site_only

    try:
        recipients, skipped = load_recipients(
            args.config, include_unconfigured=no_send
        )
        if skipped:
            logging.info("未配置 OpenID，已跳过：%s", ", ".join(skipped))

        wechat_client = None
        template_id = ""
        if not no_send:
            app_id, app_secret, template_id = load_wechat_credentials()
            wechat_client = WeChatClient(app_id, app_secret)

        summary = run_push(
            recipients,
            period,
            now,
            OpenMeteoWeather(),
            wechat_client=wechat_client,
            template_id=template_id,
            dry_run=no_send,
            preview=not args.site_only,
            site_dir=args.site_dir,
            page_base_url=args.page_base_url,
        )
    except (ConfigurationError, ValueError) as exc:
        logging.error("配置错误：%s", exc)
        return 2
    except Exception as exc:
        logging.exception("推送任务未能完成：%s", exc)
        return 1

    logging.info(
        "任务完成：成功 %d，失败 %d，天气降级 %d",
        summary.sent,
        summary.failed,
        summary.degraded_weather,
    )
    return 1 if summary.failed else 0


def _resolve_period(value: str, now: datetime) -> str:
    if value != "auto":
        return value
    return "morning" if now.hour < 13 else "evening"
