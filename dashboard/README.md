# Agency Dashboard — Grafana + Prometheus

Monitors all client projects from one place. Runs on each client VPS; data ships to Grafana Cloud.

## Stack

| Component | Purpose |
|---|---|
| `grafana-agent` | Scrapes metrics, remote_writes to Grafana Cloud |
| `node-exporter` | CPU, RAM, disk for the host |
| `blackbox-exporter` | HTTP uptime probes for client app URLs |
| Client app `/metrics` | Request volume, API token usage (added per project) |

## Setup

### 1. Get Grafana Cloud credentials

1. Go to [grafana.com](https://grafana.com) → your stack → **Prometheus**
2. Copy the **Remote Write Endpoint** URL
3. Copy your **numeric User ID**
4. Go to **Access Policies** → create a token with **MetricsPublisher** role

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Grafana Cloud credentials and a client label
```

### 3. Add client URLs to monitor

Edit `agent-config.yml` under `job_name: blackbox_http` → add each client's health check URL:

```yaml
static_configs:
  - targets:
      - https://your-client-app.com/health
      - https://another-client.com/health
```

### 4. Deploy on each VPS

```bash
# Install Docker + Docker Compose if not present
curl -fsSL https://get.docker.com | sh

# Clone or copy the dashboard/ folder to the VPS
# Then:
docker compose up -d
```

Each VPS gets its own `CLIENT_LABEL` in `.env` (e.g. `metabelly-vps`, `client-b-vps`).

### 5. Import the Grafana dashboard

1. In Grafana Cloud → **Dashboards** → **Import**
2. Upload `dashboards/agency-overview.json`
3. Select your Prometheus datasource

## Adding a new client

1. Deploy this stack on their VPS with a unique `CLIENT_LABEL`
2. Add their app URL to `agent-config.yml` under `blackbox_http`
3. Add a new `app_metrics` scrape block pointing to their `/metrics` port
4. Restart the agent: `docker compose restart grafana-agent`

## API cost tracking

Client apps must expose a Prometheus counter:

```python
# Example (Python + prometheus_client)
from prometheus_client import Counter

api_tokens_used = Counter(
    "api_tokens_used_total",
    "Total API tokens consumed",
    ["client", "provider"]   # e.g. client="metabelly", provider="mistral"
)

# After each API call:
api_tokens_used.labels(client="metabelly", provider="mistral").inc(usage.total_tokens)
```

The dashboard picks this up automatically under **API Cost Tracking**.

## Alerting

Rules are in `prometheus/rules.yml`. Upload them to Grafana Cloud:

1. Grafana Cloud → **Alerting** → **Alert rules** → **Import**
2. Or configure via the Grafana Agent's `rule_files` field

Current alerts:
- App down for 2+ minutes → **critical**
- Response time > 3s for 5+ minutes → **warning**
- CPU > 85% for 10+ minutes → **warning**
- Memory > 90% for 5+ minutes → **warning**
- Disk > 85% → **warning**
- API tokens > 50k/day per client → **warning**
