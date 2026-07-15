from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from love_push.http import JsonHttpClient
from love_push.models import TemplateMessage


TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send"


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
        response = self.http.post_json(target, message.as_payload(openid, template_id))
        if response.get("errcode") != 0:
            raise WeChatApiError("发送模板消息", response)
        return str(response.get("msgid", ""))

