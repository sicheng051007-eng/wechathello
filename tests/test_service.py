import io
import unittest
from contextlib import redirect_stdout
from datetime import datetime

from love_push.details import detail_page_path
from love_push.models import Location, Recipient, WeatherSnapshot
from love_push.service import run_push


class BrokenWeather:
    def fetch(self, location):
        raise RuntimeError("weather service unavailable")


class FineWeather:
    def fetch(self, location):
        return WeatherSnapshot(1, 26.3, 27.1, 71, 8.2, 23.4, 31.2, 20, 7.1)


class FakeWeChat:
    def __init__(self):
        self.message = None

    def get_access_token(self):
        return "token"

    def send_template(self, token, openid, template_id, message):
        self.message = message
        return "42"


class ServiceTests(unittest.TestCase):
    def test_weather_failure_degrades_but_does_not_stop_push(self) -> None:
        recipients = [
            Recipient(
                "her",
                "宝贝",
                "preview:her",
                Location("清华园", 40, 116.3),
                "想你",
            )
        ]
        output = io.StringIO()
        with redirect_stdout(output):
            summary = run_push(
                recipients,
                "morning",
                datetime(2026, 7, 15, 8, 5),
                BrokenWeather(),
                dry_run=True,
            )
        self.assertEqual(summary.sent, 1)
        self.assertEqual(summary.degraded_weather, 1)
        self.assertIn("天气暂时走丢了", output.getvalue())

    def test_real_send_uses_summary_and_detail_link(self) -> None:
        recipient = Recipient(
            "her",
            "宝贝",
            "openid",
            Location("清华园", 40, 116.3),
            "来自浙大的牵挂 💗",
        )
        wechat = FakeWeChat()
        summary = run_push(
            [recipient],
            "morning",
            datetime(2026, 7, 15, 8, 5),
            FineWeather(),
            wechat_client=wechat,
            template_id="template",
            page_base_url="https://example.com/wechathello/",
        )
        self.assertEqual(summary.sent, 1)
        self.assertIsNotNone(wechat.message)
        self.assertTrue(wechat.message.url.startswith("https://example.com/wechathello/message-"))
        self.assertLessEqual(len(wechat.message.fields["encouragement"]["value"]), 18)

    def test_period_care_uses_its_own_page_and_personal_words(self) -> None:
        recipient = Recipient(
            "her",
            "宝贝",
            "openid",
            Location("清华园", 40, 116.3),
            "来自浙大的牵挂 💗",
        )
        wechat = FakeWeChat()
        summary = run_push(
            [recipient],
            "morning",
            datetime(2026, 7, 15, 8, 5),
            FineWeather(),
            wechat_client=wechat,
            template_id="template",
            page_base_url="https://example.com/wechathello/",
            message_kind="period-care",
            care_style="很难受想休息",
            extra_words="乖乖休息，晚点给你打电话",
        )
        self.assertEqual(summary.sent, 1)
        self.assertIsNotNone(wechat.message)
        self.assertNotEqual(
            wechat.message.url,
            "https://example.com/wechathello/"
            + detail_page_path("her"),
        )
        self.assertEqual(
            wechat.message.url,
            "https://example.com/wechathello/"
            + detail_page_path("her", "period-care"),
        )
        self.assertTrue(
            wechat.message.fields["encouragement"]["value"].startswith("乖乖休息")
        )


if __name__ == "__main__":
    unittest.main()
