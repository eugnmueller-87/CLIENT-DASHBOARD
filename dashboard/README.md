# Agency Dashboard — Grafana + Prometheus

![Grafana](https://img.shields.io/badge/Grafana-F46800?style=flat&logo=grafana&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=flat&logo=prometheus&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-private-lightgrey?style=flat)
![Status](https://img.shields.io/badge/status-in%20development-yellow?style=flat)

Internal ops tool for monitoring all client projects from a single Grafana Cloud instance. Not a client deliverable — this is agency infrastructure.

Each client VPS runs a lightweight agent stack (grafana-agent + node-exporter + blackbox-exporter) that scrapes metrics locally and ships them to Grafana Cloud via remote_write. All clients are visible in one dashboard, separated by a `client` label.

## What it monitors

| Category | Metrics |
|---|---|
| Uptime | HTTP probe success/failure per client app URL |
| Response time | HTTP probe duration per endpoint |
| Request volume | Requests/sec per client service |
| Infrastructure | CPU %, memory %, disk % per VPS |
| API costs | Token usage per client per AI provider (Mistral, OpenAI, etc.) |

## Architecture

```
Client A VPS                    Client B VPS
┌─────────────────────┐         ┌─────────────────────┐
│  grafana-agent      │         │  grafana-agent      │
│  node-exporter      │──────▶  │  node-exporter      │──────▶  Grafana Cloud
│  blackbox-exporter  │         │  blackbox-exporter  │         (single stack)
│  app /metrics       │         │  app /metrics       │
└─────────────────────┘         └─────────────────────┘
  CLIENT_LABEL=client-a           CLIENT_LABEL=client-b
```

## Stack

| Component | Purpose |
|---|---|
| `grafana-agent` | Scrapes all exporters, remote_writes to Grafana Cloud |
| `node-exporter` | CPU, RAM, disk for the host |
| `blackbox-exporter` | HTTP uptime probes for client app URLs |
| Client app `/metrics` | Request volume, API token usage (added per project) |

## Files

```
dashboard/
├── docker-compose.yml          # grafana-agent + node-exporter + blackbox-exporter
├── agent-config.yml            # scrape configs + remote_write to Grafana Cloud
├── blackbox.yml                # HTTP probe module config
├── .env.example                # credentials template — copy to .env
├── prometheus/
│   └── rules.yml               # alerting rules
└── dashboards/
    └── agency-overview.json    # importable Grafana dashboard
```

## Setup

### 1. Get Grafana Cloud credentials

1. Go to [grafana.com](https://grafana.com) → your stack → **Details**
2. Find **Prometheus** → copy the **Remote Write Endpoint** URL and **Username** (numeric ID)
3. Go to **Access Policies** → create a token with **MetricsPublisher** role

### 2. Configure environment

```bash
cp .env.example .env
# Fill in GRAFANA_CLOUD_URL, GRAFANA_CLOUD_USER, GRAFANA_CLOUD_API_KEY, CLIENT_LABEL
```

### 3. Add client URLs to monitor

Edit `agent-config.yml` under `job_name: blackbox_http`:

```yaml
static_configs:
  - targets:
      - https://your-client-app.com/health
      - https://another-client.com/health
```

### 4. Deploy on the VPS

```bash
# Install Docker if not present
curl -fsSL https://get.docker.com | sh

# Clone this repo onto the VPS, then:
cd dashboard/
cp .env.example .env   # fill in credentials
docker compose up -d
```

Each VPS gets its own `CLIENT_LABEL` in `.env` (e.g. `metabelly-vps`, `client-b-vps`).

### 5. Import the Grafana dashboard

1. Grafana Cloud → **Dashboards** → **Import**
2. Upload `dashboards/agency-overview.json`
3. Select your Prometheus datasource

## Adding a new client

1. Deploy this stack on their VPS with a unique `CLIENT_LABEL`
2. Add their app URL to `agent-config.yml` under `blackbox_http`
3. Add a new `app_metrics` scrape block pointing to their `/metrics` port
4. Restart: `docker compose restart grafana-agent`

## API cost tracking

Each client app must expose a Prometheus counter at `/metrics`:

```python
from prometheus_client import Counter

api_tokens_used = Counter(
    "api_tokens_used_total",
    "Total API tokens consumed",
    ["client", "provider"]
)

# Call after each API request:
api_tokens_used.labels(client="metabelly", provider="mistral").inc(response.usage.total_tokens)
```

The dashboard **API Cost Tracking** panels pick this up automatically.

## Alerting

Rules are in `prometheus/rules.yml`. To activate in Grafana Cloud:

1. **Alerting** → **Alert rules** → **Import**

| Alert | Threshold | Severity |
|---|---|---|
| App down | 2+ minutes | critical |
| Slow response | > 3s for 5 min | warning |
| High CPU | > 85% for 10 min | warning |
| High memory | > 90% for 5 min | warning |
| Low disk | > 85% full | warning |
| High API spend | > 50k tokens/day | warning |
