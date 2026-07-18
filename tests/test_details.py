import tempfile
import unittest
from pathlib import Path

from love_push.details import detail_page_path, detail_page_url, write_detail_site
from love_push.models import Location, Recipient, TemplateMessage


class DetailPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recipient = Recipient(
            "her",
            "<宝贝>",
            "secret-openid",
            Location("清华园 & 北京", 40, 116.3),
            "来自浙大的牵挂 💗",
        )
        self.message = TemplateMessage(
            {
                "greeting": {"value": "早安，<宝贝>", "color": "#000000"},
                "date": {"value": "2026年07月15日 · 星期三", "color": "#000000"},
                "location": {"value": "清华园 & 北京", "color": "#000000"},
                "weather": {"value": "晴朗 ☀️", "color": "#000000"},
                "temperature": {"value": "现在 26℃", "color": "#000000"},
                "activity": {"value": "适合散步", "color": "#000000"},
                "encouragement": {"value": "今天也要加油", "color": "#000000"},
                "closing": {"value": "想你 💗", "color": "#000000"},
                "source": {"value": "天气数据：Open-Meteo", "color": "#000000"},
            }
        )

    def test_page_url_uses_stable_opaque_path(self) -> None:
        path = detail_page_path("her")
        self.assertTrue(path.startswith("message-"))
        self.assertNotIn("her", path)
        self.assertEqual(
            detail_page_url("https://example.com/base/", "her"),
            f"https://example.com/base/{path}",
        )

    def test_site_contains_full_content_but_not_openid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            write_detail_site(directory, [(self.recipient, self.message)])
            page = (
                Path(directory) / detail_page_path(self.recipient.id) / "index.html"
            ).read_text(encoding="utf-8")
            self.assertIn("今天也要加油", page)
            self.assertIn("清华园 &amp; 北京", page)
            self.assertNotIn("secret-openid", page)
            self.assertIn('name="robots" content="noindex,nofollow,noarchive"', page)

    def test_period_care_has_distinct_path_and_loving_layout(self) -> None:
        daily_path = detail_page_path(self.recipient.id)
        care_path = detail_page_path(self.recipient.id, "period-care")
        self.assertNotEqual(daily_path, care_path)
        self.assertNotIn(self.recipient.id, care_path)

        with tempfile.TemporaryDirectory() as directory:
            write_detail_site(
                directory,
                [(self.recipient, self.message)],
                page_kind="period-care",
            )
            page = (Path(directory) / care_path / "index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn("今天不用逞强，你只需要被好好爱着", page)
            self.assertIn("把我的拥抱放在这里", page)
            self.assertIn("不用急着回复，舒服一点更重要", page)
            self.assertNotIn("secret-openid", page)


if __name__ == "__main__":
    unittest.main()
