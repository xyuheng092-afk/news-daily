import logging
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

logger = logging.getLogger("mailer")

TAG_COLORS = {
    "breaking": "#dc3545",
    "politics": "#0d6efd",
    "economy": "#198754",
    "tech": "#6f42c1",
    "general": "#6c757d",
}

CATEGORY_LABELS = {
    "breaking": "突发",
    "politics": "政治",
    "economy": "经济",
    "tech": "科技",
    "general": "综合",
}

BJT = timezone(timedelta(hours=8))


def _build_html(articles: list[dict]) -> str:
    now_bj = datetime.now(BJT)
    date_str = now_bj.strftime("%Y年%m月%d日")

    items_html = ""
    for i, a in enumerate(articles, 1):
        cat = a.get("category", "general")
        color = TAG_COLORS.get(cat, TAG_COLORS["general"])
        label = CATEGORY_LABELS.get(cat, "综合")
        title = a.get("title_cn", a["title"])
        short_summary = a.get("summary_cn", a.get("summary", ""))
        source = a.get("source", "")
        is_hot = a.get("is_hot", False)
        cluster_size = a.get("cluster_size", 1)
        full_text = a.get("full_content_cn", "")
        has_full = bool(full_text and len(full_text) > 30)

        hot_badge = ""
        if is_hot and cluster_size >= 3:
            hot_badge = (
                f'<span style="display:inline-block;background:#ff6b35;color:#fff;'
                f'font-size:10px;padding:1px 6px;border-radius:3px;margin-left:4px;">'
                f'🔥 {cluster_size}家媒体报道</span>'
            )

        # 有全文翻译时用 details/summary 实现展开/收起
        full_section = ""
        if has_full:
            full_section = f"""
            <details style="margin-top:10px;">
                <summary style="cursor:pointer;font-size:12px;color:#1a73e8;
                                display:inline-block;padding:4px 12px;
                                border:1px solid #1a73e8;border-radius:14px;
                                user-select:none;">
                    阅读中文全文
                </summary>
                <div style="font-size:14px;color:#333;line-height:1.9;margin-top:12px;
                            padding:14px 16px;background:#fafafa;border-radius:6px;
                            border-left:3px solid {color};">
                    {full_text}
                </div>
            </details>"""

        items_html += f"""
        <tr>
            <td style="padding:16px 20px; border-bottom:1px solid #eee;">
                <div style="margin-bottom:4px;">
                    <span style="display:inline-block;background:{color};color:#fff;
                        font-size:10px;padding:2px 8px;border-radius:3px;margin-right:6px;">
                        {label}
                    </span>
                    <span style="font-size:12px;color:#999;">{source}</span>
                    {hot_badge}
                </div>
                <div style="font-size:15px;font-weight:bold;color:#222;line-height:1.4;
                            margin-bottom:4px;">
                    {i}. {title}
                </div>
                <div style="font-size:12px;color:#888;line-height:1.5;margin-bottom:6px;">
                    {short_summary[:120]}{'...' if len(short_summary) > 120 else ''}
                </div>
                <div style="font-size:11px;">
                    <a href="{a['link']}" target="_blank"
                       style="color:#999;text-decoration:none;">查看英文原文 &rarr;</a>
                </div>
                {full_section}
            </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f4f4f4;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;">
<tr><td align="center" style="padding:20px 10px;">
<table width="640" cellpadding="0" cellspacing="0"
       style="background:#fff;border-radius:8px;overflow:hidden;
              box-shadow:0 2px 8px rgba(0,0,0,0.08);">

    <!-- Header -->
    <tr>
        <td style="background:linear-gradient(135deg,#1a73e8,#1557b0);
                   padding:24px 20px;text-align:center;">
            <div style="font-size:20px;font-weight:bold;color:#fff;">
                每日全球新闻精选
            </div>
            <div style="font-size:12px;color:rgba(255,255,255,0.8);margin-top:4px;">
                {date_str} · 精选{len(articles)}条要闻 · 经济/政治/科技/突发
            </div>
        </td>
    </tr>

    <!-- Articles -->
    {items_html}

    <!-- Footer -->
    <tr>
        <td style="padding:18px;text-align:center;
                   background:#fafafa;border-top:1px solid #eee;">
            <div style="font-size:11px;color:#aaa;">
                CNN · FOX · NYT · BBC · Reuters · CNBC · AP · The Guardian
                · HackerNews · TechCrunch · TheVerge · 36氪 · 虎嗅 · 澎湃 · CGTN
            </div>
            <div style="font-size:11px;color:#aaa;margin-top:2px;">
                抓取时间：{now_bj.strftime('%Y-%m-%d %H:%M')} (北京时间)
            </div>
            <div style="font-size:10px;color:#ccc;margin-top:6px;">
                News Daily Bot · Powered by DeepSeek AI
            </div>
        </td>
    </tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def send_email(articles: list[dict]) -> bool:
    if not config.SENDER_EMAIL or not config.SENDER_PASSWORD:
        raise RuntimeError("邮件配置缺失: 请设置 SENDER_EMAIL 和 SENDER_PASSWORD 环境变量")

    if not config.RECIPIENT_EMAIL:
        raise RuntimeError("邮件配置缺失: 请设置 RECIPIENT_EMAIL 环境变量")

    date_str = datetime.now(BJT).strftime("%Y年%m月%d日")
    html = _build_html(articles)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"每日全球新闻精选 - {date_str}"
    msg["From"] = config.SENDER_EMAIL
    msg["To"] = config.RECIPIENT_EMAIL
    msg.attach(MIMEText(html, "html", "utf-8"))

    logger.info(f"Sending email to {config.RECIPIENT_EMAIL} via {config.SMTP_SERVER}")
    with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT, timeout=30) as server:
        server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
        server.sendmail(config.SENDER_EMAIL, config.RECIPIENT_EMAIL, msg.as_string())

    return True
