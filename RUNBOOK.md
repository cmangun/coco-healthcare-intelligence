# CoCo Operations Runbook

**Last Updated:** 2024-12-01  
**Owner:** ML Platform Team  
**On-Call Rotation:** PagerDuty - `coco-oncall`

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start all services | `docker compose up -d` |
| Stop all services | `docker compose down` |
| View logs | `docker compose logs -f coco-api` |
| Check health | `curl http://localhost:8000/health` |
| Page on-call | PagerDuty: `coco-oncall` |

---

## 1. How to Start

### Full Stack (Production-like)

```bash
cd /path/to/coco-healthcare-intelligence

# Start all services
docker compose up -d

# Verify services are healthy
docker compose ps

# Expected output: All services "healthy" or "running"
```

### Individual Services

```bash
# API only (for development)
docker compose up -d coco-api postgres redis

# Monitoring stack only
docker compose up -d prometheus grafana jaeger

# Full ML stack
docker compose up -d coco-api postgres redis mlflow qdrant feast
```

### Verify Startup

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"healthy","services":{"database":"up","redis":"up","mlflow":"up"}}

# Readiness check
curl http://localhost:8000/ready
# Expected: {"ready":true}
```

---

## 2. How to Stop

### Graceful Shutdown

```bash
# Stop all services (preserves data)
docker compose down

# Stop and remove volumes (DESTRUCTIVE - loses data)
docker compose down -v
```

### Emergency Stop

```bash
# Force stop all containers
docker compose kill

# If Docker is unresponsive
sudo systemctl restart docker
```

---

## 3. How to Debug

### Service Not Starting

```bash
# Check container logs
docker compose logs coco-api --tail=100

# Check container status
docker compose ps

# Inspect container
docker inspect coco-api

# Common issues:
# - Port already in use: `lsof -i :8000`
# - Out of memory: `docker stats`
# - Missing env vars: Check .env file
```

### API Returning Errors

```bash
# Check API logs
docker compose logs -f coco-api

# Check request with verbose output
curl -v http://localhost:8000/api/v1/care-gaps/patient/P12345

# Check Jaeger for traces
open http://localhost:16686
```

### Database Connection Issues

```bash
# Check database logs
docker compose logs postgres

# Test connection
docker compose exec postgres psql -U coco -d coco -c "SELECT 1"

# Check connection pool
curl http://localhost:8000/metrics | grep db_pool
```

### Model Inference Failures

```bash
# Check MLflow
curl http://localhost:5000/health

# Check model registry
docker compose exec mlflow mlflow models list

# Check Qdrant (for RAG)
curl http://localhost:6333/health
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check Prometheus metrics
open http://localhost:9090

# Check Grafana dashboards
open http://localhost:3000
# Default credentials: admin/admin
```

---

## 4. When to Page Someone

### Page Immediately (P1)

- [ ] PHI exposure suspected
- [ ] All API endpoints returning 5xx
- [ ] Database corruption detected
- [ ] Audit chain integrity failure
- [ ] Any kill criteria triggered

**Action:** PagerDuty → `coco-oncall`

### Page During Business Hours (P2)

- [ ] Single endpoint consistently failing
- [ ] Model performance degraded >10%
- [ ] Response latency >5x normal
- [ ] Monitoring stack down

**Action:** Slack → `#coco-alerts`

### Can Wait for Next Business Day (P3)

- [ ] Intermittent errors <1%
- [ ] Non-critical feature unavailable
- [ ] Minor performance degradation
- [ ] Documentation issues

**Action:** Jira ticket

---

## 5. What Not to Change

### Never Modify in Production

| Component | Reason | Safe Alternative |
|-----------|--------|------------------|
| `audit_logger.py` | Audit chain integrity | Deploy new version via CI/CD |
| Database schema | Data integrity | Migration scripts only |
| Model weights directly | Version control | MLflow registry |
| TLS certificates manually | Security | Automated rotation |
| Environment secrets | Security | Vault/Secrets Manager |

### Change Only With Approval

| Component | Approver | Lead Time |
|-----------|----------|-----------|
| Kill criteria thresholds | CTO | 1 week |
| Cost ceiling values | Finance + Engineering | 1 week |
| HIPAA controls | Compliance | 2 weeks |
| Model architecture | ML Lead + QA | 1 sprint |

### Safe to Change

| Component | Notes |
|-----------|-------|
| Log verbosity | `LOG_LEVEL` env var |
| Feature flags | LaunchDarkly / config |
| Rate limits | API gateway config |
| Dashboard layouts | Grafana |

---

## 6. Common Scenarios

### Scenario: High Latency

1. Check Grafana latency dashboard
2. Identify slow endpoint
3. Check Jaeger traces for bottleneck
4. Common causes:
   - Database slow queries → Check `pg_stat_statements`
   - LLM API slow → Check OpenAI status
   - Memory pressure → Scale up or restart

### Scenario: Model Drift Alert

1. Check drift dashboard in Grafana
2. Compare current vs. baseline distributions
3. If PSI > 0.25:
   - Investigate data pipeline
   - Check for upstream changes
   - Escalate to ML team
4. If false positive:
   - Adjust threshold if recurring

### Scenario: Disk Space Low

1. Check which container is consuming space:
   ```bash
   docker system df
   ```
2. Clean up:
   ```bash
   docker system prune -f
   docker volume prune -f
   ```
3. If still low:
   - Rotate old logs
   - Archive old model versions
   - Expand volume

### Scenario: Rollback Required

1. Identify last known good version
2. Rollback via CI/CD:
   ```bash
   # GitOps approach
   git revert HEAD
   git push
   ```
3. Or manual rollback:
   ```bash
   docker compose pull coco-api:v1.2.3
   docker compose up -d coco-api
   ```
4. Verify rollback successful
5. Create incident ticket

---

## 7. Monitoring Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| API Overview | `grafana:3000/d/api-overview` | Request rate, latency, errors |
| Model Performance | `grafana:3000/d/model-perf` | Predictions, drift, fairness |
| Cost Telemetry | `grafana:3000/d/cost` | Spend, ROI, budget |
| Infrastructure | `grafana:3000/d/infra` | CPU, memory, disk |
| Audit Activity | `grafana:3000/d/audit` | PHI access, governance actions |

---

## 8. Escalation Path

```
L1: On-Call Engineer
    │
    ├── Can resolve: Restart, scale, rollback
    │
    └── Escalate if: Data issue, model issue, security issue
          │
          ▼
L2: ML Platform Lead
    │
    ├── Can resolve: Model changes, pipeline fixes
    │
    └── Escalate if: PHI exposure, compliance issue
          │
          ▼
L3: CTO + Compliance
    │
    └── Handles: Regulatory notification, executive communication
```

---

## 9. Contact List

| Role | Name | Contact | Backup |
|------|------|---------|--------|
| On-Call | Rotation | PagerDuty | - |
| ML Platform Lead | [Name] | [Phone] | [Backup] |
| SRE Lead | [Name] | [Phone] | [Backup] |
| Security | [Name] | [Phone] | [Backup] |
| Compliance | [Name] | [Phone] | [Backup] |

---

## 10. Post-Incident Checklist

- [ ] Immediate threat mitigated
- [ ] Stakeholders notified
- [ ] Timeline documented
- [ ] Root cause identified
- [ ] Postmortem scheduled (within 5 days)
- [ ] Action items created
- [ ] Monitoring enhanced
- [ ] Runbook updated

---

*This runbook is a living document. Update after every incident.*
