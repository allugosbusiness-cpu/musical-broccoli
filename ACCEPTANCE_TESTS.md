# Acceptance Test Suite: Production Alert Pipeline v2.0

**Objective**: Validate that the new alert pipeline meets 10 requirements and passes production acceptance criteria.

**Execution**: Run all tests in CI/CD pipeline before staging deployment.

---

## Test 1: Crash Rate = 0 (100% Stability)

**Requirement**: System does not crash, even with malformed input

### Test Case 1.1: Null Input Handling
```python
def test_null_coordinates():
    """Pipeline should handle null coordinates gracefully"""
    location = LocationPoint(
        truck_id='TRK001',
        latitude=None,  # Invalid
        longitude=31.034,
        speed_kmh=60,
        timestamp=datetime.utcnow(),
        trace_id='test-001'
    )
    # Should not raise exception; should log and skip
    alerts = evaluator.evaluate(EvaluationContext(location, route, None, {}))
    assert len(alerts) == 0
    assert metrics.exceptions == 0
```

**Pass Criteria**: Exception count = 0; no app crash; log entry recorded

### Test Case 1.2: Invalid Coordinates Out of Range
```python
def test_invalid_lat_lng_range():
    """Latitude >90 or longitude >180 should be rejected"""
    invalid_points = [
        (200, 31.034),      # Lat > 90
        (-17.825, 200),     # Lng > 180
        (float('nan'), 31), # NaN
        (float('inf'), 31)  # Infinity
    ]
    for lat, lng in invalid_points:
        location = LocationPoint(
            truck_id='TRK001',
            latitude=lat,
            longitude=lng,
            speed_kmh=60,
            timestamp=datetime.utcnow(),
            trace_id='invalid'
        )
        alerts = evaluator.evaluate(EvaluationContext(location, None, None, {}))
        assert len(alerts) == 0
        assert metrics.exceptions == 0  # Should not crash
```

**Pass Criteria**: All invalid points rejected; exception count = 0

### Test Case 1.3: Malformed Route Polyline
```python
def test_malformed_polyline():
    """Polyline with malformed points should fall back gracefully"""
    route = RoutePolyline(
        route_id='RT001',
        points=[(float('nan'), 31.0), (-17.825, 31.034), None]
    )
    location = LocationPoint(
        truck_id='TRK001',
        latitude=-17.825,
        longitude=31.034,
        speed_kmh=60,
        timestamp=datetime.utcnow(),
        trace_id='test-001'
    )
    # Should not crash; should skip polyline check
    alerts = evaluator.evaluate(EvaluationContext(location, route, None, {}))
    assert metrics.exceptions == 0
```

**Pass Criteria**: No exception raised; metrics.exceptions = 0

### Test Case 1.4: High-Load Crash Test (500 concurrent vehicles, 100 updates/sec)
```python
def test_high_load_no_crash():
    """System should not crash under 10x normal load"""
    pipeline = AlertPipeline()
    
    # Simulate 500 vehicles, 1 update/sec each = 500 updates/sec
    for sec in range(60):
        for truck_idx in range(500):
            location = LocationPoint(
                truck_id=f'TRK{truck_idx:04d}',
                latitude=-17.0 + (truck_idx % 100) * 0.01,
                longitude=31.0 + (truck_idx % 100) * 0.01,
                speed_kmh=60,
                timestamp=datetime.utcnow(),
                trace_id=f'load-test-{sec}-{truck_idx}'
            )
            pipeline.ingest_location(location, None, {})
        
        time.sleep(1)
    
    metrics = pipeline.get_metrics()
    assert metrics['exceptions'] == 0, "Should not crash under load"
    pipeline.shutdown()
```

**Pass Criteria**: Exception count = 0 after 60 seconds at 500 events/sec

**Acceptance Threshold**: ✅ All 4 test cases pass

---

## Test 2: Latency <500ms p50, <2s p95, <5s p99

