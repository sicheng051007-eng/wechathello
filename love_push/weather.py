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
        0: "晴朗 ☀️",
        1: "大致晴朗 🌤️",
        2: "多云 ⛅",
        3: "阴天 ☁️",
        45: "有雾 🌫️",
        48: "雾凇 🌫️",
        51: "小毛毛雨 🌦️",
        53: "毛毛雨 🌦️",
        55: "较强毛毛雨 🌧️",
        56: "轻微冻雨 🌧️",
        57: "冻雨 🌧️",
        61: "小雨 🌦️",
        63: "中雨 🌧️",
        65: "大雨 🌧️",
        66: "轻微冻雨 🌧️",
        67: "较强冻雨 🌧️",
        71: "小雪 🌨️",
        73: "中雪 ❄️",
        75: "大雪 ❄️",
        77: "米雪 ❄️",
        80: "小阵雨 🌦️",
        81: "阵雨 🌧️",
        82: "强阵雨 ⛈️",
        85: "小阵雪 🌨️",
        86: "强阵雪 ❄️",
        95: "雷雨 ⛈️",
        96: "雷雨伴小冰雹 ⛈️",
        99: "雷雨伴大冰雹 ⛈️",
    }
    return mapping.get(code, "天气多变 🌈")


def activity_suggestions(weather: WeatherSnapshot, period: str) -> tuple[str, ...]:
    """返回符合天气和时段的一组活动建议，供消息按日期稳定轮换。"""
    rainy = weather.precipitation_probability >= 50 or weather.weather_code in {
        51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99
    }
    snowy = weather.weather_code in {71, 73, 75, 77, 85, 86}
    if rainy:
        return (
            (
                "带好伞，适合去图书馆看书，路上慢一点 ☔",
                "雨天适合找间安静教室学习，休息时听听喜欢的歌 ☔",
                "适合在室内做拉伸或轻运动，出门记得穿防滑的鞋 ☔",
                "可以带杯热饮去自习，听着雨声专心完成一件小事 ☔",
            )
            if period == "morning"
            else (
                "回去记得带伞，今晚适合吃顿热饭、看场电影 ☔",
                "雨夜适合泡杯热饮、听听歌，再和我聊聊今天 ☔",
                "适合做一点室内拉伸，洗个热水澡后早点休息 ☔",
                "可以整理一下书桌和明日计划，然后安心放松 ☔",
            )
        )
    if snowy:
        return (
            (
                "注意保暖和防滑，课间可以安全地拍张雪景给我 ❄️",
                "适合在暖和的室内学习，出门慢走并避开结冰路面 ❄️",
                "可以喝杯热饮暖暖手，再隔着窗看看安静的雪景 ❄️",
                "适合去图书馆待一会儿，围巾手套也要记得带好 ❄️",
            )
            if period == "morning"
            else (
                "注意保暖和防滑，今晚适合热饭、热饮和好睡眠 ❄️",
                "可以拍一张夜色里的雪景给我，然后早点回到室内 ❄️",
                "适合泡泡脚、听听歌，让身体和心情都暖起来 ❄️",
                "回去路上慢一点，进门后可以看部轻松的电影 ❄️",
            )
        )
    if weather.temperature_max >= 35:
        return (
            (
                "尽量避开午后暴晒，多喝水，适合在室内学习 🧊",
                "可以把户外安排放在清晨，午后留给图书馆和空调房 🧊",
                "适合做舒缓的室内运动，随身带水并及时补充水分 🧊",
                "今天可以吃些清爽的水果，忙碌间隙也别忘了喝水 🧊",
            )
            if period == "morning"
            else (
                "今天高温辛苦了，补点水，适合在室内安静放松 🧊",
                "适合冲个温水澡、吃点水果，让燥热慢慢退下去 🧊",
                "可以等凉快些再短暂散步，今晚不要做剧烈运动 🧊",
                "吹着空调看看电影也很好，记得别让温度开得太低 🧊",
            )
        )
    if weather.temperature_min <= 2:
        return (
            (
                "多穿一层再出门，适合晒太阳、喝热饮和室内活动 🧣",
                "适合去暖和的图书馆学习，出门前记得围好围巾 🧣",
                "午间有阳光时可以慢慢走一走，活动身体也暖暖手 🧣",
                "带杯热水在身边，课间起来伸展一下会更舒服 🧣",
            )
            if period == "morning"
            else (
                "晚上降温，多穿一层，适合喝点热饮和早点休息 🧣",
                "可以泡泡脚、听听歌，把被窝提前暖得舒服一点 🧣",
                "适合吃顿热乎的晚饭，回去后做几分钟轻柔拉伸 🧣",
                "今晚少在室外久留，看看电影或读几页轻松的书吧 🧣",
            )
        )
    if weather.wind_speed >= 35:
        return (
            (
                "风有点大，适合室内活动，帽子和随身物品要拿稳 🍃",
                "可以去图书馆或健身房，今天别安排太久的户外运动 🍃",
                "适合在室内学习和拉伸，骑车经过风口时注意减速 🍃",
                "找个避风又有阳光的地方走走，出门记得穿好外套 🍃",
            )
            if period == "morning"
            else (
                "晚风较大，适合早点回去，在室内听歌或看电影 🍃",
                "今晚别在户外停留太久，可以回去做点轻松的拉伸 🍃",
                "回程注意侧风，进门后喝点热水、安心休息一会儿 🍃",
                "适合整理明日计划，再窝在舒服的地方读几页书 🍃",
            )
        )
    if period == "morning" and weather.uv_index_max >= 6:
        return (
            "天气适合出门，午间紫外线偏强，记得防晒补水 🧴",
            "适合清晨散步，正午尽量走阴凉处并戴好遮阳帽 🧴",
            "可以早点完成户外安排，午后去图书馆安静学习 🧴",
            "阳光很好，适合晒晒心情，但防晒和水杯都别落下 🧴",
        )
    if period == "morning":
        return (
            "很适合校园散步或轻运动，给今天一个精神的开场 🌿",
            "可以找片安静的地方读会儿书，再从容开始今天 🌿",
            "适合课间晒晒太阳、伸伸懒腰，让思路也透透气 🌿",
            "今天可以完成一件拖延的小事，再奖励自己一杯喜欢的饮料 🌿",
            "很适合和同学走走聊聊，也别忘了给自己留点独处时间 🌿",
            "可以戴上耳机散会儿步，用喜欢的歌开启好心情 🌿",
        )
    return (
        "适合晚饭后走一走、看看晚霞，再给自己留点放松时间 🌙",
        "可以听听歌、洗个热水澡，把今天的疲惫慢慢放下 🌙",
        "适合和我聊聊今天，也可以安静读几页喜欢的书 🌙",
        "去操场慢走几圈吧，吹吹晚风，再舒舒服服地休息 🌙",
        "可以吃点喜欢的东西、看一集轻松的剧，奖励今天的自己 🌙",
        "适合简单整理明日计划，然后把剩下的时间交给好梦 🌙",
    )


def activity_suggestion(weather: WeatherSnapshot, period: str) -> str:
    """兼容旧调用：返回当前天气场景的第一条活动建议。"""
    return activity_suggestions(weather, period)[0]


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
