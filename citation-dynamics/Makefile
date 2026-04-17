# citation-dynamics pipeline Makefile
#
# Usage (from citation-networks/ root):
#   make -f citation-dynamics/Makefile all          # full pipeline
#   make -f citation-dynamics/Makefile nst          # NST only (needs hdf5 + leiden)
#   make -f citation-dynamics/Makefile help
#
# Or from citation-dynamics/ directly:
#   make all
#   make nst
#
# Set APS_METADATA_DIR to the directory containing aps-dataset-metadata-2022/ JSON files.

MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PYTHON     = $(MAKEFILE_DIR)../.venv/bin/python
SRC        = $(MAKEFILE_DIR)src
DATA_EXP   = $(MAKEFILE_DIR)data/exported
DATA_SYN   = $(MAKEFILE_DIR)data/synthesis
DATA_ANA   = $(MAKEFILE_DIR)data/analysis
DATA_FIG   = $(MAKEFILE_DIR)data/figures
DATA_PROC  = $(MAKEFILE_DIR)data/processed

# Output files (used as make targets)
HDF5       = $(DATA_EXP)/aps-2022-citation-graph.h5
LEIDEN     = $(DATA_EXP)/aps-2022-leiden-1p00.npz
ZEITGEIST  = $(DATA_ANA)/zeitgeist_community_fits.csv
FIGURES    = $(DATA_FIG)/fig1_indegree_ccdf.pdf
SUBGRAPH   = $(DATA_SYN)/k17-rgc-subgraph.npz

.PHONY: all hdf5 leiden zeitgeist figures subgraph clean help

help:
	@echo "Targets:"
	@echo "  all       — full §§1–4 pipeline (hdf5 → leiden → zeitgeist → figures)"
	@echo "  hdf5      — Phase 1: build HDF5 citation graph from CSV + JSON"
	@echo "  leiden    — Phase 2: full-corpus Leiden clustering"
	@echo "  zeitgeist — Phase 2b: per-community power-law fitting"
	@echo "  figures   — Generate all §§1–4 paper figures"
	@echo "  subgraph  — Phase 5 (on hold): Q-SYNTH 1-hop subgraph around K17-RGC gold DOIs"
	@echo "  clean     — remove generated data/exported/, data/analysis/, data/figures/ outputs"

all: zeitgeist figures

# --- Phase 1 -----------------------------------------------------------------
hdf5: $(HDF5)

$(HDF5): $(SRC)/phase1_build_graph.py \
         $(DATA_PROC)/aps-dataset-citations-2022.csv
	$(PYTHON) $(SRC)/phase1_build_graph.py
	@echo "[Phase 1] HDF5 written: $@"

# --- Phase 2 -----------------------------------------------------------------
leiden: $(LEIDEN)

$(LEIDEN): $(SRC)/phase2_leiden_cluster.py $(HDF5)
	$(PYTHON) $(SRC)/phase2_leiden_cluster.py
	@echo "[Phase 2] Leiden written: $@"

# --- Phase 5 -----------------------------------------------------------------
subgraph: $(SUBGRAPH)

$(SUBGRAPH): $(SRC)/phase5_synthesis_subgraph.py $(HDF5) \
             $(DATA_SYN)/k17-rgc-gold-dois.txt
	$(PYTHON) $(SRC)/phase5_synthesis_subgraph.py
	@echo "[Phase 5] Subgraph written: $@"

# --- Phase 2b ----------------------------------------------------------------
zeitgeist: $(ZEITGEIST)

$(ZEITGEIST): $(SRC)/phase2b_zeitgeist_fit.py $(HDF5) $(LEIDEN)
	$(PYTHON) $(SRC)/phase2b_zeitgeist_fit.py --ks_boots 500
	@echo "[Phase 2b] Zeitgeist fits written: $@"

# --- Figures -----------------------------------------------------------------
figures: $(FIGURES)

$(FIGURES): $(SRC)/generate_figures.py $(HDF5) $(LEIDEN) $(ZEITGEIST)
	$(PYTHON) $(SRC)/generate_figures.py --out $(DATA_FIG)
	@echo "[Figures] All §§1–4 figures written: $(DATA_FIG)/"

# --- Phase 5 (on hold) -------------------------------------------------------
subgraph: $(SUBGRAPH)

$(SUBGRAPH): $(SRC)/phase5_synthesis_subgraph.py $(HDF5) \
             $(DATA_SYN)/k17-rgc-gold-dois.txt
	$(PYTHON) $(SRC)/phase5_synthesis_subgraph.py
	@echo "[Phase 5] Subgraph written: $@"

# --- Housekeeping ------------------------------------------------------------
clean:
	@echo "Removing generated outputs..."
	rm -f $(DATA_EXP)/aps-2022-citation-graph.h5
	rm -f $(DATA_EXP)/aps-2022-leiden-*.npz
	rm -f $(DATA_ANA)/zeitgeist_community_fits.csv
	rm -f $(DATA_ANA)/zeitgeist_summary.txt
	rm -f $(DATA_ANA)/zeitgeist_gamma_dist.npy
	rm -f $(DATA_ANA)/global_fit.txt
	rm -rf $(DATA_FIG)
	rm -f $(DATA_SYN)/k17-rgc-subgraph.npz $(DATA_SYN)/k17-rgc-subgraph-dois.txt
	rm -f $(DATA_SYN)/k17-rgc-subgraph-leiden-*.npz
