from __future__ import annotations

from typing import Any

from love_push.http import JsonHttpClient
from love_push.models import Location, WeatherSnapshot


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherDataError(RuntimeError):
    """天气数据缺失或格式异常。"""


class OpenMeteoWeather:
    def __init__(self, http: JsonHttpClient | None = None) -> None:
        self.http = http or JsonHttpClient()

    def fetch(self, location: Location) -> WeatherSnapshot:
        payload = self.http.get_json(
            FORECAST_URL,
            {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "timezone": location.timezone,
                "forecast_days": 1,
                "current": (
                    "temperature_2m,apparent_temperature,relative_humidity_2m,"
                    "weather_code,wind_speed_10m"
                ),
                "daily": (
                    "weather_code,temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max,uv_index_max"
                ),
            },
        )
        try:
            current = _object(payload, "current")
            daily = _object(payload, "daily")
            return WeatherSnapshot(
                weather_code=int(_value(current, "weather_code")),
                current_temperature=float(_value(current, "temperature_2m")),
                apparent_temperature=float(_value(current, "apparent_temperature")),
                humidity=int(_value(current, "relative_humidity_2m")),
                wind_speed=float(_value(current, "wind_speed_10m")),
                temperature_min=float(_first(daily, "temperature_2m_min")),
                temperature_max=float(_first(daily, "temperature_2m_max")),
                precipitation_probability=int(
                    _first(daily, "precipitation_probability_max")
                ),
                uv_index_max=float(_first(daily, "uv_index_max")),
            )
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise WeatherDataError("Open-Meteo 返回的数据字段不完整") from exc


def weather_text(code: int) -> str:
    mapping = {
        0: "晴朗",
        1: "大致晴朗",
        2: "多云",
        3: "阴天",
        45: "有雾",
        48: "雾凇",
        51: "小毛毛雨",
        53: "毛毛雨",
        55: "较强毛毛雨",
        56: "轻微冻雨",
        57: "冻雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        66: "轻微冻雨",
        67: "较强冻雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        77: "米雪",
        80: "小阵雨",
        81: "阵雨",
        82: "强阵雨",
        85: "小阵雪",
        86: "强阵雪",
        95: "雷雨",
        96: "雷雨伴小冰雹",
        99: "雷雨伴大冰雹",
    }
    return mapping.get(code, "天气多变")


def activity_suggestion(weather: WeatherSnapshot, period: str) -> str:
    rainy = weather.precipitation_probability >= 50 or weather.weather_code in {
        51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99
    }
    snowy = weather.weather_code in {71, 73, 75, 77, 85, 86}
    if rainy:
        return (
            "带好伞，适合在室内看书、喝热饮，路上慢一点"
            if period == "morning"
            else "回去记得带伞，今晚适合热饭、电影和好好休息"
        )
    if snowy:
        return "注意保暖和防滑，也可以拍一张雪景分享给我"
    if weather.temperature_max >= 35:
        return (
            "尽量避开午后暴晒，多喝水，适合室内学习和运动"
            if period == "morning"
            else "今天高温辛苦了，补点水，适合在室内放松和早点休息"
        )
    if weather.temperature_min <= 2:
        return (
            "多穿一层再出门，适合晒太阳、喝热饮和室内活动"
            if period == "morning"
            else "晚上降温，多穿一层，适合喝点热饮和早点休息"
        )
    if weather.wind_speed >= 35:
        return "风有点大，户外活动别太久，帽子和随身物品要拿稳"
    if period == "morning" and weather.uv_index_max >= 6:
        return "天气适合出门，午间紫外线偏强，记得防晒补水"
    if period == "morning":
        return "很适合校园散步或轻运动，给今天一个精神的开场"
    return "适合晚饭后走一走、看看晚霞，再给自己留点放松时间"


def _object(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data[key]
    if not isinstance(value, dict):
        raise TypeError(key)
    return value


def _value(data: dict[str, Any], key: str) -> Any:
    value = data[key]
    if value is None:
        raise ValueError(key)
    return value


def _first(data: dict[str, Any], key: str) -> Any:
    value = data[key]
    if not isinstance(value, list) or not value or value[0] is None:
        raise ValueError(key)
    return value[0]