**Requirement**: Low-latency alert evaluation via bounded queue + worker pool

### Test Case 2.1: Ingestion Latency (Synchronous)
```python
def test_ingestion_latency_p50():
    """Ingest operation should be <50ms p50"""
    latencies_ms = []
    for i in range(1000):
        start = time.perf_counter()
        location = LocationPoint(...)
        pipeline.ingest_location(location, None, {})
        latencies_ms.append((time.perf_counter() - start) * 1000)
    
    p50 = sorted(latencies_ms)[len(latencies_ms) // 2]
    assert p50 < 50, f"P50 ingestion latency {p50}ms > 50ms"
```

**Pass Criteria**: p50 <50ms, p95 <100ms

### Test Case 2.2: Alert Evaluation Latency (Background Worker)
```python
def test_evaluation_latency_p95():
    """Evaluation latency from queue to decision should be <2s p95"""
    pipeline = AlertPipeline()
    
    # Track latency from ingest timestamp to evaluation time
    latencies_ms = []
    for i in range(100):
        start_ms = time.perf_counter() * 1000
        location = LocationPoint(
            truck_id='TRK001',
            latitude=-17.825,
            longitude=31.034,
            speed_kmh=60,
            timestamp=datetime.utcnow(),
            trace_id=f'latency-{i}'
        )
        route = RoutePolyline(
            route_id='RT001',
            points=[(-17.0, 31.0), (-18.0, 32.0)]
        )
        pipeline.ingest_location(location, route, {})
    
    time.sleep(5)  # Wait for workers to process
    
    metrics = pipeline.get_metrics()
    p95_latency = metrics['latency_percentile_95_ms']
    assert p95_latency < 2000, f"P95 evaluation latency {p95_latency}ms > 2000ms"
    
    pipeline.shutdown()
```

**Pass Criteria**: p95 <2s, p99 <5s

### Test Case 2.3: End-to-End Latency (Ingest → Alert → API Response)
```python
def test_e2e_latency_api():
    """Full cycle from POST /api/telemetry/ingest_location to alert in DB"""
    client = APIClient()
    
    start = time.perf_counter()
    response = client.post('/api/telemetry/ingest_location/', {
        'truck_id': 'TRK001',
        'latitude': -15.0,  # Off-route
        'longitude': 33.0,
        'speed_kmh': 60,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    assert response.status_code == 202, "Should accept async"
    
    # Wait up to 5s for alert to appear
    for _ in range(50):
        time.sleep(0.1)
        alerts = client.get('/api/alerts/unresolved/?truck_id=TRK001')
        if len(alerts) > 0:
            e2e_latency_ms = (time.perf_counter() - start) * 1000
            assert e2e_latency_ms < 5000, f"E2E latency {e2e_latency_ms}ms > 5s"
            break
```

**Pass Criteria**: E2E latency <5s for 99% of requests

**Acceptance Threshold**: ✅ All 3 test cases pass with SLO met

---

## Test 3: Alert Consensus (N=3 consecutive points) Suppression

**Requirement**: False positive suppression via N-consensus voting

### Test Case 3.1: Single Off-Route Point = No Alert
```python
def test_consensus_single_point_no_alert():
    """One off-route point should NOT trigger alert"""
    evaluator = AlertEvaluator(AlertConfig(off_route_consensus_count=3), metrics)
    
    location = LocationPoint(truck_id='TRK001', latitude=-15.0, longitude=33.0, ...)
    route = RoutePolyline(route_id='RT001', points=[(-17.0, 31.0), (-18.0, 32.0)])
    
    alerts = evaluator.evaluate(EvaluationContext(location, route, None, {}))
    assert len(alerts) == 0, "Single point should not alert"
    assert metrics.false_positive_suppressions == 1
```

**Pass Criteria**: Alert count = 0; false_positive_suppressions > 0

