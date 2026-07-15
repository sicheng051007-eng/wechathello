from __future__ import annotations

import hashlib
from html import escape
from pathlib import Path

from love_push.models import Recipient, TemplateMessage


def detail_page_path(recipient_id: str) -> str:
    """使用稳定但不暴露收件人名称的路径。"""
    digest = hashlib.sha256(recipient_id.encode("utf-8")).hexdigest()[:16]
    return f"message-{digest}/"


def detail_page_url(base_url: str, recipient_id: str) -> str:
    return f"{base_url.rstrip('/')}/{detail_page_path(recipient_id)}"


def write_detail_site(
    output_dir: str | Path,
    pages: list[tuple[Recipient, TemplateMessage]],
) -> None:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / ".nojekyll").write_text("", encoding="utf-8")
    (root / "index.html").write_text(_landing_html(), encoding="utf-8")

    for recipient, message in pages:
        page_dir = root / detail_page_path(recipient.id)
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            _message_html(message),
            encoding="utf-8",
        )


def _message_html(message: TemplateMessage) -> str:
    value = {
        name: escape(item["value"])
        for name, item in message.fields.items()
    }
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
        <span class="pill">🏫 {value['location']}</span>
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


def _landing_html() -> str:
    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>清浙小报</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;text-align:center;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;color:#694e59;background:linear-gradient(145deg,#fff1f4,#fffbed)}main{padding:32px}h1{font-size:32px}p{line-height:1.8;color:#9b7f89}</style></head><body><main><h1>💗 清浙小报</h1><p>每天两次，把天气和惦记送到彼此身边。</p></main></body></html>"""
