FROM python:3.12-slim

# Install Node.js 20
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY scrapers/requirements.txt scrapers/requirements.txt
RUN pip install --no-cache-dir -r scrapers/requirements.txt

# Install Node dependencies (Jest unit tests)
COPY site/tests/package.json site/tests/package.json
RUN cd site/tests && npm install

# Install Playwright e2e dependencies
COPY e2e/package.json e2e/package.json
RUN cd e2e && npm install && npx playwright install --with-deps chromium

COPY . .
