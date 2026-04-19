.PHONY: help setup test verify scan sync-audit pr-packet lint health clean

PYTHON ?= python3
PYTEST ?= pytest

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Setup ────────────────────────────────────────────────────────────────

setup: ## Install Python deps and configure git hooks
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install pytest pyyaml jsonschema
	git config core.hooksPath .githooks
	@echo "\n✓ Setup complete. Git hooks active."

# ── Testing ──────────────────────────────────────────────────────────────

test: ## Run the full test suite
	$(PYTEST) tests/ -v --tb=short

test-quick: ## Run tests without verbose output
	$(PYTEST) tests/ -q

# ── Workspace Operations ─────────────────────────────────────────────────

verify: ## Run workspace verification (side-effect-free)
	$(PYTHON) tools/workspace_verify.py

scan: ## Discover and inventory workspace state
	$(PYTHON) tools/workspace_scan.py

health: ## Run full health check (tests + verify + lint + sync audit)
	@echo "══════════════════════════════════════════"
	@echo "  Aurora Workspace Health Check"
	@echo "══════════════════════════════════════════"
	@echo "\n── Tests ──"
	@$(PYTEST) tests/ -q || true
	@echo "\n── Workspace Verification ──"
	@$(PYTHON) tools/workspace_verify.py || true
	@echo "\n── YAML/JSON Lint ──"
	@$(MAKE) -s lint || true
	@echo "\n── Sync Audit (root) ──"
	@$(PYTHON) skills/gitwiz-github-manager/scripts/gitwiz_sync_audit.py --repo root || true
	@echo "\n══════════════════════════════════════════"
	@echo "  Health check complete."
	@echo "══════════════════════════════════════════"

# ── Git / Sync ───────────────────────────────────────────────────────────

sync-audit: ## Run sync audit for root repo
	$(PYTHON) skills/gitwiz-github-manager/scripts/gitwiz_sync_audit.py --repo root

sync-audit-all: ## Run sync audit for all registered repos
	$(PYTHON) skills/gitwiz-github-manager/scripts/gitwiz_sync_audit.py --repo all \
		--canonical-root "$(shell pwd)"

pr-packet: ## Draft a PR packet for root repo
	$(PYTHON) skills/gitwiz-github-manager/scripts/gitwiz_pr_packet.py \
		--repo-name root --base origin/main

# ── Lint ─────────────────────────────────────────────────────────────────

lint: ## Validate YAML and JSON catalog files
	$(PYTHON) tools/workspace_health_check.py --lint-only

# ── GUMAS Simulation ────────────────────────────────────────────────────

gumas-validate: ## Run GUMAS v3.0 validation suite
	$(PYTHON) GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19/validate_v3.py

gumas-api: ## Start GUMAS simulation API server (port 8000)
	$(PYTHON) tools/gumas_api.py --host 0.0.0.0 --port 8000

# ── Cleanup ──────────────────────────────────────────────────────────────

clean: ## Remove Python caches and temp files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned."
