import unittest
from datetime import datetime

from love_push.compose import compose_message, render_preview
from love_push.models import Location, Recipient, WeatherSnapshot


class ComposeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recipient = Recipient(
            "her", "宝贝", "openid", Location("清华园 · 北京", 40, 116.3), "想你 ♥"
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

    def test_weather_failure_still_renders_complete_message(self) -> None:
        message = compose_message(self.recipient, None, "evening", self.now)
        preview = render_preview(message)
        self.assertIn("天气暂时走丢了", preview)
        self.assertIn("想你", preview)

    def test_template_values_do_not_contain_four_byte_emoji(self) -> None:
        message = compose_message(self.recipient, self.weather, "morning", self.now)
        values = [field["value"] for field in message.fields.values()]
        self.assertFalse(any(ord(char) > 0xFFFF for value in values for char in value))

    def test_message_contains_android_compatible_symbols(self) -> None:
        message = compose_message(self.recipient, self.weather, "morning", self.now)
        values = " ".join(field["value"] for field in message.fields.values())
        self.assertIn("☀", values)
        self.assertIn("♥", values)


if __name__ == "__main__":
    unittest.main()
