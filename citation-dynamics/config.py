"""config.py — Path constants for the citation-dynamics Python pipeline.

All paths are relative to this file so the module works regardless of
the working directory the caller was launched from.

Usage:
    from config import DATA_EXPORTED, DATA_SYNTHESIS
"""

import os
from pathlib import Path

# Root of citation-dynamics/ (the directory this file lives in)
ROOT = Path(__file__).parent.resolve()

# Data directories
DATA_PROCESSED  = ROOT / "data" / "processed"   # canonical MAT / CSV inputs
DATA_SAMPLE     = ROOT / "data" / "sample"       # small test datasets
DATA_EXPORTED   = ROOT / "data" / "exported"     # HDF5, NPZ, PT outputs from pipeline
DATA_SYNTHESIS  = ROOT / "data" / "synthesis"    # Q-SYNTH subgraph + gold DOIs

# APS metadata lives outside the repo; configure via env var
APS_METADATA_DIR: Path | None = (
    Path(os.environ["APS_METADATA_DIR"]) if "APS_METADATA_DIR" in os.environ else None
)

# Key data files
APS_H5      = DATA_EXPORTED / "aps-2022-citation-graph.h5"
APS_LEIDEN  = DATA_EXPORTED / "aps-2022-leiden-1p00.npz"
APS_GOLD    = DATA_SYNTHESIS / "k17-rgc-gold-dois.txt"
APS_SUBGRAPH = DATA_SYNTHESIS / "k17-rgc-subgraph.npz"


def check_paths() -> None:
    """Print existence status of all expected data files."""
    dirs = [DATA_PROCESSED, DATA_SAMPLE, DATA_EXPORTED, DATA_SYNTHESIS]
    files = [APS_H5, APS_LEIDEN, APS_GOLD, APS_SUBGRAPH]
    for p in dirs:
        tag = "OK" if p.exists() else "MISSING"
        print(f"  [{tag}] {p}")
    for p in files:
        tag = "OK" if p.exists() else "MISSING"
        print(f"  [{tag}] {p}")
    if APS_METADATA_DIR is None:
        print("  [WARN] APS_METADATA_DIR not set (needed only for build_aps_hdf5.py)")
    else:
        tag = "OK" if APS_METADATA_DIR.exists() else "MISSING"
        print(f"  [{tag}] APS_METADATA_DIR={APS_METADATA_DIR}")


if __name__ == "__main__":
    print(f"citation-dynamics root: {ROOT}")
    check_paths()
