#!/usr/bin/env python3
"""Create linkedin_post.txt from the official Microsoft Azure Updates RSS feed."""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

RSS_URL = "https://www.microsoft.com/releasecommunications/api/v2/azure/rss"
MAX_UPDATES = 5
OUTPUT_TEXT = Path("linkedin_post.txt")
OUTPUT_JSON = Path("azure_updates.json")
OUTPUT_CANDIDATES = Path("linkedin_candidates.json")
USER_AGENT = "koritsidis.me-azure-news/1.0"

PRIORITY_KEYWORDS = {
    "azure arc": 30,
    "azure local": 30,
    "azure virtual desktop": 28,
    "avd": 20,
    "hybrid cloud": 22,
    "hybrid": 12,
    "migration": 18,
    "landing zone": 18,
    "expressroute": 18,
    "site recovery": 17,
    "disaster recovery": 17,
    "resiliency": 16,
    "availability zone": 14,
    "backup": 14,
    "firewall": 15,
    "private link": 13,
    "nat gateway": 13,
    "networking": 12,
    "network": 10,
    "security": 14,
    "defender": 16,
    "sentinel": 15,
    "entra": 14,
    "identity": 12,
    "policy": 12,
    "governance": 14,
    "compliance": 11,
    "azure monitor": 12,
    "monitor": 8,
    "kubernetes": 10,
    "aks": 12,
    "azure ai": 10,
    "openai": 10,
    "virtual machine": 12,
    "storage": 9,
    "region": 8,
}

RELEASE_KEYWORDS = {
    "generally available": 12,
    "general availability": 12,
    "[launched]": 10,
    "launched": 8,
    "public preview": 6,
    "in preview": 5,
    "preview": 3,
}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<\s*(br|p|div|li)\b[^>]*>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def shorten(value: str, limit: int = 360) -> str:
    value = clean_text(value)
    if len(value) <= limit:
        return value
    result = value[:limit].rsplit(" ", 1)[0].rstrip(".,;:")
    return result + "..."


def child_text(element: ET.Element, names: tuple[str, ...]) -> str:
    for child in list(element):
        local_name = child.tag.split("}")[-1].lower()
        if local_name in names:
            return "".join(child.itertext()).strip()
    return ""


