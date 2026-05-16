import logging
import time

from deep_translator import GoogleTranslator

import config

logger = logging.getLogger("translator")


def translate_articles(articles: list[dict]) -> list[dict]:
    translator = GoogleTranslator(source="en", target="zh-CN")

    for article in articles:
        # 翻译标题
        try:
            article["title_cn"] = translator.translate(article["title"])
            time.sleep(config.TRANSLATION_DELAY)
        except Exception as e:
            logger.warning(f"Title translation failed: {e}")
            article["title_cn"] = article["title"]

        # 翻译摘要
        try:
            raw = article.get("summary", "")[:500]
            if raw.strip():
                article["summary_cn"] = translator.translate(raw)
                if len(article["summary_cn"]) > config.MAX_SUMMARY_LENGTH:
                    article["summary_cn"] = (
                        article["summary_cn"][: config.MAX_SUMMARY_LENGTH] + "..."
                    )
            else:
                article["summary_cn"] = ""
            time.sleep(config.TRANSLATION_DELAY)
        except Exception as e:
            logger.warning(f"Summary translation failed: {e}")
            article["summary_cn"] = article.get("summary", "")

    return articles
