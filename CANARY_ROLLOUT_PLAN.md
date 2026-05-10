# Production Rollout Plan: New Alert Pipeline (v2.0)

## Overview
This document defines a 10-stage canary rollout for the new production-grade alert pipeline, designed to achieve:
- **Crash rate**: 0 (protected by try/catch + metrics.record_exception())
- **Latency**: p50 <500ms, p95 <2s (validated by bounded queue + worker pool)
- **False positives**: <N-consensus suppressions + exponential backoff
- **Queue drops**: <0.1% (backpressure sampling at 80% capacity)

**Risk Profile**: MEDIUM — Well-tested core, proven patterns (consensus, cooldown), but high-scale deployment (1,000+ vehicles) and mobile integration are new.

---

## Stage 1: Development Validation (Week 1)
**Goal**: Confirm core functionality in controlled environment

### 1.1 Unit Tests
- Run `pytest server/tests/test_alerts_pipeline.py -v`
- Coverage requirements:
  - [ ] Geometry: 100% (haversine, bbox, polyline, edge cases)
  - [ ] Evaluator: 100% (off-route, consensus, cooldown logic)
  - [ ] Queue: 95% (enqueue, drop, sampling)
- **Pass criteria**: All tests green, no flaky tests

### 1.2 Integration Tests (Backend + Frontend)
```bash
# Backend: Create integration test harness
pytest server/tests/test_integration_alerts.py -v

# Frontend: Component tests
npm run test -- AlertsTable.test.jsx

# E2E: Simulate 100 GPS points through full pipeline
python server/tests/e2e_pipeline_test.py --vehicle_count 10 --duration_sec 60
```

### 1.3 Stress Test (Single Machine)
```bash
# Simulate 1,000 vehicles @ 1 update/sec (1,000 events/sec total)
python server/tests/stress_test.py \
  --vehicle_count 1000 \
  --event_rate_per_sec 1 \
  --duration_sec 300 \
  --assert_latency_p95_ms 2000 \
  --assert_exception_rate 0 \
  --assert_queue_drop_rate 0.001
```

**Acceptance Criteria**:
- [ ] p50 latency <500ms, p95 <2s, p99 <5s
- [ ] Exception rate = 0 (monitored via metrics.record_exception())
- [ ] Queue drops <0.1%
- [ ] No UI blocking (frontend renders <100ms per update)

**Responsible**: QA Lead + Backend Lead
**Time**: 3-5 days
**Blockers**: None

---

## Stage 2: Internal Staging (Week 1-2)
**Goal**: Validate on production-like infrastructure (3-5 pilot employees, 10 vehicles)

### 2.1 Environment Setup
- [ ] Deploy alerts_pipeline.py + telemetry_views.py to staging backend (port 8000)
- [ ] Configure Django settings: `USE_NEW_ALERT_PIPELINE = False` (disabled by default)
- [ ] Deploy AlertsTable.jsx + alert-evaluator.worker.js to frontend (port 5174)
- [ ] Set up Prometheus + Grafana with monitoring_dashboard.json
- [ ] Configure PagerDuty alerts (exceptions, queue >80%, latency p95 >2s)

### 2.2 Pilot Test (48 hours)
- [ ] Enable for 5 internal drivers (fleet PILOT_001)
- [ ] Manually verify using POST /api/telemetry/set_feature_flag/ with enabled=true
- [ ] Drivers conduct 2-3 normal shifts with all features
- [ ] Collect metrics:
  - Latency: p50, p95, p99 (from /api/telemetry/metrics/)
  - Exception count (target: 0)
  - Queue utilization (target: <80%)
  - Alerts generated (spot-check against old system)

### 2.3 Failure Injection Test
```python
# Simulate grid failures to test fallback & recovery
python server/tests/failure_injection_test.py --failures [
  "polyline_malformed",
  "route_missing",
  "coords_nan",
  "queue_full",
  "worker_crash"
]
```

**Acceptance Criteria**:
- [ ] No application crashes (exception_rate = 0)
- [ ] Latency SLOs met
- [ ] Fallback to legacy system works (set_feature_flag → false)
- [ ] Monitoring dashboard shows clean data
- [ ] All 5 pilot drivers confirm no issues

**Responsible**: DevOps + QA Lead
**Time**: 5-7 days
**Blockers**: None

---

## Stage 3: Canary Rollout - Wave 1 (Week 2)
**Goal**: Deploy to 3-5 paying customers with small vehicle fleets (10-50 vehicles total)

### 3.1 Customer Selection
- Select 3-5 customers with:
  - Fleet size 10-50 vehicles
  - Regular urban routes (predictable telemetry)
  - Support access for troubleshooting
  - Willingness to provide feedback
- **Example customers**: Small parcel delivery, field service, rental companies

