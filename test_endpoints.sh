#!/bin/bash
# Test mission endpoints on Render

echo "Testing mission endpoints..."
sleep 45

echo -e "\n✅ Testing available-missions endpoint..."
curl -s https://pulsetrack-back.onrender.com/api/v1/mobile/driver/test/available-missions/ | jq . 2>/dev/null || echo "Connection issue"

echo -e "\n✅ Testing start-tracking endpoint..."
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"driver_id":"test","mission_id":"00000000-0000-0000-0000-000000000001"}' \
  https://pulsetrack-back.onrender.com/api/v1/mobile/mission/start-tracking/ | jq . 2>/dev/null || echo "Connection issue"
