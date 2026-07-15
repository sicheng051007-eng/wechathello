from __future__ import annotations

import hashlib
import re
from datetime import datetime

from love_push.models import Recipient, TemplateMessage, WeatherSnapshot
from love_push.weather import activity_suggestion, weather_text


MORNING_WORDS = (
    "新的一天不用一下子做到完美，认真走好眼前这一小步就很好。",
    "你已经比自己想象中更勇敢了，今天也请相信自己的节奏。",
    "愿你今天遇到的题都有思路，走过的路都有好风景。",
    "再忙也别忘了吃早餐。你照顾好自己，就是给我的最好消息。",
    "距离只是地图上的数字，我们正在各自发光，也在一起向前。",
    "今天也会有小小的好事发生，记得留一点期待给它。",
    "不必和别人赶同一趟时间表，你稳稳地进步就已经很了不起。",
    "课业再多也要记得抬头看看天，我的惦记一直在你身边。",
    "愿你的努力都有回声，暂时没有也没关系，我先为你鼓掌。",
    "今天的你也值得被温柔对待，尤其要记得对自己温柔一点。",
    "把大目标切成一个个小任务，完成一个就奖励自己笑一下。",
    "早安，去做那个认真又可爱的你吧，我始终站在你这一边。",
)

EVENING_WORDS = (
    "今天辛苦啦。没做完的事留给明天，你的疲惫也值得被照顾。",
    "无论今天顺利还是磕绊，你都认真生活了一天，已经很棒了。",
    "别用一天里的小失误否定自己，你身上有更多闪闪发光的部分。",
    "忙碌的一天快结束了，记得好好吃饭，把烦恼也一起消化掉。",
    "我们隔着一段路，但你的每份开心和委屈，我都愿意认真听。",
    "今晚把脚步放慢一点，休息不是偷懒，是为了明天更有力气。",
    "今天完成了多少都可以，平安、健康、好好睡觉同样很重要。",
    "如果今天有点难，就允许它只是有点难，不代表你不够好。",
    "给今天画一个温柔的句号，明天仍然有新的可能在等你。",
    "晚风会带走一点疲惫，我的想念会替你留下暖意。",
    "愿你今晚吃到喜欢的东西，听到好消息，也做一个轻松的梦。",
    "你不需要时时坚强。累了就歇一歇，我一直是你的后援。",
)

WEEKDAYS = "一二三四五六日"


def compose_message(
    recipient: Recipient,
    weather: WeatherSnapshot | None,
    period: str,
    now: datetime,
) -> TemplateMessage:
    if period not in {"morning", "evening"}:
        raise ValueError("period 必须是 morning 或 evening")

    greeting = (
        f"早安呀，{recipient.name}！今天也一起加油 ☀️"
        if period == "morning"
        else f"晚上好，{recipient.name}！今天辛苦啦 🌙"
    )
    date_text = f"{now:%Y年%m月%d日} · 星期{WEEKDAYS[now.weekday()]}"
    words = MORNING_WORDS if period == "morning" else EVENING_WORDS
    encouragement = _daily_choice(words, now, recipient.id, period)

    if weather is None:
        weather_line = "天气暂时走丢了，但关心没有掉线 🛰️"
        temperature_line = "气温数据稍后再来，请按体感及时增减衣物"
        activity_line = "适合照顾好自己，也适合随时给我发消息 💗"
    else:
        weather_line = (
            f"{weather_text(weather.weather_code)}｜降雨 {weather.precipitation_probability}%"
            f"｜湿度 {weather.humidity}%"
        )
        temperature_line = (
            f"现在 {weather.current_temperature:.1f}℃（体感 {weather.apparent_temperature:.1f}℃）"
            f"｜今日 {weather.temperature_min:.0f}～{weather.temperature_max:.0f}℃"
        )
        activity_line = activity_suggestion(weather, period)

    return TemplateMessage(
        fields={
            "greeting": _field(greeting, "#FF6B81"),
            "date": _field(date_text, "#7A7A7A"),
            "location": _field(recipient.location.name, "#5B8FF9"),
            "weather": _field(weather_line, "#D48806"),
            "temperature": _field(temperature_line, "#E8684A"),
            "activity": _field(activity_line, "#389E0D"),
            "encouragement": _field(encouragement, "#C41D7F"),
            "closing": _field(recipient.signoff, "#722ED1"),
            "source": _field("天气数据：Open-Meteo", "#BFBFBF"),
        }
    )


def render_preview(message: TemplateMessage) -> str:
    fields = {name: item["value"] for name, item in message.fields.items()}
    return "\n".join(
        (
            fields["greeting"],
            "",
            f"📅 {fields['date']}",
            f"🏫 {fields['location']}",
            f"☁️ {fields['weather']}",
            f"🌡️ {fields['temperature']}",
            f"💡 {fields['activity']}",
            "",
            f"💌 {fields['encouragement']}",
            fields["closing"],
            f"☁️ {fields['source']}",
        )
    )


def compose_card_summary(
    recipient: Recipient,
    weather: WeatherSnapshot | None,
    period: str,
    full_message: TemplateMessage,
    url: str,
) -> TemplateMessage:
    """生成适合微信卡片首屏展示的短摘要，完整内容保留在详情页。"""
    fields = {
        name: dict(item)
        for name, item in full_message.fields.items()
    }
    fields["greeting"]["value"] = _short_text(
        (
            f"早安，{recipient.name} ☀️"
            if period == "morning"
            else f"晚安，{recipient.name} 🌙"
        ),
        16,
    )
    fields["date"]["value"] = re.sub(
        r"^\d{4}年(\d{2}月\d{2}日) · 星期(.)$",
        r"\1 周\2",
        fields["date"]["value"],
    )
    fields["location"]["value"] = _short_text(recipient.location.name, 14)

    if weather is None:
        fields["weather"]["value"] = "天气稍后再来｜先照顾好自己"
        fields["temperature"]["value"] = "按体感增减衣物"
    else:
        condition = weather_text(weather.weather_code).split("｜", 1)[0]
        fields["weather"]["value"] = (
            f"{condition}｜{weather.current_temperature:.0f}℃"
            f"｜雨{weather.precipitation_probability}%"
        )
        fields["temperature"]["value"] = (
            f"{weather.current_temperature:.0f}℃｜体感"
            f"{weather.apparent_temperature:.0f}℃"
        )

    fields["activity"]["value"] = _first_clause(
        full_message.fields["activity"]["value"], 16
    )
    fields["encouragement"]["value"] = _first_clause(
        full_message.fields["encouragement"]["value"], 18
    )
    fields["closing"]["value"] = _first_clause(recipient.signoff, 16)
    fields["source"]["value"] = "点击查看完整内容"
    return TemplateMessage(fields=fields, url=url)


def _daily_choice(words: tuple[str, ...], now: datetime, recipient_id: str, period: str) -> str:
    seed = f"{now.date().isoformat()}|{recipient_id}|{period}".encode("utf-8")
    index = int.from_bytes(hashlib.sha256(seed).digest()[:4], "big") % len(words)
    return words[index]


def _field(value: str, color: str) -> dict[str, str]:
    return {"value": value, "color": color}


def _first_clause(value: str, max_length: int) -> str:
    clause = re.split(r"[，。！？；\n]", value.strip(), maxsplit=1)[0].strip()
    return _short_text(clause or value, max_length)


def _short_text(value: str, max_length: int) -> str:
    return value.strip()[:max_length].rstrip()
