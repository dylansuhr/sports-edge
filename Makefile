.PHONY: help verify install clean test etl signals settle dashboard migrate db-ping clv clv-report milestone-check

# Use python3 by default (macOS/Linux standard)
PYTHON := python3
PIP := pip3

help:
	@echo "Sports Edge - Available Commands"
	@echo "================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make verify     - Verify environment setup"
	@echo ""
	@echo "Database:"
	@echo "  make migrate    - Run database migrations"
	@echo "  make db-ping    - Test database connectivity"
	@echo ""
	@echo "Operations:"
	@echo "  make etl        - Run odds ETL (NFL only)"
	@echo "  make signals    - Generate betting signals (NFL only)"
	@echo "  make settle     - Settle bet results"
	@echo "  make clv        - Capture closing lines (run before games start)"
	@echo "  make clv-report - Generate CLV performance report"
	@echo "  make milestone-check - Check milestone readiness"
	@echo ""
	@echo "Development:"
	@echo "  make dashboard  - Start Next.js dashboard (dev mode)"
	@echo "  make test       - Run unit tests"
	@echo "  make clean      - Clean build artifacts"
	@echo ""

verify:
	@echo "🔍 Verifying environment setup..."
	@$(PYTHON) ops/scripts/verify_setup.py

migrate:
	@echo "🗄️  Running database migrations..."
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "❌ DATABASE_URL not set"; \
		echo "   Set it in .env or run: source .venv/bin/activate"; \
		exit 1; \
	fi
	@echo "Running 0001_init.sql..."
	@psql "$$DATABASE_URL" -f infra/migrations/0001_init.sql || (echo "❌ Migration 0001 failed" && exit 1)
	@echo "Running 0002_add_elo_tracking.sql..."
	@psql "$$DATABASE_URL" -f infra/migrations/0002_add_elo_tracking.sql || (echo "❌ Migration 0002 failed" && exit 1)
	@echo "Running 0003_add_elo_history.sql..."
	@psql "$$DATABASE_URL" -f infra/migrations/0003_add_elo_history.sql || (echo "❌ Migration 0003 failed" && exit 1)
	@echo "Running 0004_add_selection_to_odds.sql..."
	@psql "$$DATABASE_URL" -f infra/migrations/0004_add_selection_to_odds.sql || (echo "❌ Migration 0004 failed" && exit 1)
	@echo "Running 0005_add_raw_implied_prob.sql..."
	@psql "$$DATABASE_URL" -f infra/migrations/0005_add_raw_implied_prob.sql || (echo "❌ Migration 0005 failed" && exit 1)
	@echo "Running 0006_add_signal_clv_tracking.sql..."
	@psql "$$DATABASE_URL" -f infra/migrations/0006_add_signal_clv_tracking.sql || (echo "❌ Migration 0006 failed" && exit 1)
	@echo "Running 0013_add_milestones.sql..."
	@psql "$$DATABASE_URL" -f infra/migrations/0013_add_milestones.sql || (echo "❌ Migration 0013 failed" && exit 1)
	@echo "✅ All migrations successful"

db-ping:
	@$(PYTHON) ops/scripts/db_ping.py

install:
	@echo "📦 Installing Python dependencies..."
	@$(PYTHON) -m pip install --upgrade pip
	@$(PIP) install -r packages/models/requirements.txt
	@echo "✅ Python dependencies installed"
	@echo ""
	@echo "📦 Installing Node dependencies..."
	@cd apps/dashboard && npm install
	@echo "✅ Node dependencies installed"

etl:
	@echo "📊 Running odds ETL (NFL only - single-sport focus)..."
	@$(PYTHON) ops/scripts/odds_etl_v2.py --leagues nfl

signals:
	@echo "🎯 Generating signals (NFL only - single-sport focus)..."
	@$(PYTHON) ops/scripts/generate_signals_v2.py --leagues nfl

settle:
	@echo "💰 Settling bet results..."
	@$(PYTHON) ops/scripts/settle_results_v2.py --league nfl --days 1

clv:
	@echo "📈 Capturing closing lines for CLV tracking (NFL only)..."
	@$(PYTHON) ops/scripts/capture_closing_lines.py --leagues nfl --minutes-ahead 30

clv-report:
	@echo "📊 Generating CLV performance report..."
	@$(PYTHON) ops/scripts/clv_report.py

milestone-check:
	@echo "🎯 Checking milestone readiness..."
	@$(PYTHON) ops/scripts/check_milestone_readiness.py

dashboard:
	@echo "🚀 Starting dashboard..."
	@cd apps/dashboard && npm run dev

test:
	@echo "🧪 Running unit tests..."
	@$(PYTHON) -m pytest packages/shared/tests/test_odds_math.py -v

clean:
	@echo "🧹 Cleaning build artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@cd apps/dashboard && rm -rf .next out 2>/dev/null || true
	@echo "✅ Cleanup complete"
