# Monitoring Lokalt - Lärguide

En komplett guide för att lära dig Prometheus, Grafana, Loki och Jaeger lokalt.

## 🚀 Snabb Start

### Starta Monitoring Stack

```bash
docker-compose -f backend/docker-compose.monitoring.yml up -d
```

### Öppna Dashboard (via Caddy)

Alla tjänster är tillgängliga via Caddy reverse proxy:

- **Prometheus:** http://monitoring.hey.local (Metrics collection)
- **Grafana:** http://grafana.hey.local (admin / admin)
- **Alertmanager:** http://alertmanager.hey.local (Alert management)
- **Jaeger:** http://jaeger.hey.local (Distributed tracing)
- **Loki:** http://loki.hey.local (Log aggregation)

**Direkta portar (för debugging):**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- Alertmanager: http://localhost:9093
- Jaeger: http://localhost:16686
- Loki: http://localhost:3100

## 📊 Vad Är Vad?

### **Prometheus** - Metrics Collection
Samlar in **numeriska mätningar** från dina tjänster:
- CPU-användning
- Minne
- Requests per sekund
- API response time
- Error rates

**Port:** 9090

```bash
# Se alla tillgängliga metrics
curl http://localhost:9090/api/v1/query?query=up

# Se alla targets (tjänster som skickar metrics)
curl http://localhost:9090/api/v1/targets
```

### **Grafana** - Visualization
Skapar vackra **dashboards** av Prometheus metrics:
- Realtids grafer
- Historiska trender
- Alarmer
- Alerts

**Port:** 3001 (admin/admin)

### **Alertmanager** - Alert Management
Hanterar **varningar**:
- Grupperar alerts
- Router till rätt mål (Slack, email, etc)
- Undviker duplicate alerts

**Port:** 9093

### **Jaeger** - Distributed Tracing
Visualiserar **request flows** genom systemet:
- Vilka services ett request passerar
- Tidsmätningar mellan services
- Bottleneck identifiering

**Port:** 16686

### **Loki** - Log Aggregation
Samlar **loggar** från alla containers:
- Sökbar log history
- Snabb log querying
- Integration med Grafana

**Port:** 3100

## 🎯 Prometheus - Lär Dig First

### Vad samlar Prometheus in?

Prometheus scraper (hämtar) metrics från endpoints som:
- `/metrics` på port 8080 (workers)
- `/metrics` på port 9100 (node-exporter)

Varje metric är en **tid-serie** (Time Series Data):
```
metric_name{label1="value1", label2="value2"} 42.5 1634567890
```

Exempel:
```
node_cpu_seconds_total{cpu="0", mode="user"} 12345.6 1634567890
http_request_duration_seconds_bucket{le="0.1", path="/api/users"} 150 1634567890
```

### Prometheus Query Language (PromQL)

**Visa alla metrics:**
```
up
```

**Räkna antal failed requests:**
```
rate(http_requests_failed_total[5m])
```

**CPU usage av ditt system:**
```
rate(node_cpu_seconds_total{mode!="idle"}[5m])
```

**Minne i procent:**
```
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100
```

### Öva PromQL

1. Gå till http://localhost:9090
2. Klick på "Targets" - se vad som skickar metrics
3. Gå till "Graph" tab
4. Prova dessa queries:

```promql
# Se systemuptime
up

# CPU usage last 5 minutes
rate(node_cpu_seconds_total[5m])

# Memory usage
node_memory_MemAvailable_bytes

# Disk usage
node_filesystem_avail_bytes
```

Klick **Execute** för att se resultat.

## 📈 Grafana - Visualisering

### Logga In

1. Gå till http://localhost:3001
2. Logga in: admin / admin
3. Byt lösenord (du får prompt)

### Se Datasources

1. Settings (gear icon, bottom left) → Data Sources
2. Du bör se:
   - **Prometheus** (Metrics)
   - **Loki** (Logs)
   - **Jaeger** (Traces)

### Skapa Din Första Dashboard

#### Dashboard 1: System Health

1. **Home** → **Create** → **Dashboard**
2. **Add panel**
3. I "Metrics browser", sök på `node_`
4. Välj `node_memory_MemAvailable_bytes`
5. Byt title till "Available Memory"
6. **Apply**
7. **Save dashboard**

#### Dashboard 2: HTTP Requests

1. **Add panel**
2. Sök på `http_requests_total`
3. Lägg till query:
```promql
rate(http_requests_total[5m])
```
4. Byt title till "Requests/sec"
5. **Apply**

#### Dashboard 3: Error Rate

1. **Add panel**
2. Query:
```promql
rate(http_requests_failed_total[5m]) / rate(http_requests_total[5m]) * 100
```
3. Title: "Error Rate %"
4. Set unit to "percent (0-100)" i panel options
5. **Apply**

### Lägg Till Loki (Logs)

1. **Add panel**
2. I "Datasource" dropdown, välj **Loki**
3. Klick "code" toggle
4. Skriv:
```logql
{container="hey-sh-api"}
```
5. Title: "API Logs"
6. **Apply**

## 🚨 Alerting - Skapa Varningar

### Prometheus Alerts (alerts.yaml)

Alerts definieras i `backend/monitoring/alerts.yaml`:

```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate too high"
```

### Testa Alert

