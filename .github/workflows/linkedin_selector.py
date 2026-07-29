import json
import re
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# Configuration
# ============================================================

INPUT_FILE = Path("azure_updates.json")
OUTPUT_DIRECTORY = Path("linkedin_candidates")
MANIFEST_FILE = OUTPUT_DIRECTORY / "manifest.json"

MAX_CANDIDATES = 3
MINIMUM_LINKEDIN_SCORE = 20

SITE_URL = "https://koritsidis.me/azure-news.html"

CORE_TOPICS = {
    "azure arc": 20,
    "azure local": 20,
    "azure virtual desktop": 20,
    "avd": 18,
    "hybrid cloud": 17,
    "hybrid": 12,
    "migration": 14,
    "site recovery": 15,
    "disaster recovery": 15,
    "resiliency": 14,
    "expressroute": 16,
    "vpn": 11,
    "networking": 12,
    "nat gateway": 12,
    "firewall": 13,
    "private link": 12,
    "defender": 14,
    "security": 12,
    "entra": 13,
    "identity": 11,
    "governance": 12,
    "azure policy": 14,
    "landing zone": 15,
    "virtual machine": 10,
    "storage": 9,
    "backup": 12,
    "aks": 9,
    "kubernetes": 8,
    "azure ai": 9,
    "openai": 9,
}

RELEASE_SCORES = {
    "generally available": 10,
    "general availability": 10,
    "[launched]": 9,
    "launched": 8,
    "public preview": 5,
    "preview": 3,
}

LOW_VALUE_TERMS = {
    "retired": -2,
    "minor": -3,
    "documentation": -3,
    "portal experience": -2,
}


# ============================================================
# Helper functions
# ============================================================

def normalize_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def shorten_text(text, maximum_length=520):
    text = normalize_text(text)

    if len(text) <= maximum_length:
        return text

    shortened = text[:maximum_length].rsplit(" ", 1)[0]
    return shortened.rstrip(".,;:") + "..."


def calculate_score(update):
    title = normalize_text(update.get("title"))
    summary = normalize_text(update.get("summary"))

    title_lower = title.lower()
    combined_lower = f"{title} {summary}".lower()

    score = 0
    matched_topics = []

    for keyword, weight in CORE_TOPICS.items():
        if keyword in combined_lower:
            score += weight
            matched_topics.append(keyword)

        # A title match has higher importance.
        if keyword in title_lower:
            score += round(weight * 0.5)

    for keyword, weight in RELEASE_SCORES.items():
        if keyword in combined_lower:
            score += weight

    for keyword, weight in LOW_VALUE_TERMS.items():
        if keyword in combined_lower:
            score += weight

    return score, sorted(set(matched_topics))


def determine_category(update):
    text = (
        f"{update.get('title', '')} "
        f"{update.get('summary', '')}"
    ).lower()

    if any(
        word in text
        for word in [
            "azure arc",
            "azure local",
            "hybrid",
            "edge",
        ]
    ):
        return "Hybrid Cloud"

    if any(
        word in text
        for word in [
            "virtual desktop",
            "avd",
            "fslogix",
        ]
    ):
        return "Azure Virtual Desktop"

    if any(
        word in text
        for word in [
            "network",
            "expressroute",
            "vpn",
            "nat gateway",
            "firewall",
            "private link",
            "dns",
            "ipv6",
        ]
    ):
        return "Azure Networking"

    if any(
        word in text
        for word in [
            "defender",
            "security",
            "sentinel",
            "entra",
            "identity",
            "compliance",
        ]
    ):
        return "Security & Identity"

    if any(
        word in text
        for word in [
            "migration",
            "site recovery",
            "backup",
            "resiliency",
            "disaster recovery",
        ]
    ):
        return "Migration & Resiliency"

    if any(
        word in text
        for word in [
            "virtual machine",
            "storage",
            "disk",
            "compute",
        ]
    ):
        return "Azure Infrastructure"

    if any(
        word in text
        for word in [
            "azure ai",
            "openai",
            "artificial intelligence",
        ]
    ):
        return "Azure AI"

    return "Azure Platform"


def build_csa_perspective(update, category):
    perspectives = {
        "Hybrid Cloud": (
            "From an Azure architecture perspective, this update is "
            "particularly relevant to organizations extending Azure "
            "management, governance and security across datacenter, "
            "edge and multicloud environments."
        ),
        "Azure Virtual Desktop": (
            "For AVD environments, the key question is how this capability "
            "affects user experience, profile management, image strategy, "
            "identity, networking and day-two operations."
        ),
        "Azure Networking": (
            "Network architects should assess the impact on routing, "
            "addressing, DNS, security controls, resiliency, observability "
            "and the existing landing-zone design."
        ),
        "Security & Identity": (
            "Security and identity teams should map this capability to "
            "existing controls, compliance requirements, access models, "
            "logging and incident-response processes."
        ),
        "Migration & Resiliency": (
            "This update should be evaluated against workload dependencies, "
            "recovery objectives, failure-domain design and tested "
            "operational runbooks."
        ),
        "Azure Infrastructure": (
            "Infrastructure teams should evaluate workload compatibility, "
            "performance, availability, operational tooling and cost before "
            "adopting this capability in production."
        ),
        "Azure AI": (
            "Enterprise adoption should include identity, data protection, "
            "network isolation, governance, monitoring, responsible-AI "
            "controls and cost management."
        ),
        "Azure Platform": (
            "Architecture teams should assess business value, technical "
            "dependencies, security, governance, operational readiness "
            "and cost before production adoption."
        ),
    }

    return perspectives.get(
        category,
        perspectives["Azure Platform"],
    )


