#!/bin/bash
# Apply migration 0017: Fix api_usage_current_month view
# Re-creates the view so monitoring always shows the lowest remaining credits

set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL is not set. Export it or add to .env"
  exit 1
fi

echo "Applying migration 0017 (api_usage_current_month fix)..."
psql "$DATABASE_URL" -f infra/migrations/0017_fix_api_usage_current_month.sql

echo "✅ Migration 0017 applied successfully."
