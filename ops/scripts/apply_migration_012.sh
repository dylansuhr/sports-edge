#!/bin/bash
# Apply migration 0012: API usage tracking
# Run this script to add the api_usage_log table to your database

set -e  # Exit on error

echo "Applying migration 0012: API usage tracking..."
echo "This will create:"
echo "  - api_usage_log table"
echo "  - api_usage_monthly view"
echo "  - api_usage_current_month view"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    echo "Set it in your .env file or export it:"
    echo "  export DATABASE_URL='your_database_url_here'"
    exit 1
fi

# Apply migration
psql "$DATABASE_URL" -f infra/migrations/0012_add_api_usage_tracking.sql

echo ""
echo "✅ Migration applied successfully!"
echo ""
echo "You can now query API usage:"
echo "  psql \"\$DATABASE_URL\" -c 'SELECT * FROM api_usage_current_month'"
