# dengue-allocator -- everything reproducible from make. No manual steps.
#
# Prefers `uv` when available and falls back to venv + pip, so the same targets
# work on a machine without uv installed.

SHELL := /bin/sh

VENV        := .venv
UV          := $(shell command -v uv 2>/dev/null)

ifeq ($(OS),Windows_NT)
  BIN       := $(VENV)/Scripts
  PY        := $(BIN)/python.exe
else
  BIN       := $(VENV)/bin
  PY        := $(BIN)/python
endif

PYTEST      := $(PY) -m pytest
RUFF        := $(PY) -m ruff
STREAMLIT   := $(PY) -m streamlit

# Synthetic panel size for the offline acceptance run (~10 years).
N_WEEKS        ?= 520
STRIDE         ?= 4
# The pipeline refits SEI-SIR per district, so it uses a shorter window.
PIPELINE_WEEKS ?= 320

.DEFAULT_GOAL := help
.PHONY: help setup setup-full data panel panel-synthetic baseline baseline-real \
        pipeline pipeline-real all tune test test-all lint format app clean clean-data check

help:  ## Show this help
	@echo "dengue-allocator targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# --------------------------------------------------------------------------
# Environment
# --------------------------------------------------------------------------

setup:  ## Create the venv and install pinned dependencies
ifeq ($(UV),)
	@echo ">> uv not found; using python -m venv + pip"
	python -m venv $(VENV) || py -3 -m venv $(VENV)
	$(PY) -m pip install --upgrade pip setuptools wheel
	$(PY) -m pip install -e ".[dev]"
else
	@echo ">> using uv"
	$(UV) venv $(VENV)
	$(UV) pip install --python $(PY) -e ".[dev]"
endif
	@echo ">> setup complete"

setup-full: setup  ## Also install the optional geo + polars extras
	$(PY) -m pip install -e ".[dev,geo,fast]"

# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------

data:  ## Run every ingest step (requires network)
	@echo ">> colmozzie (CRAN, CC0)"
	-$(PY) -m dengue.ingest.colmozzie
	@echo ">> open-meteo archive (CC-BY-4.0)"
	-$(PY) -m dengue.ingest.openmeteo
	@echo ">> reliefweb (API v2; needs a pre-approved appname)"
	-$(PY) -m dengue.ingest.reliefweb
	@echo ">> WER pdf parser (library; supply PDFs explicitly)"
	-$(PY) -m dengue.ingest.wer_pdf
	@echo ">>> district boundaries (OCHA/HDX, CC-BY-IGO)"
	-$(PY) -m dengue.ingest.boundaries
	@echo ">>> health facilities (OpenStreetMap ODbL + World Bank CC-BY)"
	-$(PY) -m dengue.ingest.health_facilities
	@echo ">> ingest finished (individual sources may have been skipped; see the log)"

panel:  ## Build data/processed/panel.parquet from the ingested sources
	$(PY) -m dengue.features.build_panel --features

panel-synthetic:  ## Build a synthetic panel (fully offline)
	$(PY) -m dengue.features.build_panel --synthetic --features

# --------------------------------------------------------------------------
# Modelling
# --------------------------------------------------------------------------

baseline:  ## Train all Stage 1 baselines and print the comparison table
	$(PY) -m dengue.eval.backtest --synthetic --n-weeks $(N_WEEKS) --stride $(STRIDE)

baseline-real:  ## Same, but against data/processed/panel.parquet
	$(PY) -m dengue.eval.backtest --stride $(STRIDE)

pipeline:  ## Run all 3 stages and write every dashboard artifact (offline)
	$(PY) -m dengue.pipeline --synthetic --n-weeks $(PIPELINE_WEEKS)

pipeline-real:  ## Same, but against data/processed/panel.parquet
	$(PY) -m dengue.pipeline

history:  ## Build the app's predicted-vs-actual historical view (offline)
	$(PY) -m dengue.eval.history --synthetic

history-real:  ## Same, but against data/processed/panel.parquet
	$(PY) -m dengue.eval.history

alerts:  ## Send this week's due email alerts (needs Supabase + Resend secrets)
	$(PY) -m dengue.platform.alerts

all: baseline pipeline history  ## Backtest + full pipeline, everything the app needs

tune:  ## GA hyperparameter + ensemble-weight search, offline (~30 min)
	$(PY) -m dengue.tuning.runner --synthetic --n-weeks $(N_WEEKS)

# --------------------------------------------------------------------------
# Quality
# --------------------------------------------------------------------------

test:  ## Run the test suite (no network, no slow GA end-to-end test)
	$(PYTEST) -m "not network and not slow"

test-all:  ## Run every test, including network-dependent ones
	$(PYTEST)

lint:  ## Lint with ruff
	$(RUFF) check src tests app
	$(RUFF) format --check src tests app

format:  ## Auto-fix lint issues and format
	$(RUFF) check --fix src tests app
	$(RUFF) format src tests app

check: lint test  ## Lint and test

# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------

app:  ## Launch the Streamlit dashboard (reads cached artifacts only)
	$(STREAMLIT) run app/streamlit_app.py

# --------------------------------------------------------------------------
# Housekeeping
# --------------------------------------------------------------------------

clean:  ## Remove caches and build artefacts
	-rm -rf .pytest_cache .ruff_cache .coverage htmlcov build dist *.egg-info
	-find . -type d -name __pycache__ -prune -exec rm -rf {} +

clean-data:  ## Delete downloaded/derived data (keeps .gitkeep)
	-find data -type f ! -name '.gitkeep' -delete
	-find artifacts -type f ! -name '.gitkeep' -delete