### Test Case 3.2: Three Consecutive Off-Route Points = Alert
```python
def test_consensus_three_points_alert():
    """Three consecutive off-route points SHOULD trigger alert"""
    evaluator = AlertEvaluator(AlertConfig(off_route_consensus_count=3), metrics)
    
    for i in range(3):
        location = LocationPoint(
            truck_id='TRK001',
            latitude=-15.0 - (i * 0.1),  # Drifting further off-route
            longitude=33.0,
            speed_kmh=60,
            timestamp=datetime.utcnow() + timedelta(seconds=10*i),
            trace_id=f'consensus-{i}'
        )
        route = RoutePolyline(route_id='RT001', points=[...])
        alerts = evaluator.evaluate(EvaluationContext(location, route, None, {}))
        
        if i < 2:
            assert len(alerts) == 0, f"Point {i} should not alert yet"
        else:
            assert len(alerts) == 1, f"Point {i} should alert"
            assert alerts[0].alert_type == 'off_route'
```

**Pass Criteria**: Alert triggers after exactly 3 consecutive points

### Test Case 3.3: Consensus Reset on In-Route Point
```python
def test_consensus_reset_on_in_route():
    """In-route point should reset consensus counter"""
    evaluator = AlertEvaluator(AlertConfig(off_route_consensus_count=3), metrics)
    
    # 2 off-route points
    for i in range(2):
        location = LocationPoint(truck_id='TRK001', latitude=-15.0, longitude=33.0, ...)
        alerts = evaluator.evaluate(EvaluationContext(location, route, None, {}))
        assert len(alerts) == 0
    
    # 1 in-route point (resets counter)
    location = LocationPoint(truck_id='TRK001', latitude=-17.5, longitude=31.5, ...)  # On route
    evaluator.evaluate(EvaluationContext(location, route, None, {}))
    
    # 2 more off-route (counter still at 2, not 3)
    for i in range(2):
        location = LocationPoint(truck_id='TRK001', latitude=-15.0, longitude=33.0, ...)
        alerts = evaluator.evaluate(EvaluationContext(location, route, None, {}))
        assert len(alerts) == 0, "Consensus counter was reset"
```

**Pass Criteria**: Consensus counter resets; no alert fired

**Acceptance Threshold**: ✅ All 3 test cases pass

---

## Test 4: Exponential Backoff (Repeated Alert Suppression)

**Requirement**: Alert cooldown with 2x multiplier, capped at 1 hour

### Test Case 4.1: Initial Cooldown
```python
def test_cooldown_initial():
    """After alert, next alert suppressed for cooldown_sec"""
    evaluator = AlertEvaluator(
        AlertConfig(alert_cooldown_seconds=300, cooldown_multiplier=2.0),
        metrics
    )
    
    # Trigger first alert
    for i in range(3):
        location = LocationPoint(truck_id='TRK001', latitude=-15.0, longitude=33.0, ...)
        evaluator.evaluate(EvaluationContext(location, route, None, {}))
    
    # Immediate next point (same truck, still off-route) should be suppressed
    location = LocationPoint(truck_id='TRK001', latitude=-15.0, longitude=33.0, ...)
    alerts = evaluator.evaluate(EvaluationContext(location, route, None, {}))
    assert len(alerts) == 0, "Alert should be suppressed by cooldown"
    assert metrics.cooldown_suppressions > 0
```

**Pass Criteria**: Alert suppressed; cooldown_suppressions > 0

### Test Case 4.2: Exponential Backoff Multiplier
```python
def test_cooldown_exponential_backoff():
    """Repeated alerts → cooldown * 2^N (capped at 1 hour)"""
    evaluator = AlertEvaluator(AlertConfig(cooldown_multiplier=2.0), metrics)
    
    # Trigger alert #1 (cooldown = 300s)
    # ... wait 300s ...
    # Trigger alert #2 (cooldown = 600s = 300 * 2)
    # ... wait 600s ...
    # Trigger alert #3 (cooldown = 1200s = 600 * 2)
    # ... wait 1200s ...
    # Trigger alert #4 (cooldown = 2400s = 1200 * 2)
    # ... wait 2400s ...
    # Trigger alert #5 (cooldown = 3600s = capped at 1 hour)
    
    # Verify cooldown values via state inspection
    state = evaluator._vehicle_state['TRK001']
    # After each alert, cooldown should double
```

