import logging

import config

logger = logging.getLogger("filter")

CATEGORY_PRIORITY = {"breaking": 0, "politics": 1, "economy": 2, "general": 3}

CATEGORY_LABELS = {
    "breaking": "突发",
    "politics": "政治",
    "economy": "经济",
    "general": "综合",
}


def classify_and_score(article: dict, keywords: dict = None) -> dict:
    """对文章进行关键词匹配，返回带 category 和 score 的文章"""
    if keywords is None:
        keywords = config.KEYWORDS

    text = (article["title"] + " " + article.get("summary", "")).lower()
    scores = {cat: 0 for cat in keywords}

    for category, words in keywords.items():
        scores[category] = sum(1 for w in words if w.lower() in text)

    primary = max(scores, key=scores.get)
    article["category"] = primary if scores[primary] > 0 else "general"
    article["score"] = sum(scores.values())
    return article


def select_top(articles: list[dict], n: int = None) -> list[dict]:
    """排序并选取 TOP N 篇文章"""
    if n is None:
        n = config.MAX_ARTICLES

    # 排序：分类优先级 > 得分(降序) > 发布时间(降序)
    articles.sort(
        key=lambda a: (
            CATEGORY_PRIORITY.get(a.get("category", "general"), 99),
            -a.get("score", 0),
        )
    )

    # 取前 N 篇，同时尽量保证来源多样化
    selected = []
    source_counts = {}

    for a in articles:
        if len(selected) >= n:
            break
        src = a.get("source", "Unknown")
        cnt = source_counts.get(src, 0)
        # 同一来源最多不超过一半
        if cnt < max(n // 3, 2):
            selected.append(a)
            source_counts[src] = cnt + 1

    # 如果还没凑够 N 篇，放宽来源限制再补
    if len(selected) < n:
        for a in articles:
            if len(selected) >= n:
                break
            if a not in selected:
                selected.append(a)

    return selected[:n]
