"""Shared utilities for AI Safety Clock scrapers."""

import json
import os
from datetime import datetime, timezone

from dateutil import parser as dateutil_parser


def parse_incident_date(date_string: str) -> datetime:
    """Parse a date string into a timezone-aware UTC datetime.

    Supports:
    - ISO 8601 (2025-12-10T00:00:00Z, 2025-12-10)
    - Month-Year (DEC-2025) -> 15th of that month
    """
    date_string = date_string.strip()

    # Try MON-YYYY format (e.g. DEC-2025)
    try:
        dt = datetime.strptime(date_string, "%b-%Y")
        return dt.replace(day=15, tzinfo=timezone.utc)
    except ValueError:
        pass

    # Try general date parsing
    try:
        dt = dateutil_parser.parse(date_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, dateutil_parser.ParserError):
        pass

    raise ValueError(f"Cannot parse date: {date_string!r}")


def find_latest_incident(incidents: list[dict]) -> dict | None:
    """Return the incident with the most recent date, or None if empty."""
    if not incidents:
        return None
    return max(incidents, key=lambda i: parse_incident_date(i["date"]))


def merge_incidents(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge two incident lists, deduplicating by (date, title)."""
    seen = set()
    merged = []
    for incident in existing + new:
        key = (incident["date"], incident["title"])
        if key not in seen:
            seen.add(key)
            merged.append(incident)
    return merged


def build_clock_json(
    clock_id: str,
    clock_name: str,
    description: str,
    incidents: list[dict],
    data_source: dict,
) -> dict:
    """Build the standard clock JSON structure."""
    latest = find_latest_incident(incidents)
    previous = [i for i in incidents if i is not latest] if latest else []

    return {
        "clock_id": clock_id,
        "clock_name": clock_name,
        "description": description,
        "last_incident": latest,
        "previous_incidents": previous,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_source": data_source,
    }


def load_clock_json(path: str) -> dict | None:
    """Load clock JSON from file. Returns None if file doesn't exist or is empty/invalid."""
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            content = f.read().strip()
            if not content:
                return None
            return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return None


def save_clock_json(data: dict, path: str) -> None:
    """Save clock JSON to file, creating directories if needed."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
