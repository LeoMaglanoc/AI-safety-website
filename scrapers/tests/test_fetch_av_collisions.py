import json
import os
import tempfile

import pytest
import responses

from scrapers.fetch_av_collisions import (
    SOURCE_URL,
    build_incident_title,
    map_severity,
    parse_csv,
    run,
)

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "sample_ads.csv")


def _read_fixture():
    with open(FIXTURE_PATH) as f:
        return f.read()


class TestParseCsv:
    def test_extracts_incidents(self):
        csv_text = _read_fixture()
        incidents = parse_csv(csv_text)
        assert len(incidents) == 5

    def test_date_parsing(self):
        csv_text = _read_fixture()
        incidents = parse_csv(csv_text)
        # DEC-2025 should become 2025-12-15
        dec_incident = [i for i in incidents if "DEC" in i["_raw_date"]][0]
        assert dec_incident["date"] == "2025-12-15T00:00:00Z"

    def test_empty_csv_no_incidents(self):
        header_only = "Report ID,Make,Model,City,State,Incident Date,Highest Injury Severity,Property Damage\n"
        incidents = parse_csv(header_only)
        assert incidents == []


class TestSeverityMapping:
    def test_property_damage_only(self):
        assert map_severity("None", "Property Damage Only") == "property_damage"

    def test_minor_injury(self):
        assert map_severity("Minor", "Minor") == "minor_injury"

    def test_serious_injury(self):
        assert map_severity("Suspected Serious", "Severe") == "serious_injury"

    def test_none(self):
        assert map_severity("None", "Minor") == "property_damage"


class TestBuildIncidentTitle:
    def test_includes_make_model_city(self):
        title = build_incident_title("JAGUAR", "I-PACE", "San Francisco", "CA")
        assert "JAGUAR" in title
        assert "I-PACE" in title
        assert "San Francisco" in title


class TestFetch:
    @responses.activate
    def test_fetch_handles_http_error(self):
        responses.add(responses.GET, SOURCE_URL, status=500)
        with pytest.raises(Exception):
            run(output_path="/dev/null")

    @responses.activate
    def test_updates_existing_json(self):
        csv_text = _read_fixture()
        responses.add(responses.GET, SOURCE_URL, body=csv_text, status=200)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Seed with one existing incident not in CSV
            json.dump({
                "clock_id": "av_collisions",
                "clock_name": "Physical AI Safety Clock",
                "description": "Time since last autonomous vehicle collision",
                "last_incident": {"date": "2025-01-15T00:00:00Z", "title": "Old incident"},
                "previous_incidents": [],
                "last_updated": "2025-01-01T00:00:00Z",
                "data_source": {},
            }, f)
            path = f.name

        try:
            run(output_path=path)
            with open(path) as f:
                data = json.load(f)
            # Should have CSV incidents + the old one
            all_incidents = [data["last_incident"]] + data["previous_incidents"]
            assert len(all_incidents) == 6  # 5 from CSV + 1 existing
        finally:
            os.unlink(path)
