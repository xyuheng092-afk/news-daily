import os
import logging

# --- SMTP 邮件配置（从环境变量读取）---
SMTP_SERVER = os.environ.get("SMTP_SERVER") or "smtp.qq.com"
SMTP_PORT = int(os.environ.get("SMTP_PORT") or "465")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL") or ""
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD") or ""
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL") or ""

# --- DeepSeek API 配置 ---
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") or ""
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
LLM_MAX_RETRIES = 3
LLM_BATCH_SIZE = 20

# --- RSS 源配置 ---
RSS_SOURCES = {
    # 原有源
    "CNN": [
        "http://rss.cnn.com/rss/cnn_topstories.rss",
        "http://rss.cnn.com/rss/money_latest.rss",
    ],
    "FOX": [
        "https://feeds.foxnews.com/foxnews/latest",
        "https://feeds.foxnews.com/foxnews/politics",
    ],
    "NYT": [
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
    ],
    "BBC": [
        "http://feeds.bbci.co.uk/news/rss.xml",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "http://feeds.bbci.co.uk/news/business/rss.xml",
        "http://feeds.bbci.co.uk/news/politics/rss.xml",
    ],
    # 科技
    "HackerNews": [
        "https://hnrss.org/frontpage",
    ],
    "TechCrunch": [
        "https://techcrunch.com/feed/",
    ],
    "TheVerge": [
        "https://www.theverge.com/rss/index.xml",
    ],
    "ArsTechnica": [
        "https://feeds.arstechnica.com/arstechnica/index",
    ],
    # 财经
    "Reuters": [
        "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
        "https://www.reutersagency.com/feed/?best-topics=politics&post_type=best",
    ],
    "CNBC": [
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    ],
    # 政治/国际
    "APNews": [
        "https://www.apnews.com/apf-topnews",
    ],
    "Politico": [
        "https://rss.politico.com/politics-news.xml",
    ],
    "TheGuardian": [
        "https://www.theguardian.com/world/rss",
    ],
    "AlJazeera": [
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],
    # 中文源
    "36Kr": [
        "https://36kr.com/feed",
    ],
    "Huxiu": [
        "https://www.huxiu.com/rss/0.xml",
    ],
    "ThePaper": [
        "https://www.thepaper.cn/rss",
    ],
}

# --- 网页爬取源 ---
WEB_SOURCES = {
    "CCTV": {
        "url": "https://news.cctv.com/",
        "item_selector": "div.list_con a, div.list a, div.image_list a, div.text_content a",
        "max_items": 30,
    },
}

# --- 中文源（无需翻译，LLM 摘要除外）---
CHINESE_SOURCES = {
    "CCTV", "36Kr", "Huxiu", "ThePaper",
}

# --- 分类关键词（LLM 不可用时的 fallback）---
KEYWORDS = {
    "breaking": [
        "breaking", "urgent", "emergency", "crisis", "disaster",
        "war", "attack", "explosion", "earthquake", "crash",
        "shooting", "death", "killed", "evacuat", "declaration",
        "resign", "impeach", "coup", "invasion", "ceasefire",
        "突发", "紧急", "重大",
    ],
    "politics": [
        "president", "election", "congress", "senate", "vote",
        "democrat", "republican", "government", "policy", "law",
        "supreme court", "bill", "administration", "diplomat",
        "sanction", "treaty", "NATO", "UN", "United Nations",
        "白宫", "选举", "国会", "外交", "制裁", "谈判",
        "summit", "minister", "parliament", "cabinet", "referendum",
    ],
    "economy": [
        "stock", "market", "economy", "inflation", "GDP",
        "trade", "tariff", "interest rate", "Fed", "Federal Reserve",
        "recession", "debt", "bank", "crypto", "bitcoin",
        "oil price", "unemploy", "失业", "股市", "经济",
        "invest", "Wall Street", "Dow", "S&P", "Nasdaq",
        "export", "import", "supply chain", "commodit",
    ],
    "tech": [
        "AI", "artificial intelligence", "chatgpt", "openai",
        "google", "apple", "microsoft", "meta", "amazon",
        "tesla", "spacex", "chip", "semiconductor", "nvidia",
        "robot", "startup", "ipo", "software", "cyber",
        "quantum", "electric vehicle", "EV", "battery",
        "人工智能", "芯片", "机器人", "自动驾驶",
        "iphone", "android", "app", "launch", "update",
    ],
}

# --- 其他配置 ---
DATA_DIR = "data"
SENT_URLS_FILE = os.path.join(DATA_DIR, "sent_urls.json")
RETENTION_DAYS = 30
MAX_ARTICLES = 15
MIN_LLM_SCORE = 4
CLUSTER_SIMILARITY_THRESHOLD = 0.55
REQUEST_TIMEOUT = 15
TRANSLATION_DELAY = 0.5
MAX_SUMMARY_LENGTH = 120
USER_AGENT = (
    "Mozilla/5.0 (compatible; NewsBot/1.0; +https://github.com/news-daily)"
)

# --- 日志配置 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
