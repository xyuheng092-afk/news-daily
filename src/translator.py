import logging
import time

from deep_translator import GoogleTranslator

import config

logger = logging.getLogger("translator")


def _get_translator():
    return GoogleTranslator(source="en", target="zh-CN")


def translate_articles(articles: list[dict]) -> list[dict]:
    """翻译标题和摘要（用于 fallback 关键词模式）"""
    try:
        translator = _get_translator()
    except Exception as e:
        logger.error(f"翻译器初始化失败: {e}")
        raise

    for article in articles:
        if article.get("source") in config.CHINESE_SOURCES:
            article["title_cn"] = article["title"]
            article["summary_cn"] = article.get("summary", "")
            continue

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


def translate_titles(articles: list[dict]) -> list[dict]:
    """仅翻译标题（LLM 模式下摘要已由 LLM 生成，只需翻译标题）"""
    try:
        translator = _get_translator()
    except Exception as e:
        logger.error(f"翻译器初始化失败: {e}")
        raise

    for article in articles:
        # 中文源直接使用原标题
        if article.get("source") in config.CHINESE_SOURCES:
            article["title_cn"] = article["title"]
            continue

        # 已经有 title_cn 则跳过（可能来自 LLM）
        if article.get("title_cn"):
            continue

        # 翻译标题
        try:
            article["title_cn"] = translator.translate(article["title"])
            time.sleep(config.TRANSLATION_DELAY)
        except Exception as e:
            logger.warning(f"Title translation failed: {e}")
            article["title_cn"] = article["title"]

    return articles
