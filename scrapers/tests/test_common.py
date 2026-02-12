import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from scrapers.common import (
    build_clock_json,
    find_latest_incident,
    load_clock_json,
    merge_incidents,
    parse_incident_date,
    save_clock_json,
)


class TestParseIncidentDate:
    def test_month_year(self):
        result = parse_incident_date("DEC-2025")
        assert result == datetime(2025, 12, 15, tzinfo=timezone.utc)

    def test_iso_string(self):
        result = parse_incident_date("2025-12-10T00:00:00Z")
        assert result == datetime(2025, 12, 10, tzinfo=timezone.utc)

    def test_iso_date_only(self):
        result = parse_incident_date("2025-12-10")
        assert result == datetime(2025, 12, 10, tzinfo=timezone.utc)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_incident_date("not-a-date")


class TestFindLatestIncident:
    def test_returns_newest(self):
        incidents = [
            {"date": "2025-11-01T00:00:00Z", "title": "older"},
            {"date": "2025-12-10T00:00:00Z", "title": "newer"},
            {"date": "2025-10-05T00:00:00Z", "title": "oldest"},
        ]
        result = find_latest_incident(incidents)
        assert result["title"] == "newer"

    def test_empty_returns_none(self):
        assert find_latest_incident([]) is None


class TestMergeIncidents:
    def test_disjoint_lists_merge(self):
        existing = [{"date": "2025-11-01T00:00:00Z", "title": "A"}]
        new = [{"date": "2025-12-01T00:00:00Z", "title": "B"}]
        merged = merge_incidents(existing, new)
        assert len(merged) == 2

    def test_deduplicates(self):
        a = [
            {"date": "2025-11-01T00:00:00Z", "title": "A"},
            {"date": "2025-12-01T00:00:00Z", "title": "B"},
        ]
        b = [
            {"date": "2025-12-01T00:00:00Z", "title": "B"},
            {"date": "2026-01-01T00:00:00Z", "title": "C"},
        ]
        merged = merge_incidents(a, b)
        assert len(merged) == 3
        titles = [i["title"] for i in merged]
        assert sorted(titles) == ["A", "B", "C"]


class TestBuildClockJson:
    def test_has_all_required_keys(self):
        incidents = [{"date": "2025-12-10T00:00:00Z", "title": "test"}]
        result = build_clock_json(
            clock_id="av_collisions",
            clock_name="Physical AI Safety Clock",
            description="Time since last autonomous vehicle collision",
            incidents=incidents,
            data_source={"name": "NHTSA SGO", "url": "https://example.com", "update_frequency": "daily"},
        )
        assert result["clock_id"] == "av_collisions"
        assert result["clock_name"] == "Physical AI Safety Clock"
        assert result["description"] == "Time since last autonomous vehicle collision"
        assert "last_incident" in result
        assert "previous_incidents" in result
        assert "last_updated" in result
        assert "data_source" in result
        assert result["last_incident"]["title"] == "test"


class TestLoadSaveClockJson:
    def test_missing_file_returns_empty(self):
        result = load_clock_json("/nonexistent/path/clock.json")
        assert result is None

    def test_save_and_load_roundtrip(self):
        data = build_clock_json(
            clock_id="test",
            clock_name="Test Clock",
            description="A test clock",
            incidents=[{"date": "2025-12-10T00:00:00Z", "title": "test incident"}],
            data_source={"name": "test", "url": "https://test.com", "update_frequency": "daily"},
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_clock_json(data, path)
            loaded = load_clock_json(path)
            assert loaded == data
        finally:
            os.unlink(path)
