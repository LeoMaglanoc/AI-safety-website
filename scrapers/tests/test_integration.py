"""Integration tests: validate that scraper pipelines produce valid clock JSON."""

import json
import os
import tempfile
from datetime import datetime, timezone

import pytest
import responses

from scrapers.fetch_av_collisions import SOURCE_URL as AV_URL, run as run_av
from scrapers.fetch_cyber_incidents import CISA_KEV_URL, CISA_RSS_URL, run as run_cyber

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

REQUIRED_KEYS = {"clock_id", "clock_name", "description", "last_incident", "previous_incidents", "last_updated", "data_source"}
INCIDENT_KEYS = {"date", "title", "source_url", "source_name", "severity"}


def _read_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return f.read()


def _validate_iso8601(date_str):
    """Check that a date string is valid ISO 8601."""
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    assert dt.tzinfo is not None or "T" in date_str


def _validate_clock_json(data):
    """Validate clock JSON structure."""
    assert REQUIRED_KEYS.issubset(data.keys()), f"Missing keys: {REQUIRED_KEYS - data.keys()}"
    assert isinstance(data["previous_incidents"], list)
    _validate_iso8601(data["last_updated"])

    if data["last_incident"] is not None:
        assert INCIDENT_KEYS.issubset(data["last_incident"].keys())
        _validate_iso8601(data["last_incident"]["date"])

    for inc in data["previous_incidents"]:
        assert INCIDENT_KEYS.issubset(inc.keys())
        _validate_iso8601(inc["date"])


class TestAvPipelineIntegration:
    @responses.activate
    def test_produces_valid_json_schema(self):
        csv_text = _read_fixture("sample_ads.csv")
        responses.add(responses.GET, AV_URL, body=csv_text, status=200)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            run_av(output_path=path)
            with open(path) as f:
                data = json.load(f)
            _validate_clock_json(data)
            assert data["clock_id"] == "av_collisions"
        finally:
            os.unlink(path)


class TestCyberPipelineIntegration:
    @responses.activate
    def test_produces_valid_json_schema(self):
        kev_text = _read_fixture("sample_kev.json")
        rss_text = _read_fixture("sample_rss.xml")
        responses.add(responses.GET, CISA_KEV_URL, body=kev_text, status=200)
        responses.add(responses.GET, CISA_RSS_URL, body=rss_text, status=200)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            run_cyber(output_path=path)
            with open(path) as f:
                data = json.load(f)
            _validate_clock_json(data)
            assert data["clock_id"] == "cyber_incidents"
        finally:
            os.unlink(path)


class TestAllDatesIso8601:
    @responses.activate
    def test_av_dates_are_iso8601(self):
        csv_text = _read_fixture("sample_ads.csv")
        responses.add(responses.GET, AV_URL, body=csv_text, status=200)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            run_av(output_path=path)
            with open(path) as f:
                data = json.load(f)
            all_incidents = [data["last_incident"]] + data["previous_incidents"]
            for inc in all_incidents:
                _validate_iso8601(inc["date"])
        finally:
            os.unlink(path)

    @responses.activate
    def test_cyber_dates_are_iso8601(self):
        kev_text = _read_fixture("sample_kev.json")
        rss_text = _read_fixture("sample_rss.xml")
        responses.add(responses.GET, CISA_KEV_URL, body=kev_text, status=200)
        responses.add(responses.GET, CISA_RSS_URL, body=rss_text, status=200)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            run_cyber(output_path=path)
            with open(path) as f:
                data = json.load(f)
            all_incidents = []
            if data["last_incident"]:
                all_incidents.append(data["last_incident"])
            all_incidents.extend(data["previous_incidents"])
            for inc in all_incidents:
                _validate_iso8601(inc["date"])
        finally:
            os.unlink(path)