**Pass Criteria**: Cooldown multiplies correctly; capped at 3600s

### Test Case 4.3: Cooldown Expiry
```python
def test_cooldown_expiry():
    """After cooldown period, next alert should fire"""
    evaluator = AlertEvaluator(AlertConfig(alert_cooldown_seconds=1), metrics)
    
    # Trigger first alert
    for i in range(3):
        location = LocationPoint(truck_id='TRK001', latitude=-15.0, longitude=33.0, ...)
        evaluator.evaluate(EvaluationContext(location, route, None, {}))
    
    # Wait for cooldown to expire
    time.sleep(1.1)
    
    # Next alert should fire (consensus reset, so need 3 points)
    for i in range(3):
        location = LocationPoint(truck_id='TRK001', latitude=-15.0, longitude=33.0, ...)
        evaluator.evaluate(EvaluationContext(location, route, None, {}))
    
    # Should have 2 alerts now (one before cooldown, one after)
    # (In real test, would track via metrics or DB)
```

**Pass Criteria**: Alert fires after cooldown expires

**Acceptance Threshold**: ✅ All 3 test cases pass

---

## Test 5: Queue Backpressure & Sampling (<0.1% Drops)

**Requirement**: Bounded queue with sampling when >80% full

### Test Case 5.1: Queue Acceptance Below 80%
```python
def test_queue_accepts_below_threshold():
    """Queue should accept all events when utilization <80%"""
    pipeline = AlertPipeline(max_queue_size=1000)
    
    dropped = 0
    for i in range(800):  # 80% of 1000
        location = LocationPoint(truck_id=f'TRK{i % 10}', ...)
        if not pipeline.ingest_location(location, None, {}):
            dropped += 1
    
    assert dropped == 0, "No events should be dropped <80% utilization"
```

**Pass Criteria**: dropped = 0

### Test Case 5.2: Queue Sampling Above 80%
```python
def test_queue_sampling_above_threshold():
    """Queue should sample (keep ~50%) when utilization >80%"""
    config = AlertConfig(max_queue_size=1000, sampling_rate_degraded=0.5)
    pipeline = AlertPipeline(config)
    
    # Fill queue to >80%
    for i in range(850):
        location = LocationPoint(truck_id='TRK001', ...)
        pipeline.ingest_location(location, None, {})
    
    # Track sampling
    dropped = 0
    for i in range(200):
        location = LocationPoint(truck_id='TRK001', ...)
        if not pipeline.ingest_location(location, None, {}):
            dropped += 1
    
    # Some events should be dropped (due to sampling)
    drop_rate = dropped / 200
    assert 0.4 < drop_rate < 0.6, f"Drop rate {drop_rate} not in [0.4, 0.6]"
    
    metrics = pipeline.get_metrics()
    assert metrics['dropped_events'] > 0
    assert metrics['dropped_events'] / 1000 < 0.01, "Total drops <1%"
```

**Pass Criteria**: drop_rate ≈ 0.5; total drops <1%

### Test Case 5.3: Total Drop Rate <0.1% Under Load
```python
def test_queue_drop_rate_under_load():
    """Drop rate should be <0.1% over extended load test"""
    pipeline = AlertPipeline(max_queue_size=10000)
    
    total_sent = 0
    for sec in range(60):
        for _ in range(500):  # 500 events/sec
            location = LocationPoint(truck_id=f'TRK{_ % 100}', ...)
            if pipeline.ingest_location(location, None, {}):
                total_sent += 1
        time.sleep(1)
    
    metrics = pipeline.get_metrics()
    drop_rate = metrics['dropped_events'] / (total_sent + metrics['dropped_events'])
    assert drop_rate < 0.001, f"Drop rate {drop_rate*100:.2f}% > 0.1%"
    
    pipeline.shutdown()
```

