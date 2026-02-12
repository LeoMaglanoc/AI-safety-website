"""Clock 1: Fetch autonomous vehicle collision data from NHTSA SGO CSV."""

import csv
import io
import sys

import requests

from scrapers.common import (
    build_clock_json,
    load_clock_json,
    merge_incidents,
    parse_incident_date,
    save_clock_json,
)

SOURCE_URL = "https://static.nhtsa.gov/odi/ffdd/sgo-2021-01/SGO-2021-01_Incident_Reports_ADS.csv"
OUTPUT_PATH = "data/clock1_av_collisions.json"

DATA_SOURCE = {
    "name": "NHTSA Standing General Order (SGO-2021-01)",
    "url": SOURCE_URL,
    "update_frequency": "near-daily",
}


def map_severity(injury_severity: str, property_damage: str) -> str:
    """Map NHTSA severity fields to a simplified severity level."""
    injury = (injury_severity or "").strip().lower()
    if injury in ("suspected serious", "serious", "fatal", "incapacitating"):
        return "serious_injury"
    if injury in ("minor", "possible", "suspected minor"):
        return "minor_injury"
    return "property_damage"


def build_incident_title(make: str, model: str, city: str, state: str) -> str:
    """Build a human-readable incident title."""
    return f"{make} {model} ADS collision, {city}, {state}"


def parse_csv(csv_text: str) -> list[dict]:
    """Parse NHTSA SGO CSV text into a list of incident dicts."""
    reader = csv.DictReader(io.StringIO(csv_text))
    incidents = []
    for row in reader:
        raw_date = row.get("Incident Date", "").strip()
        if not raw_date:
            continue
        try:
            dt = parse_incident_date(raw_date)
        except ValueError:
            continue

        incidents.append({
            "date": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "title": build_incident_title(
                row.get("Make", "Unknown"),
                row.get("Model", "Unknown"),
                row.get("City", "Unknown"),
                row.get("State", ""),
            ),
            "source_url": SOURCE_URL,
            "source_name": "NHTSA SGO",
            "severity": map_severity(
                row.get("Highest Injury Severity", ""),
                row.get("Property Damage", ""),
            ),
            "_raw_date": raw_date,
        })
    return incidents


def run(output_path: str = OUTPUT_PATH) -> None:
    """Fetch NHTSA data, merge with existing, and save."""
    resp = requests.get(SOURCE_URL, timeout=60)
    resp.raise_for_status()

    new_incidents = parse_csv(resp.text)

    # Strip internal fields before saving
    for inc in new_incidents:
        inc.pop("_raw_date", None)

    existing_data = load_clock_json(output_path)
    if existing_data and existing_data.get("last_incident"):
        existing_incidents = [existing_data["last_incident"]] + existing_data.get("previous_incidents", [])
    else:
        existing_incidents = []

    all_incidents = merge_incidents(existing_incidents, new_incidents)

    clock_data = build_clock_json(
        clock_id="av_collisions",
        clock_name="Physical AI Safety Clock",
        description="Time since last autonomous vehicle collision",
        incidents=all_incidents,
        data_source=DATA_SOURCE,
    )
    save_clock_json(clock_data, output_path)


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else OUTPUT_PATH
    run(output_path=output)
    print(f"Saved AV collision data to {output}")
