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

def collect_rss_from_urls(feed_urls: list[str], keywords: str, since: datetime) -> list[dict]:
    """ユーザー指定のRSSフィードからキーワードでフィルタリングして収集する。"""
    if not feed_urls:
        return []

    # AND/OR を解析してフィルタリング条件を構築
    must_terms, any_terms = _parse_keyword_logic(keywords)
    articles = []

    for url in feed_urls:
        try:
            feed = feedparser.parse(url, agent="news-collect-solution/1.0")
            source_name = getattr(feed.feed, "title", url)
            if feed.bozo and not feed.entries:
                logger.warning("RSS parse error for %s", url)
                continue
            for entry in feed.entries:
                published_at = _parse_entry_date(entry)
                if published_at is None or published_at < since:
                    continue
                article_url = getattr(entry, "link", "").strip()
                title = getattr(entry, "title", "").strip()
                if not article_url or not title:
                    continue
                if not _matches_keyword_logic(title, must_terms, any_terms):
                    continue
                articles.append({
                    "title": title,
                    "url": article_url,
                    "source": source_name,
                    "category": "domestic",
                    "published_at": published_at,
                })
        except Exception as e:
            logger.error("RSS fetch failed (%s): %s", url, e)

    logger.info("User RSS feeds: %d articles from %d feeds", len(articles), len(feed_urls))
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


def _parse_keyword_logic(keywords: str) -> tuple[list[str], list[str]]:
    """
    キーワード文字列を解析してAND条件とOR条件に分ける。
    例: "Tottenham AND (Spurs OR Premier)" → must=["tottenham"], any=["spurs","premier"]
    スペース区切りはOR扱い。
    """
    # AND で分割 → すべて含む必須語
    must_terms = []
    any_terms = []
    parts = re.split(r'\s+AND\s+', keywords, flags=re.IGNORECASE)
    for part in parts:
        # OR で分割 → どれか含む語
        or_parts = [p.strip().strip('()').lower() for p in re.split(r'\s+OR\s+|\s+', part) if p.strip()]
        if len(or_parts) == 1:
            must_terms.append(or_parts[0])
        else:
            any_terms.extend(or_parts)
    return must_terms, any_terms


def _matches_keyword_logic(text: str, must_terms: list[str], any_terms: list[str]) -> bool:
    text_lower = text.lower()
    if must_terms and not all(t in text_lower for t in must_terms):
        return False
    if any_terms and not any(t in text_lower for t in any_terms):
        return False
    if not must_terms and not any_terms:
        return True
    return True
