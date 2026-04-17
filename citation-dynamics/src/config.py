"""config.py — Path constants for the citation-dynamics pipeline.

All paths are relative to this file so the module works regardless of
the working directory the caller was launched from.

Usage (from any script in src/):
    from config import APS_H5, APS_LEIDEN, DATA_ANALYSIS
"""

import os
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()  # citation-dynamics/

# Data directories
DATA_PROCESSED = ROOT / "data" / "processed"   # canonical MAT / CSV inputs
DATA_SAMPLE    = ROOT / "data" / "sample"       # small test datasets
DATA_EXPORTED  = ROOT / "data" / "exported"     # HDF5, NPZ outputs from pipeline
DATA_SYNTHESIS = ROOT / "data" / "synthesis"    # Q-SYNTH subgraph + gold DOIs
DATA_ANALYSIS  = ROOT / "data" / "analysis"     # per-community stats, fit results
DATA_FIGURES   = ROOT / "data" / "figures"      # generated figures (PDF + PNG)

# APS metadata lives outside the repo; configure via env var
APS_METADATA_DIR: Path | None = (
    Path(os.environ["APS_METADATA_DIR"]) if "APS_METADATA_DIR" in os.environ else None
)

# Key data files
APS_H5       = DATA_EXPORTED  / "aps-2022-citation-graph.h5"
APS_LEIDEN   = DATA_EXPORTED  / "aps-2022-leiden-1p00.npz"
APS_FITS     = DATA_ANALYSIS  / "zeitgeist_community_fits.csv"
APS_LABELS   = DATA_ANALYSIS  / "community_labels.csv"
APS_GOLD     = DATA_SYNTHESIS / "k17-rgc-gold-dois.txt"
APS_SUBGRAPH = DATA_SYNTHESIS / "k17-rgc-subgraph.npz"


def check_paths() -> None:
    """Print existence status of all expected data files."""
    dirs  = [DATA_PROCESSED, DATA_SAMPLE, DATA_EXPORTED, DATA_SYNTHESIS,
              DATA_ANALYSIS, DATA_FIGURES]
    files = [APS_H5, APS_LEIDEN, APS_FITS, APS_LABELS, APS_GOLD, APS_SUBGRAPH]
    for p in dirs:
        print(f"  [{'OK' if p.exists() else 'MISSING'}] {p}")
    for p in files:
        print(f"  [{'OK' if p.exists() else 'MISSING'}] {p}")
    if APS_METADATA_DIR is None:
        print("  [WARN] APS_METADATA_DIR not set (needed only for phase1_build_graph.py)")
    else:
        tag = "OK" if APS_METADATA_DIR.exists() else "MISSING"
        print(f"  [{tag}] APS_METADATA_DIR={APS_METADATA_DIR}")


if __name__ == "__main__":
    print(f"citation-dynamics root: {ROOT}")
    check_paths()
