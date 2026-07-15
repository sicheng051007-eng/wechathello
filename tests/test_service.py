import io
import unittest
from contextlib import redirect_stdout
from datetime import datetime

from love_push.models import Location, Recipient
from love_push.service import run_push


class BrokenWeather:
    def fetch(self, location):
        raise RuntimeError("weather service unavailable")


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


if __name__ == "__main__":
    unittest.main()
