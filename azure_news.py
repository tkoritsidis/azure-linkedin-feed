import feedparser
import html
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


# Higher weight means higher relevance for the Azure
# Infrastructure / Hybrid Cloud / CSA audience.
PRIORITY_KEYWORDS = {
    # Core focus areas
    "azure arc": 15,
    "azure local": 15,
    "azure virtual desktop": 15,
    "avd": 14,
    "hybrid": 12,
    "migration": 11,

    # Infrastructure
    "virtual machine": 10,
    "virtual machines": 10,
    "compute": 8,
    "storage": 8,
    "backup": 10,
    "site recovery": 12,
    "disaster recovery": 12,

    # Networking
    "network": 9,
    "networking": 9,
    "expressroute": 12,
    "vpn": 10,
    "nat gateway": 10,
    "load balancer": 9,
    "application gateway": 9,
    "firewall": 11,
    "private link": 10,
    "dns": 8,

    # Governance and security
    "security": 10,
    "defender": 11,
    "sentinel": 10,
    "identity": 9,
    "entra": 10,
    "policy": 9,
    "governance": 10,
    "compliance": 9,
    "enclave": 9,

    # Containers and platform
    "kubernetes": 8,
    "aks": 9,
    "container": 7,

    # AI and data
    "artificial intelligence": 8,
    "azure ai": 9,
    "ai": 5,
    "openai": 9,

    # Release importance
    "generally available": 8,
    "general availability": 8,
    "ga": 4,
    "launched": 7,
    "public preview": 4,
    "preview": 3,

    # Broader platform changes
    "region": 6,
    "datacenter": 7,
    "resiliency": 10,
    "availability zone": 10,
    "monitor": 7,
    "management": 7,
    "automation": 7,
}


# ============================================================
# Text helpers
# ============================================================

