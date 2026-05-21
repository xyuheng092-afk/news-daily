import json
import logging
import time

import requests

import config

logger = logging.getLogger("llm_filter")

CATEGORY_PRIORITY = {"breaking": 0, "politics": 1, "economy": 2, "tech": 3, "general": 4}

CATEGORY_LABELS = {
    "breaking": "突发",
    "politics": "政治",
    "economy": "经济",
    "tech": "科技",
    "general": "综合",
}

SYSTEM_PROMPT = """你是一个资深新闻编辑，负责筛选和评估全球新闻价值。

对于每篇文章，请完成：
1. **分类**：从 ["breaking","politics","economy","tech","general"] 中选择最合适的一个
   - breaking: 突发重大事件（自然灾害、恐袭、战争爆发、重大事故、名人逝世等）
   - politics: 政治外交（选举、政策、国际关系、立法、政府变动）
   - economy: 经济金融（市场动向、贸易、货币政策、企业重大变动、产业趋势）
   - tech: 科技（AI进展、重大产品发布、科技公司动态、科研突破、网络安全）
   - general: 综合（不属于以上或价值不高的软新闻）
2. **重要性评分** (1-10分)：
   - 8-10分：全球性重大事件，影响数千万人以上
   - 6-7分：国家级重要事件，影响重大
   - 4-5分：有一定新闻价值，值得关注
   - 1-3分：软新闻或局部小事
3. **中文摘要** (50-100字)：提炼核心信息，包含关键数字、人物、事件。中文摘要必须用中文撰写。

严格按照JSON数组格式返回，每个元素为：
{"id": 序号, "category": "分类", "score": 分数, "summary_cn": "中文摘要"}"""


def _build_articles_text(articles: list[dict], start_id: int) -> str:
    lines = []
    for i, a in enumerate(articles):
        lines.append(f"ID {start_id + i}:")
        lines.append(f"  标题: {a['title']}")
        if a.get("summary"):
            lines.append(f"  摘要: {a['summary'][:300]}")
        lines.append(f"  来源: {a.get('source', '')}")
        lines.append("")
    return "\n".join(lines)


def _call_deepseek(articles: list[dict], start_id: int) -> list[dict]:
    """调用 DeepSeek API，返回解析后的结果列表"""
    articles_text = _build_articles_text(articles, start_id)
    user_prompt = f"请评估以下新闻文章：\n\n{articles_text}"

    for attempt in range(config.LLM_MAX_RETRIES):
        try:
            resp = requests.post(
                config.DEEPSEEK_BASE_URL,
                headers={
                    "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config.DEEPSEEK_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data["choices"][0]["message"]["content"].strip()
            return _parse_response(raw, len(articles), start_id)

        except Exception as e:
            logger.warning(f"DeepSeek API 调用失败 (attempt {attempt + 1}): {e}")
            if attempt < config.LLM_MAX_RETRIES - 1:
                time.sleep(2 ** attempt)

    raise RuntimeError("DeepSeek API 多次重试后仍然失败")


def _parse_response(raw: str, count: int, start_id: int) -> list[dict]:
    """解析 LLM 返回的 JSON，容错处理"""
    # 尝试提取 JSON 数组
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(line for line in lines if not line.startswith("```"))

    try:
        results = json.loads(raw)
    except json.JSONDecodeError:
        # 尝试修复：找到第一个 [ 和最后一个 ]
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            results = json.loads(raw[start:end])
        else:
            raise

    if not isinstance(results, list):
        raise ValueError(f"Expected JSON array, got {type(results)}")

    # 确保结果数量匹配
    if len(results) < count:
        logger.warning(
            f"LLM 返回结果不足: 期望 {count}，实际 {len(results)}，补齐为 general"
        )
        for i in range(len(results), count):
            results.append({
                "id": start_id + i,
                "category": "general",
                "score": 3,
                "summary_cn": "",
            })

    # 按 id 排序确保顺序
    results.sort(key=lambda x: x.get("id", 0))

    # 规范字段
    for r in results:
        r["category"] = r.get("category", "general")
        if r["category"] not in CATEGORY_PRIORITY:
            r["category"] = "general"
        try:
            r["score"] = int(r.get("score", 5))
        except (ValueError, TypeError):
            r["score"] = 5
        r["score"] = max(1, min(10, r["score"]))
        r["summary_cn"] = str(r.get("summary_cn", "") or "")

    return results


def llm_classify(articles: list[dict]) -> list[dict]:
    """使用 DeepSeek LLM 对文章进行分类、打分和摘要"""
    if not config.DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY 未设置")

    all_results = []
    batch_size = config.LLM_BATCH_SIZE

    for batch_start in range(0, len(articles), batch_size):
        batch = articles[batch_start:batch_start + batch_size]
        logger.info(
            f"LLM 处理批次 {batch_start // batch_size + 1}: "
            f"{len(batch)} 篇文章 (ID {batch_start}~{batch_start + len(batch) - 1})"
        )

        batch_results = _call_deepseek(batch, batch_start)
        all_results.extend(batch_results)

    # 将 LLM 结果合并到原文章
    for i, article in enumerate(articles):
        if i < len(all_results):
            result = all_results[i]
            article["category"] = result["category"]
            article["score"] = result["score"]
            article["summary_cn"] = result["summary_cn"]
        else:
            article["category"] = "general"
            article["score"] = 3
            article["summary_cn"] = ""

    # 统计
    cats = {}
    for a in articles:
        cats[a["category"]] = cats.get(a["category"], 0) + 1
    avg_score = sum(a.get("score", 0) for a in articles) / max(len(articles), 1)
    logger.info(f"LLM 分类完成: {cats}, 平均分: {avg_score:.1f}")

    return articles


def select_top_llm(articles: list[dict], n: int = None) -> list[dict]:
    """根据 LLM 评分和分类优先级排序选取 TOP N"""
    if n is None:
        n = config.MAX_ARTICLES

    # 过滤掉低分文章
    qualified = [a for a in articles if a.get("score", 0) >= config.MIN_LLM_SCORE]
    dropped = len(articles) - len(qualified)
    if dropped:
        logger.info(f"过滤掉 {dropped} 篇低分文章 (分数 < {config.MIN_LLM_SCORE})")

    # 排序：分类优先级 > LLM分数(降序)
    qualified.sort(
        key=lambda a: (
            CATEGORY_PRIORITY.get(a.get("category", "general"), 99),
            -a.get("score", 0),
        )
    )

    # 来源多样化选取
    selected = []
    source_counts = {}
    for a in qualified:
        if len(selected) >= n:
            break
        src = a.get("source", "Unknown")
        cnt = source_counts.get(src, 0)
        if cnt < max(n // 3, 3):
            selected.append(a)
            source_counts[src] = cnt + 1

    # 补足
    if len(selected) < n:
        for a in qualified:
            if len(selected) >= n:
                break
            if a not in selected:
                selected.append(a)

    return selected[:n]
