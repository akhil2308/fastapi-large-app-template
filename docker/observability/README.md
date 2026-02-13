# Observability Stack - Local Development

This directory contains the Docker Compose setup for local observability with Grafana, Prometheus, Tempo, and OpenTelemetry Collector.

## Services

| Service | Port | Description |
|---------|------|-------------|
| Grafana | 3000 | Visualization UI for metrics and traces |
| Prometheus | 9090 | Metrics storage and querying |
| Tempo | 3200 | Trace storage and querying |
| OTEL Collector | 4317 | OTLP receiver, exports to Prometheus and Tempo |

## Quick Start

1. Start the observability stack:

```bash
cd docker/observability
docker compose up -d
```

2. Access Grafana at http://localhost:3000

3. Configure your FastAPI app to send OTLP data to the collector:

```bash
# In your .env file, set:
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## Architecture

```
FastAPI App --> OTEL Collector --> Prometheus (metrics)
                      |
                      +-> Tempo (traces)

Grafana <-- Prometheus
Grafana <-- Tempo
```

## Grafana

- **URL**: http://localhost:3000
- **Default login**: admin/admin (or skip for anonymous)
- **Dashboards**: Pre-configured datasources for Prometheus and Tempo
- **Trace to Metrics**: Enabled for linking traces to metrics

> ⚠️ **Security Note**: Anonymous admin access is enabled for local development only.

## Prometheus

- **URL**: http://localhost:9090
- Scrapes metrics from OTEL Collector (otel-collector:9464)

## Tempo

- **URL**: http://localhost:3200
- Receives traces from OTEL Collector via OTLP gRPC (4317)

## OTEL Collector

- **OTLP gRPC**: localhost:4317
- **Prometheus metrics**: localhost:9464

## Usage with FastAPI App

The FastAPI app is already configured to send OTLP data. Ensure your `.env` file has:

```env
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_SERVICE_NAME=fastapi-app
```

## Viewing Traces

1. In Grafana, go to Explore
2. Select "Tempo" datasource
3. Search for traces using service name, operation, or tags
4. Click on a trace to view details
5. Use "Trace to Metrics" to jump to related metrics

## Stopping

```bash
docker compose down
```

To remove volumes (reset all data):

```bash
docker compose down -v
```
