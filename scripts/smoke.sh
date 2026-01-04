#!/usr/bin/env bash
set -euo pipefail

BASE="http://localhost:5001"

echo "== health =="
curl -s "$BASE/api/health" | python -m json.tool >/dev/null
echo "OK"

echo "== cities =="
curl -s "$BASE/api/cities" | python -m json.tool >/dev/null
echo "OK"

echo "== plan (smart_open) =="
curl -s -X POST "$BASE/api/plan" \
  -H "Content-Type: application/json" \
  -d '{"mode":"smart_open","start_city":"Milano","start_date":"2026-01-03","duration":3,"interests":["arte","storia"],"budget":200}' \
| python -m json.tool >/dev/null
echo "OK"