1. Gå till Prometheus: http://localhost:9090/alerts
2. Du ser alla configured alerts
3. "Pending" = villkor uppnåtts men inte triggat ännu
4. "Firing" = alert är aktiv

### Alertmanager GUI

1. Öppna http://localhost:9093
2. Se all aktiva alerts
3. Du kan "silence" (stänga av) alerts tillfälligt

## 🔍 Jaeger - Distributed Tracing

### Öppna Jaeger

http://localhost:16686

### Förstå Traces

En **trace** är en resa ett request gör genom systemet:

```
Client Request
    ↓
API Server (100ms)
    ├─ Database Query (40ms)
    ├─ Cache Lookup (10ms)
    └─ Worker Call (50ms)
        └─ AI Processing (45ms)
    ↓
Response
```

### Visualisera Traces

1. I Jaeger UI, välj service från dropdown
2. Välj operation
3. Klick **Find Traces**
4. Klick en trace för detaljerna
5. Se vilka services som tog tid

### Identifiera Bottlenecks

Om ett request är långsamt:
1. Öppna tracen i Jaeger
2. Se vilken service tog längst tid
3. Fokusera optimization där

## 📝 Loki - Logs

### Logga In I Grafana

1. Create → Panel → Choose Loki datasource
2. Skapa log query:

```logql
# Se alla API logs
{container="hey-sh-api"}

# Se bara ERROR logs
{container="hey-sh-api"} | "ERROR"

# Se logs från specifik worker
{job="hey-sh-general-worker"}

# Rate of errors
rate({container="hey-sh-api"} | "ERROR" [5m])
```

### Log Levels I Loki

Loki parsar automatiskt log levels:
```logql
{container="hey-sh-api"} | level="error"
```

## 🎓 Hands-On Övningar

### Övning 1: Skapa Error Scenario

1. Starta en container som genererar errors:
```bash
docker run -d \
  --name test-error-gen \
  -e ERROR_RATE=0.5 \
  curlimages/curl \
  sh -c "while true; do curl http://hey-sh-api:8000/health; sleep 1; done"
```

2. Öppna Prometheus: http://localhost:9090
3. Query:
```promql
rate(http_requests_failed_total[1m])
```
4. Ser du error rate öka?

### Övning 2: Track Memory Leak

1. Skapa dashboard med:
```promql
node_memory_MemAvailable_bytes
```

2. Se memory trend över tid
3. Om memory minskar konstant = memory leak

### Övning 3: Correlate Logs and Metrics

1. I Grafana dashboard
2. Lägg till både metrics och logs panels
3. Se correlation mellan error spikes och error logs

## 📚 Viktiga Koncept

### Time Series

En metrik är en **tidsserie** av värden:
```
CPU_usage: [10, 12, 11, 15, 13, 14] över tid
```

### Labels

Labels gör metrics sökbara:
```
http_requests_total{method="GET", path="/users", status="200"}
http_requests_total{method="POST", path="/users", status="400"}
```

### Rate vs Gauge

- **Rate:** Förändring över tid (`rate(metric[5m])`)
  - Request rate
  - Error rate
  - Network throughput

- **Gauge:** Aktuellt värde vid en tidpunkt
  - Memory usage
  - Temperature
  - Active connections

### Recording Rules

Prometheus kan förberäkna metrics:
```yaml
- record: job:http_requests_per_second:rate5m
  expr: rate(http_requests_total[5m])
```

Sparar CPU genom att cache frequent queries.

## 🛠️ Felsökning

### Prometheus visar ingen data

**Problem:** Metrics inte samlade

**Lösning:**
1. Kolla targets: http://localhost:9090/targets
2. Se om endpoints är "UP"
3. Om "DOWN", kolla network connectivity

```bash
# Test metrics endpoint
curl http://localhost:9100/metrics
```

### Grafana panels är tomma

**Problem:** Datasource inte connected

**Lösning:**
1. Settings → Data Sources
2. Klick Prometheus → Test
3. Se error message
4. Fixa URL eller credentials

### Alertmanager visar ingen alerts

**Problem:** Prometheus inte connected

**Lösning:**
1. Kolla prometheus-config.yaml:
```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

2. Restart Prometheus:
```bash
docker-compose -f backend/docker-compose.monitoring.yml restart prometheus
```

## 🎯 Nästa Steg

1. **Läs mer om PromQL:** https://prometheus.io/docs/prometheus/latest/querying/basics/
2. **Grafana dashboards:** https://grafana.com/grafana/dashboards/
3. **Setup real alerts:** Integrera med Slack/Email
4. **Deploy to production:** Använda Prometheus Operator

## 📖 Resurser

- Prometheus docs: https://prometheus.io/docs/
- Grafana docs: https://grafana.com/docs/grafana/latest/
- Loki docs: https://grafana.com/docs/loki/latest/
- Jaeger docs: https://www.jaegertracing.io/docs/

## Kommandoreferens

```bash
# Se alla services
docker-compose -f backend/docker-compose.monitoring.yml ps

# Se logs från Prometheus
docker-compose -f backend/docker-compose.monitoring.yml logs prometheus

# Restart stack
docker-compose -f backend/docker-compose.monitoring.yml restart

# Stoppa stack
docker-compose -f backend/docker-compose.monitoring.yml down

# Stoppa och rensa data
docker-compose -f backend/docker-compose.monitoring.yml down -v
```
