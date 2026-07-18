from __future__ import annotations

import hashlib
import re
from datetime import datetime

from love_push.models import Recipient, TemplateMessage, WeatherSnapshot
from love_push.weather import activity_suggestions, weather_text


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
    "醒来的第一件小事，是想告诉你：新的一天，我还是很喜欢你。",
    "愿清晨的好心情陪你穿过忙碌，今天也有我在远方惦记你。",
    "不用急着成为最厉害的人，认真做自己的你已经足够耀眼。",
    "如果今天任务很多，就一件一件来，我会一直为你加油。",
    "记得喝水、吃饭、偶尔伸个懒腰，你的身体也需要被认真照顾。",
    "愿你今天既有解决难题的专注，也有发现小确幸的轻松。",
    "每个普通的早晨，因为想到你，都变成了值得期待的一天。",
    "累的时候就想想，我们都在为了下一次见面认真生活。",
    "希望今天的阳光落在你肩上，也把我的拥抱悄悄带给你。",
    "你可以慢一点，但别忘了肯定一直没有放弃的自己。",
    "愿你今天上课有收获，走路有微风，三餐都有喜欢的味道。",
    "晨光已经出发，我的牵挂也是；愿你今天平安又顺心。",
    "遇到不会的题别着急，聪明的你总能一点点找到答案。",
    "今天也要把自己放在心上，你开心、健康，比什么都重要。",
    "远距离不会减少爱，只会让我更认真珍惜每一次分享。",
    "愿你带着从容开始今天，把压力留一点，把快乐多装一点。",
    "早安，我最牵挂的人。愿你的认真都被看见，真心都有回应。",
    "即使今天只是平凡的一天，也因为有你而对我意义非凡。",
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
    "今天最想听的不是你的成绩，而是你有没有好好吃饭、开心一点。",
    "把今天的压力先放在门外，今晚只需要安心做回轻松的自己。",
    "谢谢你又认真度过了一天，我也在远方认真地想念你。",
    "如果今天有遗憾，就把它变成明天的小提醒，不必变成责备。",
    "忙完记得告诉我今天的小故事，开心的和不开心的我都想听。",
    "今天的任务可以打烊了，但我对你的喜欢仍然全天营业。",
    "愿晚饭热乎，晚风温柔，回去的路一路有灯，也一路平安。",
    "你已经努力很久了，今晚允许自己什么都不想，好好放松一下。",
    "异地的夜晚并不孤单，同一片月光下，我也正在想你。",
    "今天没来得及夸自己也没关系，让我来告诉你：你真的很棒。",
    "愿所有疲惫都在热水澡和好睡眠里慢慢消散，明早轻松醒来。",
    "不开心可以分给我一半，开心也请分给我一半，我都愿意收藏。",
    "今天辛苦了，给认真生活的自己一个拥抱，也收下我隔空的拥抱。",
    "世界催你向前的时候，我会提醒你：偶尔停下来也完全可以。",
    "今晚别反复复盘不完美的地方，你做好的那些事也值得被记住。",
    "愿你放下手机后很快入睡，梦里没有ddl，只有自在和好风景。",
    "距离让拥抱晚一点到，却不会让我的关心少一点点。",
    "晚安之前再说一遍：你很重要，被爱着，也一直有人惦记。",
)

CARE_STYLES = ("温柔关心", "有些不舒服", "很难受想休息")

CARE_GREETINGS = {
    "温柔关心": "宝贝，这几天更要好好疼爱自己 🌷",
    "有些不舒服": "宝贝，今天慢一点，我一直都在 💗",
    "很难受想休息": "宝贝，难受就先休息，我一直都在 💗",
}

CARE_ACTIVITIES = {
    "温柔关心": (
        "今天适合把节奏调慢一点，喝点温热的东西，也给自己多一点休息 🌷",
        "想吃什么就选让身体舒服的，课间坐一会儿，晚上也早点休息 💗",
        "可以散一小会儿步、听喜欢的歌，今天的安排都以舒服为先 🌷",
        "记得带好需要的用品，穿得暖暖的，给自己留一点不被打扰的时间 💗",
        "今天适合热乎的饭、柔软的毯子和轻松的电影，其他事都慢慢来 🌷",
        "忙碌之间多停一停，喝水、伸展、深呼吸，把温柔也分给自己一些 💗",
    ),
    "有些不舒服": (
        "不舒服就先停一停，可以热敷一会儿、少站太久，今天不用逼自己满分 💗",
        "适合吃点热乎清淡的东西，腰腹注意保暖，能休息时就歇一歇 🌷",
        "今天少安排剧烈运动，找个舒服的位置坐坐，难受时随时告诉我 💗",
        "可以洗个温热的澡、早点躺下，课业和消息都不必急着马上处理 🌷",
        "把必须做的事缩到最少，剩下的时间用来热敷、休息和照顾自己 💗",
        "如果还要出门，记得放慢脚步、带好用品，回来就让自己好好歇着 🌷",
    ),
    "很难受想休息": (
        "今天最重要的任务是好好休息，其他事情能缓就缓，我永远站在你这边 💗",
        "难受就联系我，不要一个人硬撑；身体明显不适时记得及时找校医院帮忙 🌷",
        "先躺下来休息一会儿，热敷、温水和安静的陪伴都已经替你准备好啦 💗",
        "今天可以暂时不做那个无所不能的你，只要好好吃饭、休息和照顾自己 🌷",
        "如果疼痛影响上课或日常活动，就请及时向老师、同学或校医院求助 💗",
        "把计划先按下暂停键吧，舒服一点比完成清单更重要，我会一直陪着你 🌷",
    ),
}