def get_hashtags(category):
    common = ["#Azure", "#MicrosoftAzure", "#CloudArchitecture"]

    category_tags = {
        "Hybrid Cloud": [
            "#AzureArc",
            "#AzureLocal",
            "#HybridCloud",
        ],
        "Azure Virtual Desktop": [
            "#AzureVirtualDesktop",
            "#AVD",
            "#EUC",
        ],
        "Azure Networking": [
            "#AzureNetworking",
            "#CloudNetworking",
            "#HybridConnectivity",
        ],
        "Security & Identity": [
            "#AzureSecurity",
            "#MicrosoftDefender",
            "#MicrosoftEntra",
        ],
        "Migration & Resiliency": [
            "#AzureMigration",
            "#CloudResilience",
            "#DisasterRecovery",
        ],
        "Azure Infrastructure": [
            "#AzureInfrastructure",
            "#CloudComputing",
            "#AzureArchitecture",
        ],
        "Azure AI": [
            "#AzureAI",
            "#ArtificialIntelligence",
            "#ResponsibleAI",
        ],
        "Azure Platform": [
            "#CloudPlatform",
            "#AzureArchitecture",
            "#AzureMVP",
        ],
    }

    final_tags = common + category_tags.get(category, [])

    # Remove duplicated hashtags while preserving order.
    return " ".join(dict.fromkeys(final_tags))


def build_linkedin_post(update, candidate_number):
    title = normalize_text(update.get("title"))
    summary = shorten_text(update.get("summary"), 500)
    link = normalize_text(update.get("link"))

    category = determine_category(update)
    perspective = build_csa_perspective(update, category)
    hashtags = get_hashtags(category)

    post = f"""🚀 Azure Update Worth Watching

{title}

What Microsoft announced:
{summary}

Why it matters:
{perspective}

My recommendation:
Before enabling this broadly, review the release status, identify affected workloads and dependencies, validate security and governance requirements, and test the capability in a controlled environment.

🔗 Official Microsoft announcement:
{link}

📘 More curated Azure updates:
{SITE_URL}

{hashtags}
"""

    return post.strip()


# ============================================================
# Main processing
# ============================================================

def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as input_file:
        updates = json.load(input_file)

    if not isinstance(updates, list):
        raise ValueError(
            "azure_updates.json must contain a JSON list."
        )

    scored_updates = []

    for update in updates:
        score, matched_topics = calculate_score(update)

        enriched_update = dict(update)
        enriched_update["linkedin_score"] = score
        enriched_update["matched_topics"] = matched_topics

        scored_updates.append(enriched_update)

    scored_updates.sort(
        key=lambda item: item["linkedin_score"],
        reverse=True,
    )

    selected_updates = [
        update
        for update in scored_updates
        if update["linkedin_score"] >= MINIMUM_LINKEDIN_SCORE
    ][:MAX_CANDIDATES]

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Remove previous candidate text files.
    for previous_file in OUTPUT_DIRECTORY.glob(
        "candidate_*.txt"
    ):
        previous_file.unlink()

    manifest = {
        "generated_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "minimum_score": MINIMUM_LINKEDIN_SCORE,
        "candidate_count": len(selected_updates),
        "candidates": [],
    }

    if not selected_updates:
        no_candidate_file = (
            OUTPUT_DIRECTORY / "no_candidate.txt"
        )

        no_candidate_file.write_text(
            (
                "No Azure update exceeded the "
                "LinkedIn publishing threshold.\n"
                "Nothing should be published today.\n"
            ),
            encoding="utf-8",
        )

        print(
            "No update met the LinkedIn publishing threshold."
        )

    for index, update in enumerate(
        selected_updates,
        start=1,
    ):
        candidate_post = build_linkedin_post(
            update,
            index,
        )

        candidate_file = (
            OUTPUT_DIRECTORY /
            f"candidate_{index}.txt"
        )

        candidate_file.write_text(
            candidate_post,
            encoding="utf-8",
        )

        manifest["candidates"].append(
            {
                "candidate_number": index,
                "score": update["linkedin_score"],
                "title": update.get("title", ""),
                "category": determine_category(update),
                "matched_topics": update["matched_topics"],
                "source": update.get("link", ""),
                "file": str(candidate_file),
            }
        )

        print(
            f"Candidate {index}: "
            f"score={update['linkedin_score']} - "
            f"{update.get('title', '')}"
        )

    with MANIFEST_FILE.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        json.dump(
            manifest,
            output_file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"Created {len(selected_updates)} "
        f"LinkedIn candidate post(s)."
    )


if __name__ == "__main__":
    main()
