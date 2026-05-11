"""汎用ニュース収集エンジン。web3-news-collectorのコードを多テーマ対応に汎用化。"""

import logging
import re
import time
from datetime import datetime, timezone

import feedparser
import requests
from dateutil import parser as dateutil_parser
from django.conf import settings

logger = logging.getLogger(__name__)

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"


# ---- NewsAPI ----------------------------------------------------------------

def collect_newsapi(keywords: str, since: datetime, language: str = "both") -> list[dict]:
    api_key = settings.NEWS_API_KEY
    if not api_key:
        logger.warning("NEWS_API_KEY not set, skipping NewsAPI")
        return []

    from_date = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    langs = []
    if language in ("ja", "both"):
        langs.append(("ja", "domestic"))
    if language in ("en", "both"):
        langs.append(("en", "international"))

    articles = []
    for lang, category in langs:
        params = {
            "q": keywords,
            "language": lang,
            "from": from_date,
            "sortBy": "publishedAt",
            "pageSize": 100,
            "apiKey": api_key,
        }
        try:
            resp = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "ok":
                logger.error("NewsAPI error: %s", data.get("message"))
                continue
            logger.info("NewsAPI lang=%s: %d articles returned", lang, len(data.get("articles", [])))
            for item in data.get("articles", []):
                url = (item.get("url") or "").strip()
                if not url or url == "https://removed.com":
                    continue
                published_at = _parse_iso(item.get("publishedAt", ""))
                if published_at is None or published_at < since:
                    continue
                title = (item.get("title") or "").strip()
                if not title:
                    continue
                articles.append({
                    "title": title,
                    "url": url,
                    "source": (item.get("source") or {}).get("name", "NewsAPI"),
                    "category": category,
                    "published_at": published_at,
                })
        except requests.RequestException as e:
            logger.error("NewsAPI request failed (lang=%s): %s", lang, e)

    return articles


# ---- RSS --------------------------------------------------------------------

def collect_rss_by_keywords(keywords: str, since: datetime, language: str = "both") -> list[dict]:
    """キーワードでRSSフィードをフィルタリングして収集する。"""
    kw_list = [k.strip().lower() for k in re.split(r"\s+OR\s+|\s+AND\s+|\s+", keywords) if k.strip()]

    feeds = []
    if language in ("ja", "both"):
        feeds += _DEFAULT_JA_FEEDS
    if language in ("en", "both"):
        feeds += _DEFAULT_EN_FEEDS

    articles = []
    for feed_info in feeds:
        try:
            feed = feedparser.parse(feed_info["url"], agent="news-collect-solution/1.0")
            if feed.bozo and not feed.entries:
                continue
            for entry in feed.entries:
                published_at = _parse_entry_date(entry)
                if published_at is None or published_at < since:
                    continue
                url = getattr(entry, "link", "").strip()
                title = getattr(entry, "title", "").strip()
                if not url or not title:
                    continue
                if not _matches_keywords(title, kw_list):
                    continue
                articles.append({
                    "title": title,
                    "url": url,
                    "source": feed_info["name"],
                    "category": feed_info["category"],
                    "published_at": published_at,
                })
        except Exception as e:
            logger.error("RSS fetch failed (%s): %s", feed_info["name"], e)

    return articles


# ---- Translation ------------------------------------------------------------

def translate_titles(articles: list[dict]) -> None:
    """海外記事のタイトルを日本語に翻訳（in-place）。"""
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        logger.error("deep-translator not installed")
        return

    for article in articles:
        if article.get("category") != "international":
            continue
        title = article.get("title", "")
        if not title:
            continue
        for attempt in range(3):
            try:
                article["title_ja"] = GoogleTranslator(source="en", target="ja").translate(title[:4500]) or ""
                time.sleep(0.5)
                break
            except Exception as e:
                logger.warning("Translation failed (attempt %d): %s", attempt + 1, e)
                if attempt < 2:
                    time.sleep(15 * (attempt + 1))


# ---- Helpers ----------------------------------------------------------------

def _parse_iso(date_str: str) -> datetime | None:
    try:
        dt = dateutil_parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _parse_entry_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            return datetime(*val[:6], tzinfo=timezone.utc)
    for attr in ("published", "updated"):
        val = getattr(entry, attr, None)
        if val:
            try:
                dt = dateutil_parser.parse(val)
                return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
            except Exception:
                pass
    return None


def _matches_keywords(text: str, kw_list: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in kw_list)


_DEFAULT_JA_FEEDS = [
    {"name": "CoinPost", "url": "https://coinpost.jp/?feed=rss2", "category": "domestic"},
    {"name": "CoinDesk Japan", "url": "https://www.coindeskjapan.com/feed/", "category": "domestic"},
    {"name": "あたらしい経済", "url": "https://www.neweconomy.jp/feed", "category": "domestic"},
]

_DEFAULT_EN_FEEDS = [
    {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "category": "international"},
    {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss", "category": "international"},
    {"name": "Decrypt", "url": "https://decrypt.co/feed", "category": "international"},
    {"name": "The Block", "url": "https://www.theblock.co/rss.xml", "category": "international"},
]
