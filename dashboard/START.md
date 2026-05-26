# Agency Dashboard

[Open Dashboard](https://eugnmueller87.grafana.net/d/agency-overview-v1/agency-overview?orgId=1&from=now-24h&to=now&timezone=browser&refresh=1m)

## Quick links

| Section | Direct link |
|---|---|
| Uptime | [→ Uptime](https://eugnmueller87.grafana.net/d/agency-overview-v1/agency-overview?orgId=1&from=now-24h&to=now&timezone=browser&refresh=1m&viewPanel=1) |
| Token Consumption | [→ Tokens](https://eugnmueller87.grafana.net/d/agency-overview-v1/agency-overview?orgId=1&from=now-24h&to=now&timezone=browser&refresh=1m&viewPanel=10) |
| Cost & Retainer | [→ Cost](https://eugnmueller87.grafana.net/d/agency-overview-v1/agency-overview?orgId=1&from=now-24h&to=now&timezone=browser&refresh=1m&viewPanel=20) |
| Tier Thresholds | [→ Tiers](https://eugnmueller87.grafana.net/d/agency-overview-v1/agency-overview?orgId=1&from=now-24h&to=now&timezone=browser&refresh=1m&viewPanel=30) |

## Stack

- **Grafana Cloud** — dashboards & alerts
- **Grafana Agent** — scrapes metrics, remote-writes to cloud
- **Blackbox Exporter** — HTTP uptime probes
- **Node Exporter** — server infrastructure metrics
- **App /metrics** — token consumption, request rate (per client app)

## Tier thresholds

| Tier | Tokens / day |
|---|---|
| Tier 1 | < 100,000 |
| Tier 2 | 100,000 – 500,000 |
| Tier 3 | 500,000+ |
