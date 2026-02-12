import json
import os
import tempfile

import pytest
import responses

from scrapers.fetch_cyber_incidents import (
    CISA_KEV_URL,
    CISA_RSS_URL,
    has_ai_keyword,
    parse_kev_json,
    parse_rss_feed,
    run,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _read_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return f.read()


class TestAiKeywordDetection:
    def test_finds_machine_learning(self):
        assert has_ai_keyword("vulnerability in its machine learning inference engine")

    def test_ignores_non_ai(self):
        assert not has_ai_keyword("SQL injection vulnerability in the query parser")

    def test_word_boundary_no_false_positive(self):
        # "AVAILABILITY" should NOT match "AI"
        assert not has_ai_keyword("affecting AVAILABILITY monitoring dashboard")

    def test_finds_llm(self):
        assert has_ai_keyword("LLM-powered chatbot prompt injection vulnerability")

    def test_finds_autonomous(self):
        assert has_ai_keyword("autonomous vehicle fleet management system")

    def test_finds_deep_learning(self):
        assert has_ai_keyword("deep learning model serving component")


class TestParseKev:
    def test_finds_ai_entries(self):
        kev_text = _read_fixture("sample_kev.json")
        incidents = parse_kev_json(kev_text)
        # Should find: AI Security Suite (machine learning), DeepVision (deep learning, neural network), ChatAssist (LLM)
        assert len(incidents) == 3
        cves = {i["cve_id"] for i in incidents}
        assert "CVE-2026-0001" in cves  # machine learning
        assert "CVE-2026-0003" in cves  # deep learning, neural network
        assert "CVE-2026-0005" in cves  # LLM

    def test_ignores_non_ai(self):
        kev_text = _read_fixture("sample_kev.json")
        incidents = parse_kev_json(kev_text)
        cves = {i["cve_id"] for i in incidents}
        assert "CVE-2026-0002" not in cves  # SQL injection
        assert "CVE-2026-0004" not in cves  # AVAILABILITY (not AI)


class TestParseRss:
    def test_finds_ai_items(self):
        rss_text = _read_fixture("sample_rss.xml")
        incidents = parse_rss_feed(rss_text)
        # "artificial intelligence" in title and "autonomous" + "computer vision" in item 3
        assert len(incidents) == 2
        titles = [i["title"] for i in incidents]
        assert any("Artificial Intelligence" in t for t in titles)
        assert any("Autonomous" in t for t in titles)

    def test_ignores_non_ai(self):
        rss_text = _read_fixture("sample_rss.xml")
        incidents = parse_rss_feed(rss_text)
        titles = [i["title"] for i in incidents]
        assert not any("Yokogawa" in t for t in titles)
        assert not any("Generic Router" in t for t in titles)


class TestRun:
    @responses.activate
    def test_no_matches_preserves_existing(self):
        # KEV with no AI entries, RSS with no AI entries
        kev_data = {"vulnerabilities": [
            {"cveID": "CVE-2026-9999", "vendorProject": "X", "product": "Y",
             "vulnerabilityName": "X Y Buffer Overflow", "dateAdded": "2026-01-01",
             "shortDescription": "A buffer overflow in X Y."}
        ]}
        rss_data = """<?xml version="1.0"?><rss version="2.0"><channel>
        <item><title>Router Update</title><link>https://example.com</link>
        <description>A router bug.</description><pubDate>Mon, 01 Jan 2026 00:00:00 GMT</pubDate>
        </item></channel></rss>"""

        responses.add(responses.GET, CISA_KEV_URL, json=kev_data, status=200)
        responses.add(responses.GET, CISA_RSS_URL, body=rss_data, status=200)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "clock_id": "cyber_incidents",
                "clock_name": "Digital AI Safety Clock",
                "description": "Time since last AI-related cybersecurity incident",
                "last_incident": {"date": "2025-12-01T00:00:00Z", "title": "Old AI incident"},
                "previous_incidents": [],
                "last_updated": "2025-12-01T00:00:00Z",
                "data_source": {},
            }, f)
            path = f.name

        try:
            run(output_path=path)
            with open(path) as f:
                data = json.load(f)
            # Existing incident should be preserved
            assert data["last_incident"]["title"] == "Old AI incident"
        finally:
            os.unlink(path)

    @responses.activate
    def test_last_updated_always_advances(self):
        kev_data = {"vulnerabilities": []}
        rss_data = """<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>"""

        responses.add(responses.GET, CISA_KEV_URL, json=kev_data, status=200)
        responses.add(responses.GET, CISA_RSS_URL, body=rss_data, status=200)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "clock_id": "cyber_incidents",
                "clock_name": "Digital AI Safety Clock",
                "description": "Time since last AI-related cybersecurity incident",
                "last_incident": None,
                "previous_incidents": [],
                "last_updated": "2020-01-01T00:00:00Z",
                "data_source": {},
            }, f)
            path = f.name

        try:
            run(output_path=path)
            with open(path) as f:
                data = json.load(f)
            assert data["last_updated"] > "2020-01-01T00:00:00Z"
        finally:
            os.unlink(path)

    @responses.activate
    def test_merge_kev_and_rss(self):
        kev_text = _read_fixture("sample_kev.json")
        rss_text = _read_fixture("sample_rss.xml")

        responses.add(responses.GET, CISA_KEV_URL, body=kev_text, status=200)
        responses.add(responses.GET, CISA_RSS_URL, body=rss_text, status=200)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            run(output_path=path)
            with open(path) as f:
                data = json.load(f)
            all_incidents = []
            if data["last_incident"]:
                all_incidents.append(data["last_incident"])
            all_incidents.extend(data["previous_incidents"])
            # 3 from KEV + 2 from RSS = 5
            assert len(all_incidents) == 5
        finally:
            os.unlink(path)