### 3.2 Rollout Procedure
```bash
# 1. Set feature flag in customer's backend config
POST /api/telemetry/set_feature_flag/
{
  "enabled": true,
  "customer_id": "CUST_001"
}

# 2. Monitor for 24 hours
# - Watch /api/telemetry/metrics/ every 5 min
# - Check Grafana dashboard for anomalies
# - Have on-call engineer ready

# 3. If healthy, proceed; if issues, rollback:
POST /api/telemetry/set_feature_flag/
{
  "enabled": false,
  "customer_id": "CUST_001"
}
```

### 3.3 Validation Checkpoints (Every 6 hours)
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Exception rate | 0/sec | ? | ⚪ |
| Latency p50 | <500ms | ? | ⚪ |
| Latency p95 | <2s | ? | ⚪ |
| Queue drops | <0.1% | ? | ⚪ |
| Alerts false +ve | <N-consensus | ? | ⚪ |

### 3.4 Rollback Criteria
- **Automatic rollback** (via monitoring + PagerDuty alert):
  - Exception rate >0.1/sec for 10 min
  - Latency p95 >2s for 15 min continuously
  - Queue drop rate >0.1% for 5 min
  - Any crash reported by customer

**Acceptance Criteria**:
- [ ] All 3-5 customers report no issues
- [ ] All metrics within SLO for 72 hours
- [ ] Zero customer support escalations

**Responsible**: DevOps + On-Call Engineer
**Time**: 72 hours per wave
**Blockers**: Customer availability, monitoring setup

---

## Stage 4: Canary Rollout - Wave 2 (Week 3)
**Goal**: Expand to 10-15 customers (50-200 vehicles total, ~5-10 events/sec total load)

**Same procedure as Wave 1**, scaled to 10-15 smaller customers.

**Additional validation**:
- [ ] No rate limiter violations (max 10 events/sec per device)
- [ ] Database replication lag <1s (if using PostgreSQL replication)
- [ ] Mobile app (if deployed) shows no crashes

---

## Stage 5: Broad Canary (Week 4)
**Goal**: Deploy to 50% of customers (500+ vehicles, 50-100 events/sec load)

### 5.1 Pre-Broad Rollout Checklist
- [ ] All previous waves stable for >2 weeks
- [ ] Mobile app (DriverApp.jsx) tested on 10+ devices (iOS + Android)
- [ ] Database schema migrated to PostgreSQL (production-grade)
- [ ] Monitoring dashboard integrated with company alert system
- [ ] Rollback procedure documented and tested
- [ ] Support team trained on new system

### 5.2 Feature Flags
```json
{
  "use_new_alert_pipeline": true,
  "use_web_worker_frontend": false,  // Optional
  "use_mobile_local_evaluation": false,  // Optional
  "pilot_fleet_ids": ["CUST_001_PILOT", ..., "CUST_050_PILOT"]
}
```

### 5.3 Monitoring Escalation
- [ ] Set up Slack channel #alerts-pipeline-prod
- [ ] PagerDuty escalation policy (critical → on-call engineer → manager)
- [ ] Daily digest email with metrics snapshot

---

## Stage 6: General Availability (Week 5)
**Goal**: Enable for all customers (1,000+ vehicles, 100-500 events/sec)

### 6.1 Pre-GA Checklist
- [ ] Broad canary stable for >1 week, no production incidents
- [ ] Documentation updated (API, troubleshooting, ops runbook)
- [ ] Support team reports zero escalations (or only trivial config issues)
- [ ] Analytics show customer satisfaction >95%

### 6.2 Cutover Procedure
```bash
# Set global feature flag
config/alerts_config.json:
{
  "feature_flags": {
    "use_new_alert_pipeline": true  // Default true for all new tenants
  }
}

# Gradual migration of existing tenants (over 48 hours)
for each customer_id in all_customers:
  POST /api/telemetry/set_feature_flag/ {enabled: true}
  wait 30 minutes
  check metrics
  if any issue: rollback this customer

# Remove legacy pipeline code (after 30 days of GA)
```

### 6.3 Post-GA Monitoring (30 days)
- [ ] Daily metrics review (latency, exceptions, queue)
- [ ] Weekly customer feedback review
- [ ] Bug bounty program active
- [ ] Incident response SLA: Critical <15min, High <1hr

---

## Stage 7-10: Optimization & Feature Expansion
After GA stability (Week 6+):

### Stage 7: Web Worker Frontend (Optional)
- Deploy alert-evaluator.worker.js to 10% of clients
- Measure: Does it reduce UI blocking? (target: <50ms)
- If yes, roll out to 100%

### Stage 8: Mobile App (Optional)
- Deploy DriverApp.jsx to 5% of drivers
- Measure: Does it reduce backend load? Battery drain acceptable?
- If yes, expand to 100%

### Stage 9: Advanced Features
- Per-fleet tuning (custom AlertConfig JSON)
- Machine learning for route prediction (reduce false positives)
- Replay pipeline for audit/debugging

