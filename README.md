# AI Safety Clocks

A static GitHub Pages site displaying live "safety clocks" that track time elapsed since the last known AI-related safety incidents. Data is scraped daily from public government sources via GitHub Actions and rendered as live-ticking counters in the browser.

Live site: [https://leonardo-maglanoc.com/AI-safety-website/](https://leonardo-maglanoc.com/AI-safety-website/)

## Clocks

| Clock | What it tracks | Data source |
|-------|---------------|-------------|
| **Physical AI Safety Clock** | Time since last autonomous vehicle collision | [NHTSA Standing General Order (SGO-2021-01)](https://static.nhtsa.gov/odi/ffdd/sgo-2021-01/) |
| **Digital AI Safety Clock** | Time since last AI-related cybersecurity incident | [CISA KEV Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) + [CISA Advisories RSS](https://www.cisa.gov/cybersecurity-advisories/all.xml) |

Clock cards are color-coded by elapsed time: green (>30 days), yellow (7–30 days), red (<7 days).
 
## Project Structure

```
├── data/                        # Scraped incident JSON (committed by CI)
│   ├── clock1_av_collisions.json
│   └── clock2_cyber_incidents.json
├── scrapers/                    # Python data-fetching scripts
│   ├── common.py                # Shared utilities (date parsing, JSON I/O, merging)
│   ├── fetch_av_collisions.py   # Clock 1: NHTSA SGO CSV parser
│   ├── fetch_cyber_incidents.py # Clock 2: CISA KEV + RSS with AI keyword filtering
│   └── tests/                   # pytest unit + integration tests with fixtures
├── site/                        # Static frontend (GitHub Pages root)
│   ├── index.html
│   ├── css/style.css
│   ├── js/clocks.js             # Elapsed-time logic + DOM rendering
│   ├── js/data-loader.js        # Fetch JSON and initialize clocks
│   └── tests/                   # Jest unit tests
├── e2e/                         # Playwright end-to-end browser tests
├── .github/workflows/           # CI, daily scrape, and Pages deploy
├── Dockerfile
├── docker-compose.yml
└── Makefile
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

That's it — all dependencies (Python, Node, Playwright, etc.) are handled inside containers.

## Quick Start

Build the Docker image:

```sh
make build
```

Run the development server at [http://localhost:8080](http://localhost:8080):

```sh
make serve
```

Stop the server:

```sh
docker compose down
```

## Running Tests

Run the full test suite (38 Python + 10 Jest + 11 Playwright = 59 tests):

```sh
make test
```

Run individual test layers:

```sh
make test-scrapers   # Python unit + integration tests (pytest)
make test-frontend   # JavaScript unit tests (Jest + jsdom)
make test-e2e        # End-to-end browser tests (Playwright + Chromium)
```

Or use `docker compose` directly:

```sh
docker compose run --rm test-all
docker compose run --rm test-scrapers
docker compose run --rm test-frontend
docker compose run --rm test-e2e
```

## Running Scrapers

Fetch the latest data from live sources:

```sh
make scrape-av       # Fetch AV collision data from NHTSA
make scrape-cyber    # Fetch cyber incident data from CISA
```

These update the JSON files in `data/`. In production, this runs automatically via a daily GitHub Actions cron job at 6 AM UTC.

## How It Works

1. **Scrapers** fetch data from public government APIs, parse it, filter for AI-related entries (using keyword matching with word-boundary regex for the cyber clock), and write structured JSON to `data/`.
2. **GitHub Actions** runs the scrapers daily, commits any changes to `data/`, and deploys the site to GitHub Pages.
3. **The frontend** loads the JSON at page load, renders clock cards with the time elapsed since the most recent incident, and ticks every second.

### Data Notes

- AV collision dates from NHTSA are reported at month granularity (e.g., "DEC-2025"). These are approximated to the 15th of the month. A footnote on the site notes this.
- Cyber incident filtering uses a broad keyword list (`artificial intelligence`, `machine learning`, `neural network`, `LLM`, `autonomous`, `deepfake`, etc.) with word-boundary matching to avoid false positives (e.g., "AVAILABILITY" does not match "AI").

## GitHub Actions Workflows

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `test.yml` | Push/PR to `main` | Runs the full test suite in Docker |
| `scrape.yml` | Daily at 6 AM UTC + manual dispatch | Runs both scrapers, commits updated JSON |
| `deploy.yml` | Push to `main` (paths: `site/**`, `data/**`) | Deploys to GitHub Pages |
