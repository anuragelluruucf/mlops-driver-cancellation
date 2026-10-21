#!/usr/bin/env bash
# Smoke test a running service: ./scripts/smoke.sh http://localhost:8080
set -euo pipefail
URL=${1:-http://localhost:8080}
ORDER='{"lifetime_order_count":40,"bike_issue_rate":0.6,"post_pickup_rate":0.8,"total_distance":9.5,"first_mile_distance":2.5,"last_mile_distance":7.0,"session_time":300,"hour":19,"time_to_accept":1.0,"time_to_pickup":10}'
curl -fsS "$URL/health"; echo
curl -fsS -X POST "$URL/predict" -H 'content-type: application/json' -d "$ORDER"; echo
curl -fsS -X POST "$URL/explain?top_k=3" -H 'content-type: application/json' -d "$ORDER"; echo
echo "smoke OK"
