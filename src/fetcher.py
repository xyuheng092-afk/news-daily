import logging
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

import config

logger = logging.getLogger("fetcher")

feedparser.USER_AGENT = config.USER_AGENT


def _clean_summary(text: str) -> str:
    """去除 HTML 标签，清理空白"""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'")
    return " ".join(text.split())[:500]


def _extract_summary(entry) -> str:
    """从 feedparser entry 提取摘要"""
    raw = entry.get("summary", "") or entry.get("description", "") or ""
    return _clean_summary(raw)


def _parse_date(entry) -> str:
    """解析 feedparser entry 的发布时间"""
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


def fetch_rss_sources(sources: dict) -> list[dict]:
    """从 RSS/Atom feed 抓取文章"""
    articles = []
    for source_name, feed_urls in sources.items():
        for url in feed_urls:
            try:
                logger.info(f"Fetching RSS {source_name}: {url}")
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

                    articles.append({
                        "title": title,
                        "link": link,
                        "summary": _extract_summary(entry),
                        "source": source_name,
                        "published": _parse_date(entry),
                    })

                logger.info(
                    f"  -> {source_name} [{url}] fetched {len(feed.entries)} entries"
                )

            except Exception as e:
                logger.warning(f"Failed to fetch {source_name} [{url}]: {e}")
                continue

    return articles


def fetch_web_source(name: str, cfg: dict) -> list[dict]:
    """从网页抓取文章（用于没有 RSS 的网站，如 CCTV）"""
    articles = []
    url = cfg["url"]
    selectors = cfg.get("item_selector", "a")
    max_items = cfg.get("max_items", 30)

    try:
        logger.info(f"Fetching WEB {name}: {url}")
        resp = requests.get(
            url,
            headers={"User-Agent": config.USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        seen = set()
        for selector in selectors.split(","):
            selector = selector.strip()
            for tag in soup.select(selector):
                if len(articles) >= max_items:
                    break
                title = tag.get_text(strip=True)
                href = tag.get("href", "")
                if not title or not href or len(title) < 6:
                    continue
                full_link = urljoin(url, href)
                if full_link in seen:
                    continue
                seen.add(full_link)
                articles.append({
                    "title": title,
                    "link": full_link,
                    "summary": "",
                    "source": name,
                    "published": datetime.now(timezone.utc).isoformat(),
                })

        logger.info(f"  -> {name} [{url}] scraped {len(articles)} items")

    except Exception as e:
        logger.warning(f"Failed to scrape {name} [{url}]: {e}")

    return articles


def fetch_all_sources() -> list[dict]:
    """抓取所有源（RSS + 网页）"""
    articles = []
    articles.extend(fetch_rss_sources(config.RSS_SOURCES))
    for name, cfg in config.WEB_SOURCES.items():
        articles.extend(fetch_web_source(name, cfg))
    return articles
