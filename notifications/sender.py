"""Slack / Teams へのWebhook通知送信。"""

import json
import logging
from datetime import datetime

import requests
import pytz

logger = logging.getLogger(__name__)
JST = pytz.timezone("Asia/Tokyo")


def send_to_channel(channel, theme, articles: list) -> bool:
    if channel.channel_type == "slack":
        return _send_slack(channel.webhook_url, theme, articles)
    elif channel.channel_type == "teams":
        return _send_teams(channel.webhook_url, theme, articles)
    return False


def _build_md_body(theme, articles: list) -> str:
    date_str = datetime.now(JST).strftime("%Y-%m-%d")
    lines = [f"# {theme.name} ニュース {date_str}", ""]

    domestic = [a for a in articles if a.category == "domestic"]
    international = [a for a in articles if a.category == "international"]

    if domestic:
        lines.append("## 国内")
        for a in domestic:
            lines.append(f"- [{a.display_title}]({a.url}) — {a.source}")
        lines.append("")

    if international:
        lines.append("## 海外")
        for a in international:
            lines.append(f"- [{a.display_title}]({a.url}) — {a.source}")
        lines.append("")

    return "\n".join(lines)


def _send_slack(webhook_url: str, theme, articles: list) -> bool:
    date_str = datetime.now(JST).strftime("%Y-%m-%d")
    domestic = [a for a in articles if a.category == "domestic"]
    international = [a for a in articles if a.category == "international"]

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f":newspaper: {theme.name} ニュース {date_str}"},
        },
    ]

    def _section(title, items):
        if not items:
            return
        text = f"*{title}*\n" + "\n".join(f"• <{a.url}|{a.display_title}> — {a.source}" for a in items[:20])
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})

    _section("国内", domestic)
    _section("海外", international)

    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"収集完了: {datetime.now(JST).strftime('%Y-%m-%d %H:%M JST')}"}],
    })

    payload = {
        "text": f"{theme.name} ニュース {date_str} — 国内{len(domestic)}件・海外{len(international)}件",
        "blocks": blocks,
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Slack send failed: %s", e)
        return False


def _send_teams(webhook_url: str, theme, articles: list) -> bool:
    date_str = datetime.now(JST).strftime("%Y-%m-%d")
    domestic = [a for a in articles if a.category == "domestic"]
    international = [a for a in articles if a.category == "international"]

    def _facts(items):
        return [{"name": a.source, "value": f"[{a.display_title}]({a.url})"} for a in items[:20]]

    sections = []
    if domestic:
        sections.append({"activityTitle": "国内", "facts": _facts(domestic)})
    if international:
        sections.append({"activityTitle": "海外", "facts": _facts(international)})

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": f"{theme.name} ニュース {date_str}",
        "sections": sections,
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Teams send failed: %s", e)
        return False