def clean_html(raw_text):
    """
    Convert RSS HTML content to clean plain text.
    """

    if not raw_text:
        return ""

    text = html.unescape(str(raw_text))

    # Add line breaks where HTML normally separates content.
    text = re.sub(
        r"<\s*(br|p|div|li)\b[^>]*>",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # Remove the remaining HTML tags.
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def shorten_text(text, max_length=320):
    """
    Shorten text without breaking the last word when possible.
    """

    text = clean_html(text)

    if len(text) <= max_length:
        return text

    shortened = text[:max_length].rsplit(" ", 1)[0]
    return shortened.rstrip(".,;:-") + "..."


def get_item_summary(item):
    """
    Get the best available description from an RSS entry.
    """

    summary = item.get("summary", "")

    if not summary:
        summary = item.get("description", "")

    if not summary and item.get("content"):
        try:
            summary = item.content[0].get("value", "")
        except (IndexError, AttributeError, TypeError):
            summary = ""

    return clean_html(summary)


# ============================================================
# Prioritization
# ============================================================

def calculate_relevance_score(item):
    """
    Assign a relevance score based on title and description.

    This is deterministic prioritization, not an AI-generated
    ranking.
    """

    title = clean_html(item.get("title", ""))
    summary = get_item_summary(item)

    searchable_text = f"{title} {summary}".lower()

    score = 0

    for keyword, weight in PRIORITY_KEYWORDS.items():
        if keyword in searchable_text:
            score += weight

    # Title matches are more important than description matches.
    title_lower = title.lower()

    for keyword, weight in PRIORITY_KEYWORDS.items():
        if keyword in title_lower:
            score += weight

    return score


# ============================================================
# CSA/MVP perspective
# ============================================================

def generate_csa_perspective(title, summary):
    """
    Generate a deterministic CSA/MVP-style interpretation.

    The output is intentionally framed as a practical perspective,
    not as an additional Microsoft announcement or factual claim.
    """

    text = f"{title} {summary}".lower()

    if any(
        keyword in text
        for keyword in [
            "azure arc",
            "azure local",
            "hybrid",
            "edge",
        ]
    ):
        return (
            "CSA/MVP perspective: Hybrid-cloud teams should assess "
            "how this capability fits their existing Azure Arc, "
            "governance, connectivity, and operational-management "
            "model. Validate the feature in a controlled environment "
            "before considering broader adoption."
        )

    if any(
        keyword in text
        for keyword in [
            "virtual desktop",
            "avd",
            "fslogix",
            "desktop",
        ]
    ):
        return (
            "CSA/MVP perspective: AVD teams should review the possible "
            "impact on user experience, image strategy, identity, "
            "profile management, networking, monitoring, and day-two "
            "operations before introducing the change into production."
        )

    if any(
        keyword in text
        for keyword in [
            "network",
            "expressroute",
            "vpn",
            "nat gateway",
            "load balancer",
            "application gateway",
            "firewall",
            "private link",
            "dns",
            "ipv4",
            "ipv6",
        ]
    ):
        return (
            "CSA/MVP perspective: Network architects should evaluate "
            "addressing, routing, security controls, DNS dependencies, "
            "resiliency, observability, and cost implications. A "
            "targeted proof of concept can help validate compatibility "
            "with the current landing-zone design."
        )

    if any(
        keyword in text
        for keyword in [
            "security",
            "defender",
            "sentinel",
            "identity",
            "entra",
            "compliance",
            "enclave",
            "confidential",
        ]
    ):
        return (
            "CSA/MVP perspective: Security and identity teams should "
            "map this update to existing controls, compliance "
            "requirements, logging, access-management processes, and "
            "incident-response procedures before enabling it broadly."
        )

    if any(
        keyword in text
        for keyword in [
            "kubernetes",
            "aks",
            "container",
            "gateway api",
        ]
    ):
        return (
            "CSA/MVP perspective: Platform teams should assess cluster "
            "compatibility, deployment standards, ingress and egress "
            "design, policy enforcement, monitoring, and rollback "
            "requirements before production adoption."
        )

    if any(
        keyword in text
        for keyword in [
            "backup",
            "site recovery",
            "disaster recovery",
            "resiliency",
            "availability zone",
        ]
    ):
        return (
            "CSA/MVP perspective: Resiliency decisions should be based "
            "on validated recovery objectives, dependency mapping, "
            "failure-domain design, operational runbooks, and tested "
            "recovery procedures—not only feature availability."
        )

    if any(
        keyword in text
        for keyword in [
            "virtual machine",
            "compute",
            "storage",
            "disk",
        ]
    ):
        return (
            "CSA/MVP perspective: Infrastructure teams should review "
            "workload compatibility, performance requirements, "
            "availability design, operational tooling, and cost before "
            "selecting this capability for production workloads."
        )

    if any(
        keyword in text
        for keyword in [
            "azure ai",
            "artificial intelligence",
            "openai",
            "ai ",
        ]
    ):
        return (
            "CSA/MVP perspective: AI adoption should include a review "
            "of identity, data protection, network isolation, model "
            "governance, monitoring, responsible-AI controls, and cost "
            "management before enterprise rollout."
        )

    if any(
        keyword in text
        for keyword in [
            "region",
            "datacenter",
        ]
    ):
        return (
            "CSA/MVP perspective: A new Azure region may create "
            "additional architecture options. Organizations should "
            "validate service availability, data-residency needs, "
            "latency, connectivity, resiliency, and commercial "
            "requirements before changing regional strategy."
        )

    if any(
        keyword in text
        for keyword in [
            "policy",
            "governance",
            "management",
            "monitor",
            "automation",
        ]
    ):
        return (
            "CSA/MVP perspective: Cloud-platform teams should determine "
            "whether this update can strengthen governance, policy "
            "consistency, automation, monitoring, and operational "
            "standardization across subscriptions and environments."
        )

    return (
        "CSA/MVP perspective: Architecture teams should review business "
        "value, technical dependencies, security, governance, "
        "operational readiness, support status, and cost before "
        "introducing this capability into a production environment."
    )


# ============================================================
# Feed processing
# ============================================================

def get_important_updates(feed, maximum=5):
    """
    Score RSS entries and return the most relevant unique updates.
    """

    scored_items = []

    for position, item in enumerate(feed.entries):
        title = clean_html(item.get("title", "Azure Update"))

        if not title:
            continue

        score = calculate_relevance_score(item)

        scored_items.append(
            {
                "item": item,
                "title": title,
                "score": score,
                "feed_position": position,
            }
        )

    # Highest relevance first.
    # For equal scores, preserve the source feed order.
    scored_items.sort(
        key=lambda result: (
            -result["score"],
            result["feed_position"],
        )
    )

    selected = []
    seen_titles = set()

    for result in scored_items:
        normalized_title = result["title"].lower().strip()

        if normalized_title in seen_titles:
            continue

        seen_titles.add(normalized_title)
        selected.append(result)

        if len(selected) >= maximum:
            break

    return selected


def build_post(selected_updates):
    """
    Build the final content for linkedin_post.txt.
    """

    generated_time = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    lines = [
        "Microsoft Azure — Executive Update",
        "",
        f"Generated: {generated_time}",
        "",
        (
            "Executive summary: Below are the latest Azure service "
            "announcements prioritized for an Azure Infrastructure "
            "and Hybrid Cloud audience."
        ),
        "",
        (
            "CSA/MVP view: The announcements should be treated as "
            "inputs to architecture and roadmap decisions. Production "
            "adoption should follow validation of business value, "
            "dependencies, security, governance, resiliency, "
            "operational readiness, support status, and cost."
        ),
        "",
        "=" * 60,
        "",
    ]

    for index, result in enumerate(selected_updates, start=1):
        item = result["item"]
        title = result["title"]
        link = item.get("link", "").strip()

        source_summary = get_item_summary(item)
        short_summary = shorten_text(source_summary, 320)

        perspective = generate_csa_perspective(
            title,
            source_summary,
        )

        lines.extend(
            [
                f"{index}. {title}",
                "",
                "Microsoft update:",
                (
                    short_summary
                    if short_summary
                    else "See the official Microsoft announcement."
                ),
                "",
                perspective,
                "",
                "Recommended next steps:",
                "• Review the official announcement and release status.",
                "• Identify affected services, workloads, and dependencies.",
                "• Validate security, governance, networking, and cost.",
                "• Test the capability before production adoption.",
                "",
                "Official Microsoft source:",
                link if link else "Link not supplied by the RSS feed.",
                "",
                "-" * 60,
                "",
            ]
        )

    lines.extend(
        [
            "Follow for practical Azure Infrastructure, Azure Arc, "
            "Azure Local, AVD, migration, and hybrid-cloud insights.",
            "",
            "#Azure #MicrosoftAzure #HybridCloud "
            "#CloudArchitecture #AzureMVP",
        ]
    )

    return "\n".join(lines)


# ============================================================
# Main
# ============================================================

def main():
    feed = feedparser.parse(
        RSS_URL,
        request_headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "Azure-News-Automation/1.0 "
                "(koritsidis.me)"
            )
        },
    )

    if getattr(feed, "bozo", False):
        print(f"RSS warning: {feed.bozo_exception}")

    if not feed.entries:
        raise RuntimeError(
            "No Azure updates were returned from the Microsoft RSS feed."
        )

    selected_updates = get_important_updates(
        feed,
        maximum=MAX_UPDATES,
    )

    if not selected_updates:
        raise RuntimeError(
            "The RSS feed returned entries, but no usable Azure "
            "updates were found."
        )

    post = build_post(selected_updates)

    with open(
        "linkedin_post.txt",
        "w",
        encoding="utf-8",
        newline="\n",
    ) as output_file:
        output_file.write(post)

    print(
        f"Azure updates received: {len(feed.entries)}"
    )
    print(
        f"Azure updates selected: {len(selected_updates)}"
    )
    print(
        "Created: linkedin_post.txt"
    )
    print()
    print(post)


if __name__ == "__main__":
    main()
