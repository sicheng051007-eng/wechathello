import unittest

from love_push.models import TemplateMessage
from love_push.wechat import WeChatApiError, WeChatClient


class FakeHttp:
    def __init__(self, get_response=None, post_response=None):
        self.get_response = get_response or {}
        self.post_response = post_response or {}
        self.posted = None

    def get_json(self, url, params):
        return self.get_response

    def post_json(self, url, payload):
        self.posted = payload
        return self.post_response


class WeChatTests(unittest.TestCase):
    def test_get_access_token(self) -> None:
        client = WeChatClient("app", "secret", FakeHttp({"access_token": "token"}))
        self.assertEqual(client.get_access_token(), "token")

    def test_send_template(self) -> None:
        http = FakeHttp(post_response={"errcode": 0, "errmsg": "ok", "msgid": 42})
        client = WeChatClient("app", "secret", http)
        message = TemplateMessage({"greeting": {"value": "早安", "color": "#000000"}})
        msgid = client.send_template("token", "openid", "template", message)
        self.assertEqual(msgid, "42")
        self.assertEqual(http.posted["touser"], "openid")

    def test_send_template_preserves_color_emoji(self) -> None:
        http = FakeHttp(post_response={"errcode": 0, "errmsg": "ok", "msgid": 42})
        client = WeChatClient("app", "secret", http)
        message = TemplateMessage(
            {"greeting": {"value": "早安 ☀️ 加油 💗", "color": "#000000"}}
        )
        client.send_template("token", "openid", "template", message)
        self.assertEqual(http.posted["data"]["greeting"]["value"], "早安 ☀️ 加油 💗")

    def test_send_template_includes_detail_url(self) -> None:
        http = FakeHttp(post_response={"errcode": 0, "errmsg": "ok", "msgid": 42})
        client = WeChatClient("app", "secret", http)
        message = TemplateMessage(
            {"greeting": {"value": "早安", "color": "#000000"}},
            url="https://example.com/message/",
        )
        client.send_template("token", "openid", "template", message)
        self.assertEqual(http.posted["url"], "https://example.com/message/")

    def test_api_error_is_exposed(self) -> None:
        client = WeChatClient(
            "app", "secret", FakeHttp(post_response={"errcode": 40003, "errmsg": "bad openid"})
        )
        with self.assertRaises(WeChatApiError):
            client.send_template(
                "token", "bad", "template", TemplateMessage({})
            )


if __name__ == "__main__":
    unittest.main()
