import unittest
from datetime import datetime

from love_push.compose import (
    CARE_ACTIVITIES,
    CARE_STYLES,
    CARE_WORDS,
    EVENING_WORDS,
    MORNING_WORDS,
    compose_card_summary,
    compose_message,
    compose_period_care_message,
    render_preview,
)
from love_push.models import Location, Recipient, WeatherSnapshot


class ComposeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recipient = Recipient(
            "her", "宝贝", "openid", Location("清华园 · 北京", 40, 116.3), "想你 💗"
        )
        self.weather = WeatherSnapshot(1, 26.3, 27.1, 71, 8.2, 23.4, 31.2, 20, 7.1)
        self.now = datetime(2026, 7, 15, 8, 5)

    def test_message_matches_template_fields(self) -> None:
        message = compose_message(self.recipient, self.weather, "morning", self.now)
        self.assertEqual(
            set(message.fields),
            {
                "greeting",
                "date",
                "location",
                "weather",
                "temperature",
                "activity",
                "encouragement",
                "closing",
                "source",
            },
        )
        self.assertIn("星期三", message.fields["date"]["value"])
        self.assertIn("26.3℃", message.fields["temperature"]["value"])

    def test_daily_word_is_deterministic(self) -> None:
        first = compose_message(self.recipient, self.weather, "morning", self.now)
        second = compose_message(self.recipient, self.weather, "morning", self.now)
        self.assertEqual(first.fields["encouragement"], second.fields["encouragement"])

    def test_has_a_month_of_morning_and_evening_words(self) -> None:
        self.assertGreaterEqual(len(MORNING_WORDS), 30)
        self.assertGreaterEqual(len(EVENING_WORDS), 30)
        self.assertEqual(len(MORNING_WORDS), len(set(MORNING_WORDS)))
        self.assertEqual(len(EVENING_WORDS), len(set(EVENING_WORDS)))

    def test_daily_activity_is_deterministic(self) -> None:
        first = compose_message(self.recipient, self.weather, "morning", self.now)
        second = compose_message(self.recipient, self.weather, "morning", self.now)
        self.assertEqual(first.fields["activity"], second.fields["activity"])

    def test_weather_failure_still_renders_complete_message(self) -> None:
        message = compose_message(self.recipient, None, "evening", self.now)
        preview = render_preview(message)
        self.assertIn("天气暂时走丢了", preview)
        self.assertIn("想你", preview)

    def test_preview_uses_replacement_location_and_weather_emoji(self) -> None:
        message = compose_message(self.recipient, self.weather, "morning", self.now)
        preview = render_preview(message)
        self.assertIn("🌏 清华园 · 北京", preview)
        self.assertIn("☁️ 大致晴朗", preview)
        self.assertNotIn("📍", preview)
        self.assertNotIn("🏫", preview)
        self.assertNotIn("🌤️ 大致晴朗", preview)

    def test_card_summary_is_short_and_links_to_full_page(self) -> None:
        full = compose_message(self.recipient, self.weather, "morning", self.now)
        summary = compose_card_summary(
            self.recipient,
            self.weather,
            "morning",
            full,
            "https://example.com/message/",
        )
        self.assertEqual(summary.url, "https://example.com/message/")
        self.assertIn("26℃", summary.fields["weather"]["value"])
        self.assertLessEqual(len(summary.fields["activity"]["value"]), 16)
        self.assertLessEqual(len(summary.fields["encouragement"]["value"]), 18)
        self.assertLessEqual(len(summary.fields["closing"]["value"]), 16)
        self.assertNotIn("…", "".join(item["value"] for item in summary.fields.values()))

    def test_period_care_has_three_styles_and_varied_words(self) -> None:
        self.assertEqual(
            CARE_STYLES,
            ("温柔关心", "有些不舒服", "很难受想休息"),
        )
        for style in CARE_STYLES:
            self.assertGreaterEqual(len(CARE_ACTIVITIES[style]), 6)
            self.assertGreaterEqual(len(CARE_WORDS[style]), 6)

    def test_period_care_prioritizes_personal_words_in_card(self) -> None:
        full = compose_period_care_message(
            self.recipient,
            self.weather,
            "有些不舒服",
            self.now,
            "  今天下课后给我打电话，我想陪陪你！  ",
        )
        self.assertIn(
            "今天下课后给我打电话，我想陪陪你",
            full.fields["encouragement"]["value"],
        )
        summary = compose_card_summary(
            self.recipient,
            self.weather,
            "morning",
            full,
            "https://example.com/care/",
            "period-care",
        )
        self.assertEqual(
            summary.fields["greeting"]["value"],
            "宝贝，今天慢一点，我一直都在 💗",
        )
        self.assertTrue(
            summary.fields["encouragement"]["value"].startswith("今天下课后")
        )
        self.assertLessEqual(len(summary.fields["encouragement"]["value"]), 18)

    def test_period_care_rejects_unknown_style(self) -> None:
        with self.assertRaises(ValueError):
            compose_period_care_message(
                self.recipient,
                self.weather,
                "未知状态",
                self.now,
            )


if __name__ == "__main__":
    unittest.main()
