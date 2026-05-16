# 每日新闻推送

每天自动从 CNN、FOX News、纽约时报、CGTN 抓取新闻，筛选经济/政治/突发类要闻，翻译成中文，通过邮件推送 10 条精选新闻。

## 功能

- RSS 自动抓取 4 大新闻源（7 个 Feed）
- 中英文关键词智能分类（突发 / 政治 / 经济）
- Google Translate 免费翻译为中文
- URL 去重 + 30 天自动清理
- 精美 HTML 邮件，适配手机
- GitHub Actions 每天北京时间 21:00 自动运行

## 部署步骤

### 1. Fork 或创建仓库

将代码推送到你的 GitHub 仓库。

### 2. 设置 Secrets

在仓库 Settings → Secrets and variables → Actions 中添加：

| Secret | 说明 | 示例 |
|--------|------|------|
| `SMTP_SERVER` | SMTP 服务器 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `465` |
| `SENDER_EMAIL` | 发件邮箱 | `you@qq.com` |
| `SENDER_PASSWORD` | 邮箱授权码 | `abcdefgh` |
| `RECIPIENT_EMAIL` | 收件邮箱 | `you@qq.com` |

### 3. 启用 Actions

在 Actions 页面启用 workflows，手动触发 `Daily News Push` 测试。

## 本地运行

```bash
pip install -r requirements.txt

# 设置环境变量（Windows PowerShell）
$env:SMTP_SERVER="smtp.qq.com"
$env:SMTP_PORT="465"
$env:SENDER_EMAIL="you@qq.com"
$env:SENDER_PASSWORD="your-auth-code"
$env:RECIPIENT_EMAIL="you@qq.com"

python -m src.main
```

## 项目结构

```
├── .github/workflows/daily-news.yml  # 定时任务
├── src/
│   ├── main.py        # 主入口
│   ├── fetcher.py     # RSS 抓取
│   ├── filter.py      # 筛选排序
│   ├── translator.py  # 翻译
│   ├── dedup.py       # 去重
│   └── mailer.py      # 邮件发送
├── config.py           # 配置
├── requirements.txt
└── data/sent_urls.json # 去重记录
```