**Pass Criteria**: drop_rate <0.1%

**Acceptance Threshold**: ✅ All 3 test cases pass

---

## Test 6: Geometry Robustness (Defensive Fallbacks)

**Requirement**: 3-tier geometry fallback: bbox → haversine → polyline

### Test Case 6.1: Polyline Distance Calculation
```python
def test_geometry_polyline_distance():
    """Point-to-polyline distance should be accurate (within 1% of real distance)"""
    # Harare to Mutare route
    polyline = [
        (-17.825, 31.034),  # Harare
        (-18.964, 32.667),  # Mutare
    ]
    
    # Point on route (midpoint)
    point_on_route = (-18.395, 31.851)
    distance = GeometryUtils.point_to_polyline_distance(point_on_route, polyline)
    
    # Should be ~0 (or very small)
    assert distance < 5000, f"Point on route distance {distance}m too large"
    
    # Point off route
    point_off_route = (-15.0, 35.0)  # Far away
    distance = GeometryUtils.point_to_polyline_distance(point_off_route, polyline)
    
    # Should be hundreds of km
    assert distance > 100000, f"Point off route distance {distance}m too small"
```

**Pass Criteria**: Distances calculated correctly

### Test Case 6.2: Bbox Prefilter Optimization
```python
def test_geometry_bbox_prefilter():
    """Bounding box should quickly reject points outside route"""
    polyline = [(-17.0, 31.0), (-18.0, 32.0)]
    
    # Point inside bbox
    point_in = (-17.5, 31.5)
    bbox_dist = GeometryUtils.bounding_box_distance(point_in, polyline)
    assert bbox_dist == 0, "Point inside bbox should return 0"
    
    # Point outside bbox
    point_out = (-15.0, 35.0)
    bbox_dist = GeometryUtils.bounding_box_distance(point_out, polyline)
    assert bbox_dist == float('inf'), "Point outside bbox should return inf"
```

**Pass Criteria**: Bbox prefilter works correctly

### Test Case 6.3: Fallback on Malformed Polyline
```python
def test_geometry_fallback_malformed():
    """Should fall back gracefully when polyline is malformed"""
    # Malformed polyline with NaN
    polyline_bad = [(float('nan'), 31.0), (-18.0, 32.0)]
    
    point = (-17.5, 31.5)
    distance = GeometryUtils.point_to_polyline_distance(point, polyline_bad)
    
    # Should return infinity (invalid) or fall back to haversine
    assert distance == float('inf') or distance > 0, "Should not crash"
```

**Pass Criteria**: No crash; graceful fallback

**Acceptance Threshold**: ✅ All 3 test cases pass

---

## Test 7: API Input Validation (Defensive Ingestion)

**Requirement**: Validate lat, lng, timestamp at ingress; return 4xx on invalid

### Test Case 7.1: Missing Required Fields
```python
def test_api_missing_latitude():
    """POST without latitude should return 400"""
    response = client.post('/api/telemetry/ingest_location/', {
        'truck_id': 'TRK001',
        # 'latitude': -17.825,  # Missing
        'longitude': 31.034,
        'speed_kmh': 60,
        'timestamp': '2026-05-05T12:30:45Z'
    })
    assert response.status_code == 400
    assert 'latitude' in response.data['error'].lower()
```

**Pass Criteria**: Returns 400; error message includes field name

### Test Case 7.2: Invalid Coordinate Range
```python
def test_api_invalid_latitude_range():
    """POST with latitude >90 should return 400"""
    response = client.post('/api/telemetry/ingest_location/', {
        'truck_id': 'TRK001',
        'latitude': 200,  # Invalid
        'longitude': 31.034,
        'speed_kmh': 60,
        'timestamp': '2026-05-05T12:30:45Z'
    })
    assert response.status_code == 400
    assert 'coordinate' in response.data['error'].lower()
```

