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
DATA_PROC  = $(MAKEFILE_DIR)data/processed

# Output files (used as make targets)
HDF5       = $(DATA_EXP)/aps-2022-citation-graph.h5
LEIDEN     = $(DATA_EXP)/aps-2022-leiden-1p00.npz
SUBGRAPH   = $(DATA_SYN)/k17-rgc-subgraph.npz
NST_MODEL  = $(DATA_EXP)/aps-nst-model.pt
NST_EMB    = $(DATA_EXP)/aps-nst-embeddings.npy
ZEITGEIST  = $(DATA_ANA)/zeitgeist_community_fits.csv
TIMECURVES = $(DATA_ANA)/timecurves_nst_result.npz

.PHONY: all hdf5 leiden subgraph nst zeitgeist timecurves timecurves-proxy clean help

help:
	@echo "Targets:"
	@echo "  all             — full pipeline (hdf5 → leiden → zeitgeist → nst → timecurves)"
	@echo "  hdf5            — Phase 1: build HDF5 citation graph from CSV + JSON"
	@echo "  leiden          — Phase 2: full-corpus Leiden clustering"
	@echo "  zeitgeist       — Phase 2b: per-community power-law fitting"
	@echo "  subgraph        — Phase 5: Q-SYNTH 1-hop subgraph around K17-RGC gold DOIs"
	@echo "  nst             — Phase 3: train Neural Spacetime + export embeddings"
	@echo "  timecurves      — Phase 4: Time Curves on NST embeddings"
	@echo "  timecurves-proxy— Phase 4 (proxy): Time Curves on structural features (no NST)"
	@echo "  clean           — remove all generated data/exported/ and data/synthesis/ outputs"

all: timecurves

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

# --- Phase 3 -----------------------------------------------------------------
nst: $(NST_EMB)

$(NST_EMB): $(SRC)/phase3_nst_train.py $(SRC)/phase3_nst_adapter.py \
            $(HDF5) $(LEIDEN)
	$(PYTHON) $(SRC)/phase3_nst_train.py \
	    --num_epochs 500 --max_edges 500000 --display_epoch 50
	@echo "[Phase 3] NST embeddings written: $@"

# --- Phase 4 -----------------------------------------------------------------
timecurves: $(TIMECURVES)

$(TIMECURVES): $(SRC)/phase4_timecurves.py $(NST_EMB)
	$(PYTHON) $(SRC)/phase4_timecurves.py \
	    --embeddings $(NST_EMB) \
	    --meta $(DATA_EXP)/aps-nst-embeddings-meta.npz \
	    --out $(DATA_ANA)/
	@echo "[Phase 4] Time Curves written: $@"

timecurves-proxy:
	$(PYTHON) $(SRC)/phase4_timecurves.py --proxy \
	    --features $(DATA_EXP)/aps_nst_seed42_maxe500k_node_features.npy \
	    --meta $(DATA_EXP)/aps-nst-embeddings-meta.npz \
	    --out $(DATA_ANA)/
	@echo "[Phase 4 proxy] Time Curves (structural features) written."

# --- Housekeeping ------------------------------------------------------------
clean:
	@echo "Removing generated outputs..."
	rm -f $(DATA_EXP)/aps-2022-citation-graph.h5
	rm -f $(DATA_EXP)/aps-2022-leiden-*.npz
	rm -f $(DATA_EXP)/aps-nst-*.pt $(DATA_EXP)/aps-nst-*.npy $(DATA_EXP)/aps-nst-*.npz
	rm -f $(DATA_EXP)/aps_nst_*.pt $(DATA_EXP)/aps_nst_*.npy
	rm -f $(DATA_SYN)/k17-rgc-subgraph.npz $(DATA_SYN)/k17-rgc-subgraph-dois.txt
	rm -f $(DATA_SYN)/k17-rgc-subgraph-leiden-*.npz
