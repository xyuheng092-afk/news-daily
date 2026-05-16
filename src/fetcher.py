import logging
from datetime import datetime, timezone

import feedparser

import config

logger = logging.getLogger("fetcher")

# 设置全局 User-Agent，避免被 RSS 服务器拒绝
feedparser.USER_AGENT = config.USER_AGENT


def _clean_summary(entry) -> str:
    """从 feed entry 中提取并清理摘要文本"""
    raw = entry.get("summary", "") or entry.get("description", "") or ""
    # 去除 HTML 标签（简单方式）
    import re
    text = re.sub(r"<[^>]+>", "", raw)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'")
    return " ".join(text.split())[:500]


def _parse_date(entry) -> str:
    """解析发布时间，返回 ISO 格式字符串"""
    from dateutil import parser as dateparser

    raw = entry.get("published", "") or entry.get("updated", "")
    if not raw:
        return ""
    try:
        dt = dateparser.parse(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except (ValueError, OverflowError):
        return ""


def fetch_all_sources(sources: dict) -> list[dict]:
    articles = []
    for source_name, feed_urls in sources.items():
        for url in feed_urls:
            try:
                logger.info(f"Fetching {source_name}: {url}")
                feed = feedparser.parse(url)

                if feed.bozo and not feed.entries:
                    logger.warning(
                        f"Feed parse warning for {url}: {feed.bozo_exception}"
                    )
                    continue

                for entry in feed.entries:
                    title = (entry.get("title", "") or "").strip()
                    link = (entry.get("link", "") or "").strip()

                    if not title or not link:
                        continue

                    article = {
                        "title": title,
                        "link": link,
                        "summary": _clean_summary(entry),
                        "source": source_name,
                        "published": _parse_date(entry),
                    }
                    articles.append(article)

                logger.info(
                    f"  -> {source_name} [{url}] fetched {len(feed.entries)} entries"
                )

            except Exception as e:
                logger.warning(f"Failed to fetch {source_name} [{url}]: {e}")
                continue

    return articles
