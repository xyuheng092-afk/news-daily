import logging
import sys

import config
from src.fetcher import fetch_all_sources
from src.filter import classify_and_score, select_top
from src.dedup import filter_duplicates, save_sent_hashes
from src.translator import translate_articles
from src.mailer import send_email

logger = logging.getLogger("main")


def main():
    logger.info("=== 每日新闻推送开始 ===")

    # 1. 抓取
    logger.info("[1/6] 正在抓取新闻 RSS...")
    articles = fetch_all_sources(config.RSS_SOURCES)
    logger.info(f"  -> 共抓取 {len(articles)} 篇文章")

    if not articles:
        logger.error("未抓取到任何文章，请检查网络或 RSS 源是否可用")
        sys.exit(1)

    # 2. 分类打分
    logger.info("[2/6] 正在分类打分...")
    articles = [classify_and_score(a) for a in articles]
    cats = {}
    for a in articles:
        cats[a["category"]] = cats.get(a["category"], 0) + 1
    logger.info(f"  -> 分类统计: {cats}")

    # 3. 去重
    logger.info("[3/6] 正在去重检查...")
    unique, new_hashes = filter_duplicates(articles)
    logger.info(f"  -> 去重后剩余 {len(unique)} 篇")

    if not unique:
        logger.warning("所有文章均为已发送过的重复内容，今日无新文章")
        sys.exit(0)

    # 4. 排序选取
    logger.info("[4/6] 正在排序选取 TOP {} ...".format(config.MAX_ARTICLES))
    top = select_top(unique, config.MAX_ARTICLES)
    logger.info(f"  -> 选取 {len(top)} 篇精选文章")

    # 5. 翻译
    logger.info("[5/6] 正在翻译...")
    top = translate_articles(top)
    logger.info("  -> 翻译完成")

    # 6. 发送邮件
    logger.info("[6/6] 正在发送邮件...")
    send_email(top)
    logger.info("  -> 邮件发送成功")

    # 7. 邮件发送成功后保存去重记录
    save_sent_hashes(new_hashes)
    logger.info("  -> 去重记录已更新")

    # 统计输出
    for i, a in enumerate(top, 1):
        logger.info(
            f"  [{i}] [{a.get('category', '?')}] [{a['source']}] {a.get('title_cn', a['title'])}"
        )

    logger.info("=== 每日新闻推送完成 ===")


if __name__ == "__main__":
    main()
