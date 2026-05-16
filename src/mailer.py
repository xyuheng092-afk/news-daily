import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
from src.filter import CATEGORY_LABELS

logger = logging.getLogger("mailer")

TAG_COLORS = {
    "breaking": "#dc3545",
    "politics": "#0d6efd",
    "economy": "#198754",
    "general": "#6c757d",
}


def _build_html(articles: list[dict]) -> str:
    date_str = datetime.now().strftime("%Y年%m月%d日")

    items_html = ""
    for i, a in enumerate(articles, 1):
        cat = a.get("category", "general")
        color = TAG_COLORS.get(cat, TAG_COLORS["general"])
        label = CATEGORY_LABELS.get(cat, "综合")
        title = a.get("title_cn", a["title"])
        summary = a.get("summary_cn", a.get("summary", ""))
        source = a.get("source", "")

        items_html += f"""
        <tr>
            <td style="padding: 16px 20px; border-bottom: 1px solid #eee;">
                <div style="margin-bottom: 6px;">
                    <span style="display:inline-block;background:{color};color:#fff;
                        font-size:11px;padding:2px 8px;border-radius:3px;margin-right:6px;">
                        {label}
                    </span>
                    <span style="font-size:12px;color:#999;">{source}</span>
                </div>
                <div style="margin-bottom: 4px;">
                    <a href="{a['link']}" target="_blank"
                       style="font-size:16px;font-weight:bold;color:#222;text-decoration:none;
                              line-height:1.4;">
                        {i}. {title}
                    </a>
                </div>
                <div style="font-size:13px;color:#666;line-height:1.5;">
                    {summary}
                </div>
            </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f4f4f4;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;">
<tr><td align="center" style="padding:20px 10px;">
<table width="600" cellpadding="0" cellspacing="0"
       style="background:#fff;border-radius:8px;overflow:hidden;
              box-shadow:0 2px 8px rgba(0,0,0,0.08);">

    <!-- Header -->
    <tr>
        <td style="background:linear-gradient(135deg,#1a73e8,#1557b0);
                   padding:30px 20px;text-align:center;">
            <div style="font-size:22px;font-weight:bold;color:#fff;">
                每日新闻精选
            </div>
            <div style="font-size:13px;color:rgba(255,255,255,0.8);margin-top:6px;">
                {date_str} · 精选{len(articles)}条要闻
            </div>
        </td>
    </tr>

    <!-- Articles -->
    {items_html}

    <!-- Footer -->
    <tr>
        <td style="padding:20px;text-align:center;
                   background:#fafafa;border-top:1px solid #eee;">
            <div style="font-size:11px;color:#aaa;">
                新闻来源：CNN · FOX News · New York Times · CGTN<br>
                自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M")} (北京时间)
            </div>
            <div style="font-size:10px;color:#ccc;margin-top:4px;">
                本邮件由 News Daily Bot 自动发送
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

    date_str = datetime.now().strftime("%Y年%m月%d日")
    html = _build_html(articles)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"每日新闻精选 - {date_str}"
    msg["From"] = config.SENDER_EMAIL
    msg["To"] = config.RECIPIENT_EMAIL
    msg.attach(MIMEText(html, "html", "utf-8"))

    logger.info(f"Sending email to {config.RECIPIENT_EMAIL} via {config.SMTP_SERVER}")
    with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT, timeout=30) as server:
        server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
        server.sendmail(config.SENDER_EMAIL, config.RECIPIENT_EMAIL, msg.as_string())

    return True
