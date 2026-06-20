.PHONY: help setup test verify scan sync-audit sync-audit-all gh-auth-check pr-packet lint health devkit-check devkit-report devkit-install-plan skills-check skills-install session-claims session-claim-check cloudbank-broker cloudbank-broker-check recovery-index recovery-report recommendations recommendations-report mission-control mission-control-report confidence-audit confidence-audit-report integration-gate l2-scenario-uptake clean

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

devkit-check: ## Audit the local Aurora developer toolkit surface
	$(PYTHON) tools/aurora_devkit.py

devkit-report: ## Persist the local Aurora developer toolkit report
	$(PYTHON) tools/aurora_devkit.py --persist-report

devkit-install-plan: ## Show the approval-gated Aurora developer toolkit install plan
	$(PYTHON) tools/aurora_devkit.py --install-plan --persist-install-plan

skills-check: ## Dry-run: show what skills/ changes would be pushed to ~/.codex/skills/
	$(PYTHON) tools/sync_skills.py

skills-install: ## Push all project-owned skills from skills/ → ~/.codex/skills/
	$(PYTHON) tools/sync_skills.py --apply

session-claims: ## List local Codex/Claude Code session claims
	$(PYTHON) tools/session_claim.py list

session-claim-check: ## Check for root-wide overlapping active session claims
	$(PYTHON) tools/session_claim.py check --repo root --paths .

cloudbank-broker: ## Show CloudBank issue broker status
	$(PYTHON) tools/cloudbank_issue_broker.py status

cloudbank-broker-check: ## Check CloudBank issue broker with ISSUE=<number> PATHS="path ..."
	$(PYTHON) tools/cloudbank_issue_broker.py check --issue $(ISSUE) --paths $(PATHS)

recovery-index: ## Build the read-only recovery index summary
	$(PYTHON) tools/workspace_recovery_index.py --summary

recovery-report: ## Persist the read-only recovery index report
	$(PYTHON) tools/workspace_recovery_index.py --persist-report

recommendations: ## Build the advisory Aurora root recommendation summary
	$(PYTHON) tools/aurora_recommendation_engine.py --summary

recommendations-report: ## Persist the advisory Aurora root recommendation report
	$(PYTHON) tools/aurora_recommendation_engine.py --persist-report

mission-control: ## Build the read-only Aurora Mission Control summary
	$(PYTHON) tools/aurora_mission_control.py --summary

mission-control-report: ## Persist the read-only Aurora Mission Control report
	$(PYTHON) tools/aurora_mission_control.py --persist-report

confidence-audit: ## Run the bootstrap confidence audit example summary
	$(PYTHON) tools/aurora_confidence_audit.py score \
		--claim-type analysis \
		--text "Confidence audit tooling is available in the root control plane." \
		--evidence-level verified_artifact \
		--authority-ref docs/AURORA_CONFIDENCE_AUDIT_WORKFLOW_v1.md \
		--evidence-ref tools/aurora_confidence_audit.py \
		--summary

confidence-audit-report: ## Persist the bootstrap confidence audit example report
	$(PYTHON) tools/aurora_confidence_audit.py score \
		--claim-type analysis \
		--text "Confidence audit tooling is available in the root control plane." \
		--evidence-level verified_artifact \
		--authority-ref docs/AURORA_CONFIDENCE_AUDIT_WORKFLOW_v1.md \
		--evidence-ref tools/aurora_confidence_audit.py \
		--persist-report \
		--summary

integration-gate: ## Run the root command/agent/provenance integration gate
	$(PYTHON) tools/aurora_integration_gate.py --summary

l2-scenario-uptake: ## Validate L2 scenario seed uptake packets and emergence guardrails
	$(PYTHON) tools/l2_scenario_seed_uptake.py --summary

# ── Git / Sync ───────────────────────────────────────────────────────────

sync-audit: ## Run sync audit for root repo
	$(PYTHON) skills/gitwiz-github-manager/scripts/gitwiz_sync_audit.py --repo root --check-gh-auth

sync-audit-all: ## Run sync audit for all registered repos
	$(PYTHON) skills/gitwiz-github-manager/scripts/gitwiz_sync_audit.py --repo all \
		--canonical-root "$(shell pwd)" \
		--check-gh-auth

gh-auth-check: ## Probe GitHub CLI auth in the current execution context
	$(PYTHON) skills/gitwiz-github-manager/scripts/gitwiz_gh_auth_probe.py --repo AUo959/aurora-cloudbank-symbolic

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
