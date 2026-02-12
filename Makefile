.PHONY: build test test-scrapers test-frontend test-e2e serve scrape-av scrape-cyber

build:
	docker compose build

test: build
	docker compose run --rm test-all

test-scrapers: build
	docker compose run --rm test-scrapers

test-frontend: build
	docker compose run --rm test-frontend

test-e2e: build
	docker compose run --rm test-e2e

serve:
	docker compose up serve

scrape-av: build
	docker compose run --rm scrape-av

scrape-cyber: build
	docker compose run --rm scrape-cyber
