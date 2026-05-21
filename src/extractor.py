import logging

import requests
import trafilatura

import config

logger = logging.getLogger("extractor")

TRANSLATE_PROMPT = """你是一个专业新闻翻译和编辑。请将以下英文新闻内容翻译并改写为流畅的中文新闻报道。

要求：
1. 完整传达原文的所有关键信息（人物、事件、数据、时间、地点）
2. 中文表达自然流畅，符合新闻阅读习惯
3. 保留原文的重要引语和数据
4. 篇幅适中，不过度冗长（300-800字）
5. 不要添加原文没有的信息

请直接输出中文新闻内容："""


def extract_content(url: str) -> str:
    """从 URL 提取文章正文"""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": config.USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            logger.warning(f"HTTP {resp.status_code} for {url[:80]}")
            return ""

        content = trafilatura.extract(
            resp.text,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        if content:
            # 限制长度，避免 token 过多
            return content.strip()[:4000]
        else:
            logger.warning(f"trafilatura 未能提取内容: {url[:80]}")
            return ""

    except Exception as e:
        logger.warning(f"内容提取失败 {url[:80]}: {e}")
        return ""


def translate_full_content(title: str, content: str) -> str:
    """使用 DeepSeek 将英文全文翻译为中文新闻"""
    import config as cfg

    if not cfg.DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY 未设置")

    text = f"标题：{title}\n\n原文：\n{content}"
    if len(text) > 5000:
        text = text[:5000]

    for attempt in range(cfg.LLM_MAX_RETRIES):
        try:
            resp = requests.post(
                cfg.DEEPSEEK_BASE_URL,
                headers={
                    "Authorization": f"Bearer {cfg.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": cfg.DEEPSEEK_MODEL,
                    "messages": [
                        {"role": "system", "content": TRANSLATE_PROMPT},
                        {"role": "user", "content": text},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2048,
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

        except Exception as e:
            logger.warning(f"全文翻译失败 (attempt {attempt + 1}): {e}")
            if attempt < cfg.LLM_MAX_RETRIES - 1:
                import time
                time.sleep(2 ** attempt)

    raise RuntimeError("全文翻译多次重试后失败")
