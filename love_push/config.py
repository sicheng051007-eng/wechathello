from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Mapping

from love_push.models import Location, Recipient


class ConfigurationError(ValueError):
    """项目配置不完整或格式错误。"""


def load_recipients(
    path: str | Path,
    environ: Mapping[str, str] | None = None,
    *,
    include_unconfigured: bool = False,
) -> tuple[list[Recipient], list[str]]:
    env = os.environ if environ is None else environ
    config_path = Path(path)
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationError(f"找不到收件人配置：{config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"收件人配置不是有效 JSON：{exc}") from exc

    items = payload.get("recipients") if isinstance(payload, dict) else None
    if not isinstance(items, list) or not items:
        raise ConfigurationError("配置中的 recipients 必须是非空数组")

    recipients: list[Recipient] = []
    skipped: list[str] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ConfigurationError(f"recipients[{index}] 必须是对象")
        recipient_id = _required_string(item, "id", index)
        if recipient_id in seen_ids:
            raise ConfigurationError(f"收件人 id 重复：{recipient_id}")
        seen_ids.add(recipient_id)

        openid_env = _required_string(item, "openid_env", index)
        openid = env.get(openid_env, "").strip()
        if not openid and not include_unconfigured:
            skipped.append(recipient_id)
            continue
        if not openid:
            openid = f"preview:{recipient_id}"

        location_data = item.get("location")
        if not isinstance(location_data, dict):
            raise ConfigurationError(f"recipients[{index}].location 必须是对象")
        latitude = _number(location_data, "latitude", index)
        longitude = _number(location_data, "longitude", index)
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ConfigurationError(f"recipients[{index}] 的经纬度超出合法范围")

        recipients.append(
            Recipient(
                id=recipient_id,
                name=_required_string(item, "name", index),
                openid=openid,
                location=Location(
                    name=_required_string(location_data, "name", index),
                    latitude=latitude,
                    longitude=longitude,
                    timezone=str(location_data.get("timezone", "Asia/Shanghai")).strip()
                    or "Asia/Shanghai",
                ),
                signoff=str(item.get("signoff", "隔着山海，也一直惦记你 ♥")).strip(),
            )
        )

    if not recipients:
        env_names = ", ".join(
            str(item.get("openid_env", "")) for item in items if isinstance(item, dict)
        )
        raise ConfigurationError(
            "没有可发送的收件人。请至少设置一个 OpenID 环境变量：" + env_names
        )
    return recipients, skipped


def load_wechat_credentials(environ: Mapping[str, str] | None = None) -> tuple[str, str, str]:
    env = os.environ if environ is None else environ
    names = ("WECHAT_APP_ID", "WECHAT_APP_SECRET", "WECHAT_TEMPLATE_ID")
    values = tuple(env.get(name, "").strip() for name in names)
    missing = [name for name, value in zip(names, values) if not value]
    if missing:
        raise ConfigurationError("缺少微信环境变量：" + ", ".join(missing))
    return values  # type: ignore[return-value]


def _required_string(data: dict[object, object], key: str, index: int) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"recipients[{index}].{key} 必须是非空字符串")
    return value.strip()


def _number(data: dict[object, object], key: str, index: int) -> float:
    value = data.get(key)
    if isinstance(value, bool):
        raise ConfigurationError(f"recipients[{index}].location.{key} 必须是数字")
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"recipients[{index}].location.{key} 必须是数字") from exc
    if not math.isfinite(number):
        raise ConfigurationError(f"recipients[{index}].location.{key} 必须是有限数字")
    return number
