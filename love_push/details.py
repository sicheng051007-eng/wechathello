from __future__ import annotations

import hashlib
from html import escape
from pathlib import Path

from love_push.models import Recipient, TemplateMessage


def detail_page_path(recipient_id: str, page_kind: str = "daily") -> str:
    """使用稳定但不暴露收件人名称的路径。"""
    seed = recipient_id if page_kind == "daily" else f"{recipient_id}|{page_kind}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"message-{digest}/"


def detail_page_url(
    base_url: str,
    recipient_id: str,
    page_kind: str = "daily",
) -> str:
    return f"{base_url.rstrip('/')}/{detail_page_path(recipient_id, page_kind)}"


def write_detail_site(
    output_dir: str | Path,
    pages: list[tuple[Recipient, TemplateMessage]],
    page_kind: str = "daily",
) -> None:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / ".nojekyll").write_text("", encoding="utf-8")
    (root / "index.html").write_text(_landing_html(), encoding="utf-8")

    for recipient, message in pages:
        page_dir = root / detail_page_path(recipient.id, page_kind)
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            _message_html(message, page_kind),
            encoding="utf-8",
        )


def _message_html(message: TemplateMessage, page_kind: str = "daily") -> str:
    value = {
        name: escape(item["value"])
        for name, item in message.fields.items()
    }
    if page_kind == "period-care":
        return _period_care_html(value)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <meta name="theme-color" content="#fff7f8">
  <title>清浙小报 · 今日完整内容</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; color: #342d31; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; background: linear-gradient(160deg, #fff7f8 0%, #fffdf6 54%, #f4f9ff 100%); }}
    main {{ width: min(100% - 28px, 620px); margin: 0 auto; padding: 26px 0 calc(40px + env(safe-area-inset-bottom)); }}
    .hero, .card, .love {{ border: 1px solid rgba(255,255,255,.86); box-shadow: 0 14px 40px rgba(108, 72, 84, .10); }}
    .hero {{ padding: 26px 22px; border-radius: 28px; color: #fff; background: linear-gradient(135deg, #ff8297, #ffaf85); }}
    .eyebrow {{ margin: 0 0 10px; font-size: 13px; letter-spacing: .18em; opacity: .86; }}
    h1 {{ margin: 0; font-size: clamp(24px, 7vw, 34px); line-height: 1.35; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0 0; }}
    .pill {{ padding: 7px 11px; border-radius: 999px; font-size: 13px; color: #6b5960; background: rgba(255,255,255,.78); }}
    .grid {{ display: grid; gap: 12px; margin-top: 14px; }}
    .card {{ padding: 18px; border-radius: 22px; background: rgba(255,255,255,.78); backdrop-filter: blur(12px); }}
    .label {{ margin: 0 0 8px; color: #98858c; font-size: 13px; }}
    .value {{ margin: 0; font-size: 17px; line-height: 1.75; overflow-wrap: anywhere; }}
    .love {{ margin-top: 14px; padding: 22px; border-radius: 24px; background: linear-gradient(145deg, rgba(255,240,245,.94), rgba(255,255,255,.92)); }}
    .love .value {{ color: #a34369; font-size: 18px; }}
    .closing {{ margin: 16px 0 0; color: #765165; line-height: 1.7; }}
    footer {{ padding-top: 18px; text-align: center; color: #ae9da4; font-size: 12px; }}
    @media (min-width: 560px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} .wide {{ grid-column: 1 / -1; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">QING · ZHE DAILY</p>
      <h1>{value['greeting']}</h1>
      <div class="meta">
        <span class="pill">📅 {value['date']}</span>
        <span class="pill">🌏 {value['location']}</span>
      </div>
    </section>
    <section class="grid">
      <article class="card"><p class="label">☁️ 当地天气</p><p class="value">{value['weather']}</p></article>
      <article class="card"><p class="label">🌡️ 气温情况</p><p class="value">{value['temperature']}</p></article>
      <article class="card wide"><p class="label">💡 适合做什么</p><p class="value">{value['activity']}</p></article>
    </section>
    <section class="love">
      <p class="label">💌 今天想对你说</p>
      <p class="value">{value['encouragement']}</p>
      <p class="closing">{value['closing']}</p>
    </section>
    <footer>{value['source']} · 页面由 GitHub Actions 自动更新</footer>
  </main>
</body>
</html>
"""


def _period_care_html(value: dict[str, str]) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <meta name="theme-color" content="#fff1f5">
  <title>给宝贝的一封温柔小信</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; color: #51343f; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; background: radial-gradient(circle at 12% 8%, #ffe0e9 0 7%, transparent 28%), radial-gradient(circle at 92% 22%, #f9e0ee 0 6%, transparent 25%), linear-gradient(160deg, #fff8fa 0%, #fff1f5 48%, #fffaf5 100%); }}
    main {{ width: min(100% - 28px, 620px); margin: 0 auto; padding: 22px 0 calc(42px + env(safe-area-inset-bottom)); }}
    .letter {{ position: relative; overflow: hidden; border: 1px solid rgba(255,255,255,.9); border-radius: 30px; box-shadow: 0 22px 60px rgba(147,66,94,.14); background: rgba(255,255,255,.82); backdrop-filter: blur(14px); }}
    .hero {{ position: relative; padding: 32px 22px 28px; color: #fff; text-align: center; background: linear-gradient(135deg, #f26d91 0%, #ef89a5 46%, #eaa3b9 100%); }}
    .hero::before, .hero::after {{ position: absolute; content: "♥"; color: rgba(255,255,255,.2); font-size: 72px; line-height: 1; }}
    .hero::before {{ left: -14px; top: 8px; transform: rotate(-18deg); }}
    .hero::after {{ right: -8px; bottom: -10px; transform: rotate(16deg); }}
    .eyebrow {{ position: relative; z-index: 1; margin: 0 0 13px; font-size: 12px; font-weight: 700; letter-spacing: .19em; opacity: .86; }}
    h1 {{ position: relative; z-index: 1; margin: 0; font-size: clamp(25px, 7vw, 35px); line-height: 1.42; letter-spacing: .02em; }}
    .promise {{ position: relative; z-index: 1; display: inline-block; margin: 18px 0 0; padding: 8px 13px; border: 1px solid rgba(255,255,255,.34); border-radius: 999px; font-size: 13px; background: rgba(255,255,255,.16); }}
    .content {{ padding: 20px; }}
    .meta {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; margin: -3px 0 18px; }}
    .pill {{ padding: 7px 11px; border-radius: 999px; color: #8d6070; font-size: 13px; background: #fff3f6; }}
    .section {{ margin-top: 12px; padding: 18px; border-radius: 22px; background: #fffafb; box-shadow: inset 0 0 0 1px rgba(229,150,176,.16); }}
    .weather-grid {{ display: grid; gap: 10px; }}
    .weather-item {{ padding: 15px; border-radius: 18px; background: linear-gradient(145deg, #fff, #fff5f7); }}
    .label {{ margin: 0 0 8px; color: #ad7488; font-size: 13px; font-weight: 650; letter-spacing: .03em; }}
    .value {{ margin: 0; font-size: 16px; line-height: 1.78; overflow-wrap: anywhere; }}
    .care {{ background: linear-gradient(145deg, #fff8f1, #fffafb); }}
    .love {{ position: relative; padding: 23px 20px; text-align: center; background: linear-gradient(145deg, #ffedf3, #fff9fb); }}
    .love::before {{ content: "“"; position: absolute; left: 15px; top: 3px; color: rgba(220,91,132,.16); font: 72px/1 Georgia, serif; }}
    .love .value {{ position: relative; color: #a43e62; font-size: 18px; font-weight: 520; line-height: 1.85; }}
    .closing {{ margin: 20px 0 0; padding-top: 17px; border-top: 1px dashed #edc4d1; color: #805063; line-height: 1.75; }}
    .gentle-note {{ margin: 19px 0 2px; color: #b27f91; font-size: 13px; line-height: 1.7; text-align: center; }}
    footer {{ padding: 17px 20px 21px; color: #b69aa4; font-size: 11px; text-align: center; background: rgba(255,247,249,.72); }}
    @media (min-width: 560px) {{ .weather-grid {{ grid-template-columns: 1fr 1fr; }} .content {{ padding: 24px; }} }}
  </style>
</head>
<body>
  <main>
    <article class="letter">
      <header class="hero">
        <p class="eyebrow">A LITTLE LOVE FROM ZJU</p>
        <h1>{value['greeting']}</h1>
        <p class="promise">今天不用逞强，你只需要被好好爱着</p>
      </header>
      <div class="content">
        <div class="meta">
          <span class="pill">📅 {value['date']}</span>
          <span class="pill">🌏 {value['location']}</span>
        </div>
        <section class="weather-grid">
          <div class="weather-item"><p class="label">☁️ 先看看你那边</p><p class="value">{value['weather']}</p></div>
          <div class="weather-item"><p class="label">🌡️ 今天的温度</p><p class="value">{value['temperature']}</p></div>
        </section>
        <section class="section care">
          <p class="label">💡 今天怎么照顾自己</p>
          <p class="value">{value['activity']}</p>
        </section>
        <section class="section love">
          <p class="label">💌 把我的拥抱放在这里</p>
          <p class="value">{value['encouragement']}</p>
          <p class="closing">{value['closing']}</p>
        </section>
        <p class="gentle-note">不用急着回复，舒服一点更重要。<br>如果明显不适或疼痛影响日常，请及时寻求专业帮助。</p>
      </div>
      <footer>{value['source']} · 这份惦记由 GitHub Actions 送达</footer>
    </article>
  </main>
</body>
</html>
"""


def _landing_html() -> str:
    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>清浙小报</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;text-align:center;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;color:#694e59;background:linear-gradient(145deg,#fff1f4,#fffbed)}main{padding:32px}h1{font-size:32px}p{line-height:1.8;color:#9b7f89}</style></head><body><main><h1>💗 清浙小报</h1><p>每天两次，把天气和惦记送到彼此身边。</p></main></body></html>"""
