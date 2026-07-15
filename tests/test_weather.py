import unittest

from love_push.models import Location, WeatherSnapshot
from love_push.weather import (
    OpenMeteoWeather,
    WeatherDataError,
    activity_suggestion,
    activity_suggestions,
)


class FakeHttp:
    def __init__(self, payload):
        self.payload = payload
        self.params = None

    def get_json(self, url, params):
        self.params = params
        return self.payload


class WeatherTests(unittest.TestCase):
    def test_parses_open_meteo_response(self) -> None:
        http = FakeHttp(
            {
                "current": {
                    "temperature_2m": 26.3,
                    "apparent_temperature": 27.1,
                    "relative_humidity_2m": 71,
                    "weather_code": 1,
                    "wind_speed_10m": 8.2,
                },
                "daily": {
                    "weather_code": [1],
                    "temperature_2m_max": [31.2],
                    "temperature_2m_min": [23.4],
                    "precipitation_probability_max": [20],
                    "uv_index_max": [7.1],
                },
            }
        )
        result = OpenMeteoWeather(http).fetch(Location("清华园", 40, 116.3))
        self.assertEqual(result.weather_code, 1)
        self.assertEqual(result.humidity, 71)
        self.assertEqual(result.temperature_max, 31.2)
        self.assertEqual(http.params["timezone"], "Asia/Shanghai")

    def test_rejects_incomplete_response(self) -> None:
        with self.assertRaises(WeatherDataError):
            OpenMeteoWeather(FakeHttp({"current": {}, "daily": {}})).fetch(
                Location("清华园", 40, 116.3)
            )

    def test_rain_has_priority_in_activity_suggestion(self) -> None:
        weather = WeatherSnapshot(63, 30, 33, 80, 5, 25, 36, 90, 9)
        self.assertIn("伞", activity_suggestion(weather, "morning"))

    def test_evening_fair_weather_suggests_walk(self) -> None:
        weather = WeatherSnapshot(1, 22, 22, 50, 5, 18, 26, 5, 3)
        self.assertIn("走一走", activity_suggestion(weather, "evening"))

    def test_evening_heat_advice_does_not_mention_afternoon(self) -> None:
        weather = WeatherSnapshot(1, 34, 40, 60, 5, 29, 37, 10, 9)
        advice = activity_suggestion(weather, "evening")
        self.assertIn("高温辛苦了", advice)
        self.assertNotIn("午后", advice)

    def test_each_common_weather_period_has_multiple_activity_options(self) -> None:
        fair = WeatherSnapshot(1, 22, 22, 50, 5, 18, 26, 5, 3)
        rainy = WeatherSnapshot(63, 20, 20, 80, 5, 18, 22, 90, 2)
        for weather in (fair, rainy):
            for period in ("morning", "evening"):
                options = activity_suggestions(weather, period)
                self.assertGreaterEqual(len(options), 4)
                self.assertEqual(len(options), len(set(options)))


if __name__ == "__main__":
    unittest.main()
