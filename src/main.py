import logging
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from src.fetcher import fetch_all_sources  # noqa: E402
from src.filter import classify_and_score, select_top  # noqa: E402
from src.dedup import filter_duplicates, save_sent_hashes  # noqa: E402
from src.translator import translate_titles  # noqa: E402
from src.cluster import cluster_articles  # noqa: E402
from src.mailer import send_email  # noqa: E402

logger = logging.getLogger("main")


def main():
    try:
        _run()
    except Exception:
        logger.error("未捕获的异常:\n" + traceback.format_exc())
        sys.exit(1)


def _run_llm_pipeline(articles: list[dict]):
    """LLM 模式：分类 + 打分 + 摘要 + 聚类"""
    from src.llm_filter import llm_classify, select_top_llm

    # 3. LLM 分类打分 + 摘要
    logger.info("[3/7] 正在 LLM 智能分类打分...")
    articles = llm_classify(articles)

    # 4. 跨源聚类
    logger.info("[4/7] 正在跨源故事聚类...")
    articles = cluster_articles(articles)

    # 5. 排序选取
    logger.info("[5/7] 正在排序选取 TOP {} ...".format(config.MAX_ARTICLES))
    top = select_top_llm(articles, config.MAX_ARTICLES)
    logger.info(f"  -> 选取 {len(top)} 篇精选文章")

    return top


def _run_keyword_pipeline(articles: list[dict]):
    """Fallback 模式：关键词分类 + 打分"""
    # 3. 关键词分类打分
    logger.info("[3/7] 正在关键词分类打分...")
    articles = [classify_and_score(a) for a in articles]
    cats = {}
    for a in articles:
        cats[a["category"]] = cats.get(a["category"], 0) + 1
    logger.info(f"  -> 分类统计: {cats}")

    # 4. 跨源聚类（无 LLM 分数，用关键词分数替代）
    logger.info("[4/7] 正在跨源故事聚类...")
    articles = cluster_articles(articles)

    # 5. 排序选取
    logger.info("[5/7] 正在排序选取 TOP {} ...".format(config.MAX_ARTICLES))
    top = select_top(articles, config.MAX_ARTICLES)
    logger.info(f"  -> 选取 {len(top)} 篇精选文章")

    return top


def _run():
    logger.info("=== 每日新闻推送开始 ===")

    # 检测 LLM 是否可用
    use_llm = bool(config.DEEPSEEK_API_KEY)
    if use_llm:
        logger.info("LLM 模式: DeepSeek API 已配置")
    else:
        logger.warning("LLM 模式未启用: DEEPSEEK_API_KEY 未设置，将使用关键词模式")

    # 1. 抓取
    logger.info("[1/7] 正在抓取新闻 RSS...")
    articles = fetch_all_sources()
    logger.info(f"  -> 共抓取 {len(articles)} 篇文章")

    if not articles:
        logger.error("未抓取到任何文章，请检查网络或 RSS 源是否可用")
        sys.exit(1)

    # 2. 去重
    logger.info("[2/7] 正在去重检查...")
    unique, new_hashes = filter_duplicates(articles)
    logger.info(f"  -> 去重后剩余 {len(unique)} 篇")

    if not unique:
        logger.warning("所有文章均为已发送过的重复内容，今日无新文章")
        return

    # 3~5. 筛选排序（LLM 或关键词）
    if use_llm:
        try:
            top = _run_llm_pipeline(unique)
        except Exception as e:
            logger.error(f"LLM 流水线失败: {e}，回退到关键词模式")
            top = _run_keyword_pipeline(unique)
    else:
        top = _run_keyword_pipeline(unique)

    # 6. 翻译标题（中文源跳过，英文源翻译标题）
    logger.info("[6/7] 正在翻译标题...")
    top = translate_titles(top)
    logger.info("  -> 标题翻译完成")

    # 7. 发送邮件
    logger.info("[7/7] 正在发送邮件...")
    send_email(top)
    logger.info("  -> 邮件发送成功")

    # 保存去重记录
    save_sent_hashes(new_hashes)
    logger.info("  -> 去重记录已更新")

    # 统计输出
    for i, a in enumerate(top, 1):
        hot_info = f" 🔥x{a['cluster_size']}" if a.get("is_hot") else ""
        logger.info(
            f"  [{i}] [{a.get('category', '?')}] [{a['source']}] "
            f"得分{a.get('score', '?')}{hot_info} {a.get('title_cn', a['title'])}"
        )

    logger.info("=== 每日新闻推送完成 ===")


if __name__ == "__main__":
    main()
