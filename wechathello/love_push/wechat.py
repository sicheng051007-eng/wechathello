from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlencode

from love_push.http import JsonHttpClient
from love_push.models import TemplateMessage


TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send"

# 微信模板消息中的彩色 Emoji 在部分安卓客户端会显示为方框。发送前先把常用
# Emoji 降级成两端都更容易显示的基础 Unicode 图案，再移除无法安全降级的字符。
EMOJI_FALLBACKS = (
    ("❤️", "♥"),
    ("❤", "♥"),
    ("💗", "♥"),
    ("💕", "♥"),
    ("💖", "♥"),
    ("💓", "♥"),
    ("💞", "♥"),
    ("☀️", "☀"),
    ("🌞", "☀"),
    ("🌤️", "☀"),
    ("🌧️", "☂"),
    ("☔", "☂"),
    ("🌙", "☾"),
    ("😊", "☺"),
    ("🙂", "☺"),
    ("✨", "★"),
    ("⭐", "★"),
    ("❄️", "❄"),
    ("⚡️", "⚡"),
    ("💪", "加油"),
)
UNSUPPORTED_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001FAFF"
    "\uFE0E\uFE0F\u200D"
    "]+"
)


class WeChatApiError(RuntimeError):
    def __init__(self, action: str, response: dict[str, Any]) -> None:
        self.errcode = response.get("errcode")
        self.errmsg = response.get("errmsg", "未知错误")
        super().__init__(f"微信{action}失败（{self.errcode}）：{self.errmsg}")


class WeChatClient:
    def __init__(self, app_id: str, app_secret: str, http: JsonHttpClient | None = None) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.http = http or JsonHttpClient()

    def get_access_token(self) -> str:
        response = self.http.get_json(
            TOKEN_URL,
            {
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.app_secret,
            },
        )
        token = response.get("access_token")
        if not isinstance(token, str) or not token:
            raise WeChatApiError("获取 access_token", response)
        return token

    def send_template(
        self,
        access_token: str,
        openid: str,
        template_id: str,
        message: TemplateMessage,
    ) -> str:
        target = f"{SEND_URL}?{urlencode({'access_token': access_token})}"
        payload = message.as_payload(openid, template_id)
        for field in payload["data"].values():
            value = field.get("value")
            if isinstance(value, str):
                field["value"] = sanitize_wechat_text(value)
        response = self.http.post_json(target, payload)
        if response.get("errcode") != 0:
            raise WeChatApiError("发送模板消息", response)
        return str(response.get("msgid", ""))


def sanitize_wechat_text(value: str) -> str:
    """将彩色 Emoji 降级成安卓兼容图案，并清理无法兼容的字符。"""
    for emoji, fallback in EMOJI_FALLBACKS:
        value = value.replace(emoji, fallback)
    return " ".join(UNSUPPORTED_EMOJI_PATTERN.sub("", value).split())

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlencode

from love_push.http import JsonHttpClient
from love_push.models import TemplateMessage


TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send"

# 微信模板消息会过滤 Emoji，部分安卓客户端会显示为方框。发送前统一移除，
# 同时覆盖用户以后在自定义称呼或落款中误加 Emoji 的情况。
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001FAFF"
    "\u2600-\u27BF"
    "\uFE0E\uFE0F\u200D"
    "]+"
)


class WeChatApiError(RuntimeError):
    def __init__(self, action: str, response: dict[str, Any]) -> None:
        self.errcode = response.get("errcode")
        self.errmsg = response.get("errmsg", "未知错误")
        super().__init__(f"微信{action}失败（{self.errcode}）：{self.errmsg}")


class WeChatClient:
    def __init__(self, app_id: str, app_secret: str, http: JsonHttpClient | None = None) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.http = http or JsonHttpClient()

    def get_access_token(self) -> str:
        response = self.http.get_json(
            TOKEN_URL,
            {
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.app_secret,
            },
        )
        token = response.get("access_token")
        if not isinstance(token, str) or not token:
            raise WeChatApiError("获取 access_token", response)
        return token

    def send_template(
        self,
        access_token: str,
        openid: str,
        template_id: str,
        message: TemplateMessage,
    ) -> str:
        target = f"{SEND_URL}?{urlencode({'access_token': access_token})}"
        payload = message.as_payload(openid, template_id)
        for field in payload["data"].values():
            value = field.get("value")
            if isinstance(value, str):
                field["value"] = sanitize_wechat_text(value)
        response = self.http.post_json(target, payload)
        if response.get("errcode") != 0:
            raise WeChatApiError("发送模板消息", response)
        return str(response.get("msgid", ""))


def sanitize_wechat_text(value: str) -> str:
    """移除模板消息不支持的 Emoji，并清理多余空白。"""
    return " ".join(EMOJI_PATTERN.sub("", value).split())
