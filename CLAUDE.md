# AI Safety Clocks — Project Guidelines

## Workflow

- **Docker-first**: All development, builds, and testing must run inside Docker containers. Use `docker compose` for local dev and GitHub Actions should use container-based workflows.
- **TDD (Test-Driven Development)**: Always write tests before implementation. Red → Green → Refactor. No production code without a failing test first.

## Project Overview

Static GitHub Pages site displaying live "safety clocks" tracking time since last known incidents:

1. **Physical AI Safety Clock** — Time since last AV collision (CA DMV / NHTSA)
2. **Digital AI Safety Clock** — Time since last AI-assisted cybersecurity incident (CISA advisories)
3. **LLM Misuse Clock** — Time since last model-provider confirmed abuse cluster

## Architecture

- Static HTML/CSS/JS served via GitHub Pages
- GitHub Actions scheduled workflow scrapes public data sources and commits updated JSON
- Client-side JS reads JSON timestamps and renders live-counting clocks

## Data Sources

- CA DMV Autonomous Vehicle collision reports
- NHTSA Standing General Order crash data
- CISA advisories (AI-related)
- Model provider transparency reports / disclosure feeds

## Testing

- Unit tests for data-fetching scripts
- Unit tests for clock rendering logic
- Integration tests via Docker
