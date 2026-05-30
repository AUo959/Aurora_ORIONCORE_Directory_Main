# Warrant Lens — module-local Makefile.
# Aurora's root Makefile is left untouched on purpose; wire targets there later.

.DEFAULT_GOAL := help

# Use Aurora's preferred python invocation by default; override at the CLI.
PY        ?= python3
PIP       ?= $(PY) -m pip
PYTEST    ?= $(PY) -m pytest
BASETEMP  ?= /tmp/wl_pytest
TRACE_DIR ?= /tmp/wl_traces

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / { printf "  %-18s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install warrant-lens in editable mode with dev extras
	$(PIP) install -e ".[dev]" --break-system-packages

install-anthropic: ## Install with the anthropic extra for production client
	$(PIP) install -e ".[dev,anthropic]" --break-system-packages

test: ## Run the full pytest suite
	$(PYTEST) --basetemp=$(BASETEMP) -p no:cacheprovider

test-quick: ## Run tests quietly
	$(PYTEST) --basetemp=$(BASETEMP) -p no:cacheprovider -q

test-tier1: ## Run only the two principle-protecting tests (T-CLIMATE, T-DELIVERY)
	$(PYTEST) --basetemp=$(BASETEMP) -p no:cacheprovider -m tier1 -v

smoke: ## Run the CLI on the example file using the HeuristicClient
	mkdir -p $(TRACE_DIR)
	$(PY) -m warrant_lens analyze examples/sample.txt \
		--trace-dir $(TRACE_DIR) --topic smoke

html-demo: ## Run the CLI and also emit the HTML viewer
	mkdir -p $(TRACE_DIR)
	$(PY) -m warrant_lens analyze examples/sample.txt \
		--trace-dir $(TRACE_DIR) --topic smoke \
		--html $(TRACE_DIR)/smoke.html
	@echo "HTML viewer: $(TRACE_DIR)/smoke.html"

calibrate-demo: ## Generate a trace, then label it from a sample CSV
	mkdir -p $(TRACE_DIR)
	$(PY) -m warrant_lens analyze examples/sample.txt \
		--trace-dir $(TRACE_DIR) --topic smoke >/dev/null
	@echo "claim_id,worth_attention,notes"           >  $(TRACE_DIR)/labels.csv
	@echo "c_00073_00109,yes,real evidentiary gap"   >> $(TRACE_DIR)/labels.csv
	$(PY) -m warrant_lens calibrate \
		$(TRACE_DIR)/WARRANTLENS__TRACE__smoke__v1.0__*.jsonl \
		--labels $(TRACE_DIR)/labels.csv \
		--out-dir $(TRACE_DIR)

clean: ## Remove caches and local build artefacts
	rm -rf .pytest_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

.PHONY: help install install-anthropic test test-quick test-tier1 smoke html-demo calibrate-demo clean