def fetch_rss() -> bytes:
    request = urllib.request.Request(
        RSS_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def parse_date(value: str) -> datetime:
    if value:
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            pass
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass
    return datetime(1970, 1, 1, tzinfo=timezone.utc)


def parse_items(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    elements = [node for node in root.iter() if node.tag.split("}")[-1].lower() in ("item", "entry")]
    items = []

    for position, element in enumerate(elements):
        title = clean_text(child_text(element, ("title",)))
        summary = clean_text(child_text(element, ("description", "summary", "content", "encoded")))
        link = child_text(element, ("link",))
        if not link:
            for child in list(element):
                if child.tag.split("}")[-1].lower() == "link":
                    link = child.attrib.get("href", "")
                    if link:
                        break
        published_raw = child_text(element, ("pubdate", "published", "updated", "date"))

        if title:
            items.append(
                {
                    "title": title,
                    "summary": summary,
                    "link": link.strip(),
                    "published_raw": published_raw,
                    "published": parse_date(published_raw),
                    "position": position,
                }
            )

    return items


def score_item(item: dict) -> tuple[int, list[str]]:
    title_lower = item["title"].lower()
    searchable = (item["title"] + " " + item["summary"]).lower()
    score = 0
    topics = []

    for keyword, weight in PRIORITY_KEYWORDS.items():
        if keyword in searchable:
            score += weight
            topics.append(keyword)
        if keyword in title_lower:
            score += max(1, weight // 2)

    for keyword, weight in RELEASE_KEYWORDS.items():
        if keyword in searchable:
            score += weight

    return score, sorted(set(topics))


def select_updates(items: list[dict], maximum: int) -> list[dict]:
    ranked = []
    for item in items:
        score, topics = score_item(item)
        result = dict(item)
        result["score"] = score
        result["topics"] = topics
        ranked.append(result)

    ranked.sort(
        key=lambda item: (
            -item["score"],
            -item["published"].timestamp(),
            item["position"],
        )
    )

    selected = []
    seen = set()
    for item in ranked:
        normalized = re.sub(r"\W+", " ", item["title"].lower()).strip()
        if normalized in seen:
            continue
        seen.add(normalized)
        selected.append(item)
        if len(selected) == maximum:
            break
    return selected


def release_status(item: dict) -> str:
    text = (item["title"] + " " + item["summary"]).lower()
    if "generally available" in text or "general availability" in text or "[launched]" in text:
        return "Generally Available"
    if "public preview" in text or "in preview" in text or "[in preview]" in text:
        return "Public Preview"
    if "retire" in text or "deprecated" in text:
        return "Retirement or deprecation"
    return "Azure update"


def csa_perspective(item: dict) -> str:
    topics = item.get("topics", [])
    focus = ", ".join(topics[:3]) if topics else "architecture and operations"
    return (
        "CSA perspective: Assess relevance for " + focus + ". "
        "Validate regional availability, prerequisites, security, governance, "
        "operational readiness and cost before production adoption."
    )


def build_post(items: list[dict]) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "\U0001f680 Azure Executive Update",
        "",
        "Date: " + today,
        "",
        "Top Azure platform updates selected for infrastructure, hybrid cloud, security, networking and operations:",
        "",
    ]

    for index, item in enumerate(items, start=1):
        lines.append(str(index) + ". " + item["title"])
        lines.append("Status: " + release_status(item))
        if item["summary"]:
            lines.append("What changed: " + shorten(item["summary"], 360))
        lines.append(csa_perspective(item))
        if item["link"]:
            lines.append("Source: " + item["link"])
        lines.append("")

    lines.extend(
        [
            "Executive takeaway:",
            "Prioritize capabilities that reduce operational risk, strengthen resiliency, improve security posture or simplify hybrid-cloud management. Validate preview features in a controlled environment before production use.",
            "",
            "#Azure #MicrosoftAzure #AzureArchitecture #HybridCloud #CloudSecurity #AzureMVP",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def write_outputs(selected: list[dict]) -> None:
    post = build_post(selected)
    OUTPUT_TEXT.write_text(post, encoding="utf-8", newline="\n")

    json_items = []
    for item in selected:
        json_items.append(
            {
                "selected": False,
                "title": item["title"],
                "summary": item["summary"],
                "link": item["link"],
                "status": release_status(item),
                "score": item["score"],
                "topics": item["topics"],
                "published_utc": item["published"].isoformat(),
            }
        )
        linkedin_candidates = []

    for item in selected:
        linkedin_candidates.append(
            {
                "selected": False,
                "linkedin_ready": item["score"] >= 25,
                "priority": item["score"],
                "title": item["title"],
                "summary": shorten(item["summary"], 200),
                "link": item["link"],
                "status": release_status(item),
                "topics": item["topics"],
                "published_utc": item["published"].isoformat(),
            }
        )
    
    
    OUTPUT_CANDIDATES.write_text(json.dumps(linkedin_candidates,indent=2,ensure_ascii=False) + "\n",encoding="utf-8")
    best_candidate = max(
linkedin_candidates,
key=lambda x: x["priority"]
)
 
post_content = f"""🚀 Azure Executive Update
 
{best_candidate["title"]}
 
{best_candidate["summary"]}
 
Why it matters:
This Azure update may be relevant for organizations evaluating modernization, security, governance, resiliency, or operational improvements.
 
Read more:
{best_candidate["link"]}
 
#Azure #MicrosoftAzure #AzureArchitecture #HybridCloud #CloudSecurity #AzureMVP
"""
 
OUTPUT_TEXT.write_text(
post_content + "\n",
encoding="utf-8"
)
 
print("Best LinkedIn candidate: " + best_candidate["title"])
print("LinkedIn score: " + str(best_candidate["priority"]))
 
    OUTPUT_JSON.write_text(json.dumps(json_items, indent=2, ensure_ascii=False)+ "\n",encoding="utf-8",)    
    OUTPUT_JSON.write_text(json.dumps(json_items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("linkedin_candidates.json").write_text(json.dumps(linkedin_candidates, indent=2, ensure_ascii=False) + "\n",encoding="utf-8",)
   ## OUTPUT_CANDIDATES.write_text(json.dumps(linkedin_candidates,indent=2,ensure_ascii=False) + "\n",encoding="utf-8")

    if OUTPUT_TEXT.stat().st_size == 0:
        raise RuntimeError("linkedin_post.txt was created but is empty")

    print("Created: " + str(OUTPUT_TEXT))
    print("Created: " + str(OUTPUT_JSON))
    print("Created: " + str(OUTPUT_CANDIDATES))
    print("Created: linkedin_candidates.json")
    print("linkedin_post.txt bytes: " + str(OUTPUT_TEXT.stat().st_size))
    print(post)


def main() -> int:
    try:
        xml_bytes = fetch_rss()
        items = parse_items(xml_bytes)
        if not items:
            raise RuntimeError("The Azure RSS feed returned no readable items")

        selected = select_updates(items, MAX_UPDATES)
        if not selected:
            raise RuntimeError("No Azure updates were selected")

        write_outputs(selected)
        print("Azure updates received: " + str(len(items)))
        print("Azure updates selected: " + str(len(selected)))
        return 0
    except Exception as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
