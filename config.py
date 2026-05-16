import os
import logging

# --- SMTP 邮件配置（从环境变量读取）---
# 使用 "or" 防止 Secrets 设为空字符串时覆盖默认值
SMTP_SERVER = os.environ.get("SMTP_SERVER") or "smtp.qq.com"
SMTP_PORT = int(os.environ.get("SMTP_PORT") or "465")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL") or ""
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD") or ""
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL") or ""

# --- RSS 源配置 ---
RSS_SOURCES = {
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
    "CGTN": [
        "https://www.cgtn.com/subscribe/rss/section/latest.xml",
    ],
}

# --- 筛选关键词 ---
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
}

# --- 其他配置 ---
DATA_DIR = "data"
SENT_URLS_FILE = os.path.join(DATA_DIR, "sent_urls.json")
RETENTION_DAYS = 30
MAX_ARTICLES = 10
REQUEST_TIMEOUT = 15
TRANSLATION_DELAY = 0.5
MAX_SUMMARY_LENGTH = 150
USER_AGENT = (
    "Mozilla/5.0 (compatible; NewsBot/1.0; +https://github.com/news-daily)"
)

# --- 日志配置 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
