import feedparser
import html
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


# ============================================================
# Configuration
# ============================================================

RSS_URL = "https://www.microsoft.com/releasecommunications/api/v2/azure/rss"
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
    """Convert RSS HTML content into clean plain text."""
    if not raw_text:
        return ""

    text = html.unescape(str(raw_text))
    text = re.sub(r"<\s*(br|p|div|li)\b[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def shorten_text(text, maximum_length=360):
    """Shorten text without cutting the final word."""
    text = clean_html(text)
    if len(text) <= maximum_length:
        return text

    shortened = text[:maximum_length].rsplit(" ", 1)[0]
    return shortened.rstrip(".,;:") + "..."


def get_item_summary(item):
    """Get the best available description from an RSS item."""
    summary = item.get("summary", "") or item.get("description", "")

    if not summary and item.get("content"):
        try:
            summary = item["content"][0].get("value", "")
        except (IndexError, AttributeError, TypeError, KeyError):
            summary = ""

    return clean_html(summary)


def get_published_datetime(item):
    """Return a timezone-aware publication datetime when available."""
    for key in ("published", "updated"):
        value = item.get(key)
        if value:
            try:
                dt = parsedate_to_datetime(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except (TypeError, ValueError, OverflowError):
                pass

    return datetime.now(timezone.utc)


# ============================================================
# Relevance scoring
# ============================================================

def calculate_relevance_score(item):
    """Assign a deterministic relevance score."""
    title = clean_html(item.get("title", ""))
    summary = get_item_summary(item)
    title_lower = title.lower()
    searchable_text = f"{title} {summary}".lower()

    score = 0
    matched_topics = []

    for keyword, weight in PRIORITY_KEYWORDS.items():
        if keyword in searchable_text:
            score += weight
            matched_topics.append(keyword)
        if keyword in title_lower:
            score += round(weight * 0.5)

    for keyword, weight in RELEASE_KEYWORDS.items():
        if keyword in searchable_text:
            score += weight

    return score, sorted(set(matched_topics))


def get_important_updates(feed, maximum=5):
    """Score RSS entries and select the most relevant unique updates."""
    scored_items = []

    for position, item in enumerate(feed.entries):
        title = clean_html(item.get("title", "Azure Update"))
        if not title:
            continue

        score, matched_topics = calculate_relevance_score(item)
        scored_items.append(
            {
                "item": item,
                "title": title,
                "score": score,
                "matched_topics": matched_topics,
                "feed_position": position,
                "published": get_published_datetime(item),
            }
        )

    scored_items.sort(
        key=lambda result: (
            -result["score"],
            -result["published"].timestamp(),
            result["feed_position"],
        )
    )

    selected = []
    seen_titles = set()

    for result in scored_items:
        normalized_title = re.sub(r"\W+", " ", result["title"].lower()).strip()
        if normalized_title in seen_titles:
            continue

        seen_titles.add(normalized_title)
        selected.append(result)

        if len(selected) >= maximum:
            break

    return selected


# ============================================================
# Executive content generation
# ============================================================

def infer_release_status(title, summary):
    text = f"{title} {summary}".lower()
    if "generally available" in text or "general availability" in text or "[launched]" in text:
        return "Generally Available"
    if "public preview" in text or "in preview" in text or "[in preview]" in text:
        return "Public Preview"
    if "retire" in text or "deprecated" in text:
        return "Retirement / Deprecation"
    return "Azure Update"


def create_executive_takeaway(result):
    """Create a short CSA-oriented interpretation using only RSS content."""
    item = result["item"]
    title = result["title"]
    summary = get_item_summary(item)
    topics = result["matched_topics"]

    if topics:
        topic_text = ", ".join(topics[:3])
        return (
            f"CSA perspective: Review potential relevance for {topic_text}. "
            "Validate regional availability, prerequisites, security impact, "
            "operational readiness and cost before production adoption."
        )

    return (
        "CSA perspective: Assess customer relevance, regional availability, "
        "dependencies, governance, security, operations and cost before adoption."
    )


def build_post(selected_updates):
    """Build the text published to linkedin_post.txt and displayed on the site."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        "🚀 Azure Executive Update",
        "",
        f"Date: {today}",
        "",
        "The most relevant Azure platform updates for infrastructure, hybrid cloud, "
        "security, networking and operations:",
        "",
    ]

    for number, result in enumerate(selected_updates, start=1):
        item = result["item"]
        title = result["title"]
        summary = shorten_text(get_item_summary(item), 320)
        link = item.get("link", "").strip()
        status = infer_release_status(title, summary)

        lines.append(f"{number}. {title}")
        lines.append(f"Status: {status}")
        if summary:
            lines.append(f"What changed: {summary}")
        lines.append(create_executive_takeaway(result))
        if link:
            lines.append(f"Source: {link}")
        lines.append("")

    lines.extend(
        [
            "Executive takeaway:",
            "Prioritize updates that reduce operational risk, strengthen resiliency, "
            "improve security posture or simplify hybrid-cloud management. Preview "
            "features should be validated in a controlled environment before production use.",
            "",
            "#Azure #MicrosoftAzure #AzureArchitecture #HybridCloud "
            "#CloudSecurity #AzureMVP",
        ]
    )

    return "\n".join(lines).strip() + "\n"


# ============================================================
# Output files
# ============================================================

def write_json_file(selected_updates):
    """Create structured content for future manual or semi-automatic selection."""
    linkedin_input = []

    for result in selected_updates:
        item = result["item"]
        linkedin_input.append(
            {
                "selected": False,
                "title": result["title"],
                "summary": get_item_summary(item),
                "link": item.get("link", ""),
                "score": result["score"],
                "matched_topics": result["matched_topics"],
                "published_utc": result["published"].isoformat(),
            }
        )

    with open("azure_updates.json", "w", encoding="utf-8") as output_file:
        json.dump(linkedin_input, output_file, indent=2, ensure_ascii=False)

    print("Created: azure_updates.json")


def write_post_file(selected_updates):
    """Create the plain-text post consumed by azure-news.html."""
    post = build_post(selected_updates)

    with open("linkedin_post.txt", "w", encoding="utf-8", newline="\n") as output_file:
        output_file.write(post)

    print("Created: linkedin_post.txt")
    return post


# ============================================================
# Main execution
# ============================================================

def main():
    feed = feedparser.parse(RSS_URL)

    if getattr(feed, "bozo", False) and not feed.entries:
        raise RuntimeError(f"RSS parsing failed: {feed.bozo_exception}")

    if not feed.entries:
        raise RuntimeError("No Azure updates were returned by the RSS feed.")

    selected_updates = get_important_updates(feed, maximum=MAX_UPDATES)

    if not selected_updates:
        raise RuntimeError("No Azure updates were selected.")

    write_json_file(selected_updates)
    post = write_post_file(selected_updates)

    print(f"Azure updates received: {len(feed.entries)}")
    print(f"Azure updates selected: {len(selected_updates)}")
    print()
    print(post)


if __name__ == "__main__":
    main()
    with open("linkedin_post.txt", "w", encoding="utf-8") as f:
f.write("HELLO FROM GITHUB ACTION")
 
print("Created test linkedin_post.txt")