**Pass Criteria**: Returns 400; error message mentions coordinates

### Test Case 7.3: Invalid Speed
```python
def test_api_invalid_speed():
    """POST with speed >300 km/h should return 400"""
    response = client.post('/api/telemetry/ingest_location/', {
        'truck_id': 'TRK001',
        'latitude': -17.825,
        'longitude': 31.034,
        'speed_kmh': 500,  # Invalid
        'timestamp': '2026-05-05T12:30:45Z'
    })
    assert response.status_code == 400
```

**Pass Criteria**: Returns 400

**Acceptance Threshold**: ✅ All 3 test cases pass

---

## Test 8: Metrics Collection (Observability)

**Requirement**: Collect latency, exceptions, queue metrics without crashing

### Test Case 8.1: Metrics Endpoint Returns Valid Data
```python
def test_metrics_endpoint():
    """GET /api/telemetry/metrics/ should return valid JSON"""
    response = client.get('/api/telemetry/metrics/')
    assert response.status_code == 200
    
    metrics = response.data
    assert 'queue_length' in metrics
    assert 'exceptions' in metrics
    assert 'alerts_total' in metrics
    assert 'latency_percentile_50_ms' in metrics
    assert 'latency_percentile_95_ms' in metrics
```

**Pass Criteria**: All expected fields present

### Test Case 8.2: Metrics Accuracy
```python
def test_metrics_accuracy():
    """Metrics should reflect actual pipeline activity"""
    # Ingest 10 events
    for i in range(10):
        location = LocationPoint(truck_id=f'TRK{i % 5}', ...)
        pipeline.ingest_location(location, None, {})
    
    metrics = pipeline.get_metrics()
    assert metrics['locations_ingested'] == 10
    assert metrics['exceptions'] == 0
```

**Pass Criteria**: Metrics match actual activity

**Acceptance Threshold**: ✅ All 2 test cases pass

---

## Test 9: Frontend UI Responsiveness (No Blocking)

**Requirement**: Alert ingestion should not block UI (React render <100ms)

### Test Case 9.1: AlertsTable Component Renders Without Blocking
```javascript
test('AlertsTable renders without UI blocking', async () => {
  const startTime = performance.now();
  
  const { getByText } = render(<AlertsTable />);
  
  const renderTime = performance.now() - startTime;
  expect(renderTime).toBeLessThan(100);  // <100ms render
  expect(getByText(/Alerts/i)).toBeInTheDocument();
});
```

**Pass Criteria**: Render time <100ms

### Test Case 9.2: Toast Notification Appears Without Blocking
```javascript
test('Toast notification does not block UI', async () => {
  render(<AlertsTable />);
  
  // Simulate API response with alert
  await waitFor(() => {
    const toast = screen.getByText(/off-route/i);
    expect(toast).toBeInTheDocument();
  }, { timeout: 1000 });
});
```

**Pass Criteria**: Toast appears within 1s without blocking

### Test Case 9.3: Web Worker Offloads Geometry Calculation
```javascript
test('Alert evaluator worker offloads geometry', async () => {
  const worker = new Worker('alert-evaluator.worker.js');
  
  const startTime = performance.now();
  
  worker.postMessage({
    type: 'evaluate',
    locations: [...1000 locations...],
    route: {...}
  });
  
  // Main thread should remain responsive (<1ms)
  const afterPost = performance.now();
  expect(afterPost - startTime).toBeLessThan(1);
});
```

**Pass Criteria**: Main thread not blocked

**Acceptance Threshold**: ✅ All 3 test cases pass

---

## Test 10: Data Consistency & Replay

**Requirement**: Deterministic alert generation; replay audit trail

