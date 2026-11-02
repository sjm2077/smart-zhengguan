"""学院官网新闻增量爬虫 —— 定时抓取学院官网新闻，入库 zhhengguan_research。

用法:
    python scraper_guanwang.py              # 跑一次
    python scraper_guanwang.py --daemon     # 定时模式（APScheduler，每 6 小时）
    python scraper_guanwang.py --once       # 只跑一次

依赖: requests, beautifulsoup4, django, pymysql

数据写入 zhhengguan_research.guanwang_news 表（首次运行自动建表）。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ---- 路径 & 配置 ----
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
REPO_ROOT = SCRIPT_DIR.parent

# 复用科研系统 Django 配置
RESEARCH_SITE = REPO_ROOT / "research_system"
sys.path.insert(0, str(RESEARCH_SITE / "research_system"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "research_system.settings")

import django  # noqa: E402
django.setup()

from django.db import connection  # noqa: E402

# ---- 目标网站 ----
BASE_URL = "http://www.pspa.sdu.edu.cn"
LIST_URL = BASE_URL + "/info/1030.htm"  # 学院新闻列表页
CSV_PATH = DATA_DIR / "Guanwang_papers_full_sum.csv"

# ---- 日志 ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("guanwang")


def ensure_table():
    """首次运行自动建表。"""
    with connection.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS guanwang_news (
                id INT AUTO_INCREMENT PRIMARY KEY,
                url_hash VARCHAR(32) NOT NULL UNIQUE,
                title VARCHAR(512) NOT NULL,
                publish_date VARCHAR(32),
                url VARCHAR(512),
                fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_date (publish_date),
                INDEX idx_hash (url_hash)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )


def url_hash(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def fetch_list_page(page_url: str) -> list[dict]:
    """抓取学院新闻列表页，返回 [{title, date, url}, ...]。"""
    import requests
    from bs4 import BeautifulSoup

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    try:
        resp = requests.get(page_url, headers=headers, timeout=15)
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as exc:
        log.warning("列表页抓取失败 %s: %s", page_url, exc)
        return []

    items = []
    for a_tag in soup.select('a[href*="/info/1030/"]'):
        href = a_tag.get("href", "")
        title = a_tag.get_text(strip=True)
        if not href or not title:
            continue
        full_url = href if href.startswith("http") else BASE_URL + href.lstrip(".")
        items.append({"title": title, "url": full_url})

    # 提取日期（在同一页面的 li 或 span 里）
    for li in soup.select("li"):
        date_span = li.select_one("span, .date, .time")
        if date_span:
            link = li.select_one('a[href*="/info/1030/"]')
            if link:
                href = link.get("href", "")
                date_text = date_span.get_text(strip=True)
                for it in items:
                    if it["url"].endswith(href.lstrip(".").lstrip("/")):
                        it["date"] = date_text.replace("年", "/").replace("月", "/").replace("日", "")[:10]

    return items


def fetch_csv_fallback() -> list[dict]:
    """如果官网不可达，从已有 CSV 加载作为兜底。"""
    if not CSV_PATH.exists():
        return []
    items = []
    try:
        with open(CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    items.append({
                        "title": row[0].strip(),
                        "date": row[1].strip(),
                        "url": BASE_URL + row[2].strip().replace("..", ""),
                    })
    except Exception as exc:
        log.warning("CSV 兜底读取失败: %s", exc)
    return items


def upsert_items(items: list[dict]) -> int:
    """增量入库，返回新插入条数。"""
    if not items:
        return 0
    rows = []
    for it in items:
        u = it.get("url", "")
        rows.append((
            url_hash(u),
            it.get("title", "")[:500],
            it.get("date", ""),
            u[:500],
        ))
    with connection.cursor() as cur:
        cur.executemany(
            """
            INSERT IGNORE INTO guanwang_news (url_hash, title, publish_date, url)
            VALUES (%s, %s, %s, %s)
            """,
            rows,
        )
        inserted = cur.rowcount
    log.info("入库完成：共 %d 条，新插入 %d 条", len(rows), inserted)
    return inserted


def run_once():
    log.info("=== 学院官网新闻爬虫开始 ===")
    ensure_table()

    # 1) 尝试官网
    items = fetch_list_page(LIST_URL)

    # 2) 官网不可达时用 CSV 兜底
    if not items:
        log.info("官网列表为空，使用已有 CSV 兜底")
        items = fetch_csv_fallback()

    log.info("抓取到 %d 条", len(items))
    inserted = upsert_items(items)
    log.info("=== 爬虫完成，新插入 %d 条 ===", inserted)
    return inserted


def run_daemon():
    """APScheduler 定时模式：每 6 小时跑一次。"""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
    except ImportError:
        log.error("APScheduler 未安装，先 pip install APScheduler")
        sys.exit(1)

    scheduler = BlockingScheduler()
    scheduler.add_job(run_once, "interval", hours=6, id="guanwang_crawler")
    log.info("定时爬虫启动，每 6 小时执行一次。按 Ctrl+C 退出。")
    run_once()  # 启动先跑一次
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("定时爬虫退出")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="学院官网新闻爬虫")
    parser.add_argument("--daemon", action="store_true", help="定时模式（每 6 小时）")
    parser.add_argument("--once", action="store_true", help="只跑一次")
    args = parser.parse_args()

    if args.daemon:
        run_daemon()
    else:
        run_once()