CARE_WORDS = {
    "温柔关心": (
        "生理期不是需要你独自熬过去的几天，它只是提醒我，要比平时再多爱你一点。",
        "隔着一段路，我没法立刻递上热水，但每一句关心都在认真抱抱你。",
        "今天不用把所有事情都做好，你照顾好自己，就是我最想收到的好消息。",
        "希望这条消息像一条软软的毯子，把我的想念和温度一起盖在你身上。",
        "你可以照常闪闪发光，也可以暂时做一朵慢慢休息的小云，我都一样喜欢。",
        "想把今天所有温柔都打包寄给你：一份安心，一份惦记，还有很多很多喜欢。",
    ),
    "有些不舒服": (
        "难受的时候不用表现得和平时一样有力气，在我这里，你永远可以放心说累。",
        "我不能替你分走疼痛，但我愿意一直听你说，也一直站在你需要我的地方。",
        "今天的你不需要满分，只需要被好好照顾；剩下的事情，我们以后慢慢完成。",
        "如果身体在闹小脾气，就先哄哄它吧。你休息的时候，我会替你守着这份安心。",
        "不舒服可以告诉我，想安静也可以告诉我；怎样让你好受一点，就怎样来。",
        "真想现在就给你一个暖暖的拥抱，再认真告诉你：别怕，我一直都在。",
    ),
    "很难受想休息": (
        "今天不用坚强，也不用怕打扰我。你的一句难受，永远值得我认真回应。",
        "先把世界调成静音，好好休息。没完成的事情不会跑，我也不会离开。",
        "如果可以，我想把你的疼痛轻轻拿走，再把安心、睡意和拥抱都留给你。",
        "你不需要一个人扛过去，随时给我打电话；隔着距离，我也会认真陪着你。",
        "今天只做一件事就好：把自己放在第一位。你舒服一点，我才能放心一点。",
        "我最在意的从来不是你今天做了多少，而是你有没有被温柔照顾、平安休息。",
    ),
}

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

    weather_line, temperature_line = _weather_lines(weather)
    if weather is None:
        activity_line = "适合照顾好自己，也适合随时给我发消息 💗"
    else:
        activity_line = _daily_choice(
            activity_suggestions(weather, period),
            now,
            recipient.id,
            f"{period}|activity",
        )

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


def compose_period_care_message(
    recipient: Recipient,
    weather: WeatherSnapshot | None,
    care_style: str,
    now: datetime,
    extra_words: str = "",
) -> TemplateMessage:
    if care_style not in CARE_STYLES:
        raise ValueError("care_style 必须是：" + "、".join(CARE_STYLES))

    weather_line, temperature_line = _weather_lines(weather)
    activity = _daily_choice(
        CARE_ACTIVITIES[care_style],
        now,
        recipient.id,
        f"period-care|{care_style}|activity",
    )
    encouragement = _daily_choice(
        CARE_WORDS[care_style],
        now,
        recipient.id,
        f"period-care|{care_style}|words",
    )
    personal_words = re.sub(r"\s+", " ", extra_words).strip()[:120]
    if personal_words:
        encouragement = f"{personal_words.rstrip('。！？')}。{encouragement}"

    return TemplateMessage(
        fields={
            "greeting": _field(CARE_GREETINGS[care_style], "#E94B78"),
            "date": _field(
                f"{now:%Y年%m月%d日} · 星期{WEEKDAYS[now.weekday()]}",
                "#8C6A76",
            ),
            "location": _field(recipient.location.name, "#A45A82"),
            "weather": _field(weather_line, "#C76B37"),
            "temperature": _field(temperature_line, "#D65B72"),
            "activity": _field(activity, "#9A5B76"),
            "encouragement": _field(encouragement, "#C41D7F"),
            "closing": _field(recipient.signoff, "#8B3A62"),
            "source": _field("天气数据：Open-Meteo", "#B49BA5"),
        }
    )


def render_preview(message: TemplateMessage) -> str:
    fields = {name: item["value"] for name, item in message.fields.items()}
    return "\n".join(
        (
            fields["greeting"],
            "",
            f"📅 {fields['date']}",
            f"🌏 {fields['location']}",
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
    message_kind: str = "daily",
) -> TemplateMessage:
    """生成适合微信卡片首屏展示的短摘要，完整内容保留在详情页。"""
    fields = {
        name: dict(item)
        for name, item in full_message.fields.items()
    }
    if message_kind == "period-care":
        fields["greeting"]["value"] = _short_text(
            full_message.fields["greeting"]["value"], 18
        )
    else:
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


def _weather_lines(weather: WeatherSnapshot | None) -> tuple[str, str]:
    if weather is None:
        return (
            "天气暂时走丢了，但关心没有掉线 🛰️",
            "气温数据稍后再来，请按体感及时增减衣物",
        )
    return (
        f"{weather_text(weather.weather_code)}｜降雨 {weather.precipitation_probability}%"
        f"｜湿度 {weather.humidity}%",
        f"现在 {weather.current_temperature:.1f}℃（体感 {weather.apparent_temperature:.1f}℃）"
        f"｜今日 {weather.temperature_min:.0f}～{weather.temperature_max:.0f}℃",
    )


def _first_clause(value: str, max_length: int) -> str:
    clause = re.split(r"[，。！？；\n]", value.strip(), maxsplit=1)[0].strip()
    return _short_text(clause or value, max_length)


def _short_text(value: str, max_length: int) -> str:
    return value.strip()[:max_length].rstrip()
