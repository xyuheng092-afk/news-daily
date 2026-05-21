import logging
from difflib import SequenceMatcher

import config

logger = logging.getLogger("cluster")


def _title_similarity(t1: str, t2: str) -> float:
    """计算两个标题的相似度 (0~1)，忽略大小写和常见虚词"""
    # 预处理：去标点、小写
    import re

    def clean(s):
        s = re.sub(r"[^a-zA-Z0-9一-鿿\s]", " ", s.lower())
        # 去掉常见停用词
        for word in ["the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
                      "to", "for", "of", "and", "or", "but", "with", "from", "by",
                      "its", "it", "this", "that", "as", "has", "have", "be", "been"]:
            s = re.sub(rf"\b{word}\b", "", s)
        return " ".join(s.split())

    return SequenceMatcher(None, clean(t1), clean(t2)).ratio()


def cluster_articles(articles: list[dict], threshold: float = None) -> list[dict]:
    """将相似标题的文章聚类，每类选代表，标记热度

    返回新的文章列表，每篇可能带有：
    - cluster_size: 该故事被多少家媒体报道
    - hot_score: 热度分 = 来源数 * 2 + 最高LLM分
    - related_sources: 报道同一故事的其他来源列表
    - is_hot: 是否为热点（3家以上报道）
    """
    if threshold is None:
        threshold = config.CLUSTER_SIMILARITY_THRESHOLD

    n = len(articles)
    if n <= 1:
        for a in articles:
            a["cluster_size"] = 1
            a["hot_score"] = a.get("score", 5)
            a["related_sources"] = []
            a["is_hot"] = False
        return articles

    # 构建相似度图
    clusters = []  # list of cluster dicts
    assigned = set()

    for i in range(n):
        if i in assigned:
            continue
        cluster = [i]
        for j in range(i + 1, n):
            if j in assigned:
                continue
            sim = _title_similarity(articles[i]["title"], articles[j]["title"])
            if sim >= threshold:
                cluster.append(j)
                assigned.add(j)
        assigned.add(i)
        clusters.append(cluster)

    hot_count = sum(
        1 for c in clusters
        if len({articles[idx].get("source", "?") for idx in c}) >= 3
    )
    logger.info(
        f"聚类结果: {n} 篇文章 -> {len(clusters)} 个故事簇, "
        f"{hot_count} 个热点(>=3家不同来源)"
    )

    # 从每个簇选代表
    result = []
    for cluster in clusters:
        # 代表选 LLM 分最高的
        best_idx = max(cluster, key=lambda idx: articles[idx].get("score", 0))
        rep = dict(articles[best_idx])

        sources = list({articles[idx].get("source", "?") for idx in cluster})
        distinct_sources = len(sources)
        cluster_size = len(cluster)
        max_score = max(articles[idx].get("score", 5) for idx in cluster)

        rep["cluster_size"] = cluster_size
        rep["hot_score"] = distinct_sources * 2 + max_score
        rep["related_sources"] = sources
        rep["is_hot"] = distinct_sources >= 3

        if distinct_sources >= 3:
            logger.info(
                f"  热点: \"{rep['title'][:60]}...\" — "
                f"{distinct_sources}家不同来源({cluster_size}篇): {', '.join(sources)}"
            )

        result.append(rep)

    # 按热度分重排序
    result.sort(key=lambda a: -a["hot_score"])

    return result
