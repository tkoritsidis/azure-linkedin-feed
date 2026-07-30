import feedparser
import html
import json
import re

from datetime import datetime, timezone


# ============================================================
# Configuration
# ============================================================

RSS_URL = (
    "https://www.microsoft.com/"
    "releasecommunications/api/v2/azure/rss"
)

MAX_UPDATES = 5

PRIORITY_KEYWORDS = {
    # Core focus areas
    "azure arc": 20,
    "azure local": 20,
    "azure virtual desktop": 20,
    "avd": 18,
    "hybrid cloud": 17,
    "hybrid": 12,
    "edge": 8,
    "migration": 14,
    "landing zone": 15,

    # Compute and infrastructure
    "virtual machine": 11,
    "virtual machines": 11,
    "compute": 8,
    "storage": 9,
    "disk": 8,
    "premium ssd": 10,
    "backup": 12,
    "site recovery": 15,
    "disaster recovery": 15,
    "resiliency": 14,
    "availability zone": 12,

    # Networking
    "network": 10,
    "networking": 11,
    "expressroute": 16,
    "vpn": 11,
    "nat gateway": 13,
    "load balancer": 10,
    "application gateway": 11,
    "firewall": 13,
    "private link": 12,
    "dns": 9,
    "ipv4": 7,
    "ipv6": 9,

    # Security, identity and governance
    "security": 12,
    "defender": 14,
    "sentinel": 13,
    "identity": 11,
    "entra": 13,
    "policy": 10,
    "governance": 12,
    "compliance": 10,
    "enclave": 10,
    "confidential": 9,

    # Containers and platform
    "kubernetes": 9,
    "aks": 10,
    "container": 8,
    "gateway api": 9,

    # AI
    "azure ai": 10,
    "artificial intelligence": 9,
    "openai": 10,
    "ai": 4,

    # General platform
    "region": 6,
    "datacenter": 8,
    "monitor": 8,
    "management": 8,
    "automation": 8,
}

RELEASE_KEYWORDS = {
    "generally available": 10,
    "general availability": 10,
    "[launched]": 9,
    "launched": 8,
    "public preview": 5,
    "in preview": 4,
    "preview": 3,
}


# ============================================================
# Text helpers
# ============================================================

def clean_html(raw_text):
    """
    Convert RSS HTML content into clean plain text.
    """

    if not raw_text:
        return ""

    text = html.unescape(str(raw_text))

    text = re.sub(
        r"<\s*(br|p|div|li)\b[^>]*>",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def shorten_text(text, maximum_length=360):
    """
    Shorten text without cutting the final word.
    """

    text = clean_html(text)

    if len(text) <= maximum_length:
        return text

    shortened = text[:maximum_length].rsplit(" ", 1)[0]

    return shortened.rstrip(".,;:") + "..."


def get_item_summary(item):
    """
    Get the best available description from an RSS item.
    """

    summary = item.get("summary", "")

    if not summary:
        summary = item.get("description", "")

    if not summary and item.get("content"):
        try:
            summary = item["content"][0].get(
                "value",
                "",
            )
        except (
            IndexError,
            AttributeError,
            TypeError,
            KeyError,
        ):
            summary = ""

    return clean_html(summary)


# ============================================================
# Relevance scoring
# ============================================================

def calculate_relevance_score(item):
    """
    Assign a deterministic relevance score.

    This prioritizes updates related to Azure Infrastructure,
    Hybrid Cloud, Azure Arc, Azure Local, AVD, networking,
    security, governance, migration and resiliency.
    """

    title = clean_html(
        item.get(
            "title",
            "",
        )
    )

    summary = get_item_summary(item)

    title_lower = title.lower()

    searchable_text = (
        f"{title} {summary}"
    ).lower()

    score = 0
    matched_topics = []

    for keyword, weight in PRIORITY_KEYWORDS.items():
        if keyword in searchable_text:
            score += weight
            matched_topics.append(keyword)

        # A title match is more important.
        if keyword in title_lower:
            score += round(weight * 0.5)

    for keyword, weight in RELEASE_KEYWORDS.items():
        if keyword in searchable_text:
            score += weight

    return score, sorted(set(matched_topics))


def get_important_updates(feed, maximum=5):
    """
    Score RSS entries and select the most relevant unique updates.
    """

    scored_items = []

    for position, item in enumerate(feed.entries):
        title = clean_html(
            item.get(
                "title",
                "Azure Update",
            )
        )

        if not title:
            continue

        score, matched_topics = (
            calculate_relevance_score(item)
        )

        scored_items.append(
            {
                "item": item,
                "title": title,
                "score": score,
                "matched_topics": matched_topics,
                "feed_position": position,
            }
        )

    # Higher score first.
    # When scores are equal, retain RSS order.
    scored
