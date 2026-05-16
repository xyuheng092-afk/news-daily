import hashlib
import json
import logging
import os
from datetime import datetime, timedelta

import config

logger = logging.getLogger("dedup")


def _hash_url(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def load_sent_hashes() -> set:
    if not os.path.exists(config.SENT_URLS_FILE):
        return set()
    try:
        with open(config.SENT_URLS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        logger.warning("sent_urls.json is corrupted, resetting")
        return set()

    today = datetime.now().strftime("%Y-%m-%d")
    # 只去重当天的 URL，隔天自动失效，保证每天两次推送内容不同、每天都有新内容
    return {h for h, d in data.items() if d == today}


def save_sent_hashes(hashes: dict):
    os.makedirs(config.DATA_DIR, exist_ok=True)

    existing = {}
    if os.path.exists(config.SENT_URLS_FILE):
        try:
            with open(config.SENT_URLS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}

    existing.update(hashes)

    cutoff = (datetime.now() - timedelta(days=config.RETENTION_DAYS)).strftime(
        "%Y-%m-%d"
    )
    existing = {h: d for h, d in existing.items() if d >= cutoff}

    with open(config.SENT_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def filter_duplicates(articles: list[dict]) -> tuple[list[dict], dict]:
    sent = load_sent_hashes()
    unique = []
    new_hashes = {}
    today = datetime.now().strftime("%Y-%m-%d")

    for a in articles:
        h = _hash_url(a["link"])
        if h not in sent:
            unique.append(a)
            new_hashes[h] = today

    logger.info(f"Duplicates filtered: {len(articles)} -> {len(unique)}")
    return unique, new_hashes