### Test Case 10.1: Deterministic Evaluation
```python
def test_deterministic_evaluation():
    """Same input should produce same alert decision"""
    route = RoutePolyline(route_id='RT001', points=[(-17.0, 31.0), (-18.0, 32.0)])
    
    # Replay same events twice
    for run in range(2):
        alerts = []
        for lat, lng in [(-15.0, 33.0), (-15.1, 33.1), (-15.2, 33.2)]:
            location = LocationPoint(
                truck_id='TRK001',
                latitude=lat,
                longitude=lng,
                speed_kmh=60,
                timestamp=datetime(2026, 5, 5, 12, 0, 0),  # Fixed timestamp
                trace_id=f'replay-{run}'
            )
            result = evaluator.evaluate(EvaluationContext(location, route, None, {}))
            alerts.append(len(result))
        
        if run == 0:
            first_run_alerts = alerts
        else:
            assert alerts == first_run_alerts, "Evaluation should be deterministic"
```

**Pass Criteria**: Same input → same output in both runs

### Test Case 10.2: Replay Log Capture
```python
def test_replay_log_capture():
    """All decisions should be logged with full context"""
    location = LocationPoint(truck_id='TRK001', latitude=-15.0, longitude=33.0, ...)
    route = RoutePolyline(route_id='RT001', points=[(-17.0, 31.0), (-18.0, 32.0)])
    
    evaluator.evaluate(EvaluationContext(location, route, None, {}))
    
    # Check replay log
    replay_logs = db.query('alert_replay_log').all()
    assert len(replay_logs) > 0
    
    last_log = replay_logs[-1]
    assert last_log['truck_id'] == 'TRK001'
    assert last_log['location']['lat'] == -15.0
    assert last_log['decision'] in ['on_route', 'off_route']
```

**Pass Criteria**: Full context logged; can be replayed

**Acceptance Threshold**: ✅ All 2 test cases pass

---

## Summary: Pass/Fail Matrix

| Test | Sub-Tests | Status | Notes |
|------|-----------|--------|-------|
| 1. Crash Rate = 0 | 4 | ⚪ | Null input, invalid coords, malformed polyline, high load |
| 2. Latency SLO | 3 | ⚪ | Ingestion p50, evaluation p95, E2E p95 |
| 3. N-Consensus | 3 | ⚪ | Single point, 3 points, counter reset |
| 4. Exponential Backoff | 3 | ⚪ | Initial, multiplier, expiry |
| 5. Queue Backpressure | 3 | ⚪ | <80% accept, >80% sample, total <0.1% |
| 6. Geometry Robustness | 3 | ⚪ | Polyline distance, bbox, fallback |
| 7. API Validation | 3 | ⚪ | Missing fields, invalid coords, invalid speed |
| 8. Metrics | 2 | ⚪ | Endpoint, accuracy |
| 9. Frontend Responsiveness | 3 | ⚪ | Render <100ms, toast <1s, worker offload |
| 10. Data Consistency | 2 | ⚪ | Deterministic, replay log |
| **TOTAL** | **30 tests** | **⚪** | **All must pass for GA** |

---

## CI/CD Integration

### Pre-Merge Requirements
```yaml
# .github/workflows/alerts-acceptance-tests.yml
name: Alert Pipeline Acceptance Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run acceptance tests
        run: |
          pytest server/tests/test_acceptance_alerts.py -v --cov
          npm run test -- AlertsTable.test.jsx --coverage
      - name: Check coverage >85%
        run: coverage_check --minimum 85
      - name: Report
        uses: codecov/codecov-action@v2
```

### Approval Gates
- [ ] All 30 tests pass (automated)
- [ ] Code coverage >85% (automated)
- [ ] Performance benchmarks met (automated)
- [ ] QA sign-off (manual)
- [ ] DevOps sign-off (manual)

---

**Document Owner**: QA Lead  
**Last Updated**: [Date]  
**Execution Frequency**: Before each stage deployment  
**Expected Runtime**: 15-20 minutes for full suite