### Stage 10: Production Hardening
- Kubernetes migration (auto-scaling workers)
- Multi-region failover
- Compliance audits (GDPR, SOC2)

---

## Rollback Procedure (Anytime)

### Quick Rollback (5 minutes)
```bash
# 1. Kill alerts_pipeline processes
pkill -f alerts_pipeline

# 2. Set global feature flag to false
POST /api/telemetry/set_feature_flag/ {enabled: false}

# 3. Restart legacy alert service
systemctl start alerts-legacy

# 4. Notify team
slack-notify "CRITICAL: Alert pipeline disabled, reverted to legacy"
```

### Database Rollback (if schema change)
```sql
-- Ensure schema compatibility (should be backward compatible)
-- If not, restore from backup:
-- 1. Stop backend
-- 2. pg_restore -d fleet_prod backup.sql
-- 3. Restart backend with old code
```

### Metrics Cleanup
- Discard metrics from failed deployment
- Rebuild Grafana dashboards to show only successful waves

---

## Success Criteria (End of Stage 6)

| Criterion | Target | How to Verify |
|-----------|--------|---------------|
| **Crash Rate** | 0 (100% uptime) | Exception count = 0 in /api/telemetry/metrics/ |
| **Latency p50** | <500ms | Prometheus histogram_quantile(0.50, ...) |
| **Latency p95** | <2s | Prometheus histogram_quantile(0.95, ...) |
| **Latency p99** | <5s | Prometheus histogram_quantile(0.99, ...) |
| **Queue Drops** | <0.1% | alert_pipeline_dropped_events_total / ingest_total |
| **False Positives** | <N-consensus | alert_pipeline_false_positive_suppressions_total >99% |
| **Customer Satisfaction** | >95% | NPS survey, support tickets |
| **Data Accuracy** | 100% | Automated replay test against historical data |
| **SLA Compliance** | 99.99% | PagerDuty incident report |

---

## Decision Gate Approval

Each stage requires sign-off from:
- [ ] **QA Lead**: All tests passing
- [ ] **DevOps Lead**: Infrastructure ready, monitoring green
- [ ] **Backend Lead**: Code review passed, no technical debt
- [ ] **Product Lead**: Customer impact assessed, communication ready

Sign-off template:
```
Stage [N] Approved: [Name] on [Date]
Expected completion: [Date]
Rollback plan: [Decision gate criteria]
Risk assessment: [MEDIUM/LOW/HIGH]
```

---

## Communication Plan

### Before Rollout
- Email to customers: "New alert system v2.0 coming" (value prop, no worries)
- Internal wiki: Architecture, troubleshooting guide
- Support training: Q&A session

### During Rollout
- Slack updates (hourly to /alerts-pipeline-prod channel)
- Metrics dashboard link in Slack
- Status page update (if using status.io)

### After Rollout
- Success email to customers
- Blog post: "How we built production-grade alerts" (technical deep-dive)
- Retrospective: What went well, what to improve

---

## Cost & Resource Plan

| Stage | Duration | Resources | Est. Cost |
|-------|----------|-----------|-----------|
| 1-2 (Dev/Staging) | 10 days | 2 engineers, 1 QA | $2,000 |
| 3-5 (Canary waves) | 21 days | 1 DevOps (on-call), 1 engineer | $5,000 |
| 6 (GA) | 5 days | 1 DevOps, 1 engineer, support | $2,000 |
| 7-10 (Optimization) | ongoing | 0.5 engineers (part-time) | $1,000/month |
| **Total** | **6 weeks** | **~$10,000** | |

---

## Appendix: Monitoring Checklist

### Daily (First 30 days post-GA)
- [ ] Exception rate = 0
- [ ] Latency p95 <2s
- [ ] Queue utilization <80%
- [ ] No customer complaints

### Weekly (Months 1-3)
- [ ] All metrics reviewed
- [ ] Incident postmortem (if any)
- [ ] Performance optimization review

### Monthly (Month 3+)
- [ ] Feature parity audit (new system vs. legacy)
- [ ] Cost analysis (infrastructure usage)
- [ ] Roadmap: Deprecate legacy system? (if no issues)

---

## Questions & Escalation

**Q: What if p95 latency is 2.1s (just above SLO)?**
A: Analyze root cause (queue full? slow geometry?); optimize bottleneck; if <10% violation, proceed with monitoring.

**Q: Can we skip Wave 1 and go straight to 50% rollout?**
A: Not recommended. Previous stages catch issues before they scale. Skip at your own risk.

**Q: Should we keep the legacy pipeline running in parallel?**
A: Yes, for 30 days post-GA. Helps with debugging customer issues. After 30 days, if stable, decommission.

---

**Document Owner**: Backend Lead  
**Last Updated**: [Date]  
**Next Review**: 1 week post-GA
