"""Clock 2: Fetch AI-related cybersecurity incidents from CISA sources."""

import json
import re
import sys

import feedparser
import requests

from scrapers.common import (
    build_clock_json,
    load_clock_json,
    merge_incidents,
    parse_incident_date,
    save_clock_json,
)

CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
CISA_RSS_URL = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
OUTPUT_PATH = "data/clock2_cyber_incidents.json"

DATA_SOURCE = {
    "name": "CISA (KEV Catalog + Cybersecurity Advisories RSS)",
    "url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
    "update_frequency": "weekly",
}

# AI keywords — short terms use word boundaries to avoid false positives
_LONG_KEYWORDS = [
    "artificial intelligence",
    "machine learning",
    "neural network",
    "deep learning",
    "ai-powered",
    "ai-assisted",
    "large language model",
    "generative ai",
    "computer vision",
    "autonomous",
    "deepfake",
    "chatbot",
]

_SHORT_KEYWORDS_RE = re.compile(r"\bAI\b|\bLLM\b|\bGPT\b", re.IGNORECASE)


def has_ai_keyword(text: str) -> bool:
    """Check if text contains any AI-related keyword."""
    lower = text.lower()
    for kw in _LONG_KEYWORDS:
        if kw in lower:
            return True
    return bool(_SHORT_KEYWORDS_RE.search(text))


def parse_kev_json(kev_text: str) -> list[dict]:
    """Parse CISA KEV JSON and return AI-related incidents."""
    data = json.loads(kev_text)
    incidents = []
    for vuln in data.get("vulnerabilities", []):
        searchable = " ".join([
            vuln.get("vulnerabilityName", ""),
            vuln.get("shortDescription", ""),
            vuln.get("product", ""),
        ])
        if not has_ai_keyword(searchable):
            continue

        date_str = vuln.get("dateAdded", "")
        try:
            dt = parse_incident_date(date_str)
        except ValueError:
            continue

        incidents.append({
            "date": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "title": vuln.get("vulnerabilityName", vuln.get("cveID", "Unknown")),
            "source_url": f"https://nvd.nist.gov/vuln/detail/{vuln.get('cveID', '')}",
            "source_name": "CISA KEV",
            "severity": "cyber_vulnerability",
            "cve_id": vuln.get("cveID", ""),
        })
    return incidents


def parse_rss_feed(rss_text: str) -> list[dict]:
    """Parse CISA RSS feed and return AI-related incidents."""
    feed = feedparser.parse(rss_text)
    incidents = []
    for entry in feed.entries:
        searchable = " ".join([
            entry.get("title", ""),
            entry.get("summary", ""),
            entry.get("description", ""),
        ])
        if not has_ai_keyword(searchable):
            continue

        date_str = entry.get("published", "")
        try:
            dt = parse_incident_date(date_str)
        except ValueError:
            continue

        incidents.append({
            "date": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "title": entry.get("title", "Unknown"),
            "source_url": entry.get("link", ""),
            "source_name": "CISA Advisory",
            "severity": "cyber_advisory",
        })
    return incidents


def run(output_path: str = OUTPUT_PATH) -> None:
    """Fetch CISA data, filter for AI keywords, merge with existing, and save."""
    # Fetch KEV
    resp_kev = requests.get(CISA_KEV_URL, timeout=60)
    resp_kev.raise_for_status()
    kev_incidents = parse_kev_json(resp_kev.text)

    # Fetch RSS
    resp_rss = requests.get(CISA_RSS_URL, timeout=60)
    resp_rss.raise_for_status()
    rss_incidents = parse_rss_feed(resp_rss.text)

    new_incidents = kev_incidents + rss_incidents

    # Strip internal fields
    for inc in new_incidents:
        inc.pop("cve_id", None)

    existing_data = load_clock_json(output_path)
    if existing_data and existing_data.get("last_incident"):
        existing_incidents = [existing_data["last_incident"]] + existing_data.get("previous_incidents", [])
    else:
        existing_incidents = []

    all_incidents = merge_incidents(existing_incidents, new_incidents)

    clock_data = build_clock_json(
        clock_id="cyber_incidents",
        clock_name="Digital AI Safety Clock",
        description="Time since last AI-related cybersecurity incident",
        incidents=all_incidents,
        data_source=DATA_SOURCE,
    )
    save_clock_json(clock_data, output_path)


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else OUTPUT_PATH
    run(output_path=output)
    print(f"Saved cyber incident data to {output}")
