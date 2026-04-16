"""load_aps.py — Load APS citation graph from HDF5 into PyG Data.

Usage (round-trip test):
    python load_aps.py

Returns a PyG Data object with:
    data.edge_index : LongTensor[2, E]  — COO edge index
    data.num_nodes  : int               — N
    data.year       : FloatTensor[N]    — publication year per node
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import scipy.sparse as sp

# --- Optional PyG import (skip gracefully if not installed) ---
try:
    import torch
    from torch_geometric.data import Data as PyGData
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Default path relative to this file's location
_HERE = Path(__file__).parent
_DEFAULT_H5 = _HERE / "../../data/exported/aps-2022-citation-graph.h5"


def load_h5(h5_path: str | Path = _DEFAULT_H5) -> dict:
    """Load HDF5 export and return raw numpy arrays.

    Returns
    -------
    dict with keys:
        edge_row : int32 ndarray [E]
        edge_col : int32 ndarray [E]
        year     : float32 ndarray [N]
        n_nodes  : int
        n_edges  : int
    """
    h5_path = Path(h5_path)
    if not h5_path.exists():
        raise FileNotFoundError(
            f"HDF5 not found: {h5_path}\n"
            "Run src/export/export_for_python.m in MATLAB first."
        )

    with h5py.File(h5_path, "r") as f:
        edge_row = f["/edge_row"][:].squeeze()
        edge_col = f["/edge_col"][:].squeeze()
        year     = f["/year"][:].squeeze()
        n_nodes  = int(f.attrs.get("n_nodes", len(year)))
        n_edges  = int(f.attrs.get("n_edges", len(edge_row)))

    return dict(
        edge_row=edge_row,
        edge_col=edge_col,
        year=year,
        n_nodes=n_nodes,
        n_edges=n_edges,
    )


def to_scipy_sparse(raw: dict) -> sp.csr_matrix:
    """Reconstruct scipy sparse matrix from raw HDF5 arrays."""
    n = raw["n_nodes"]
    data = np.ones(raw["n_edges"], dtype=np.float32)
    return sp.csr_matrix(
        (data, (raw["edge_row"], raw["edge_col"])),
        shape=(n, n),
    )


def to_pyg(raw: dict) -> "PyGData":
    """Build a PyG Data object from raw HDF5 arrays.

    Requires torch and torch_geometric.
    """
    if not HAS_TORCH:
        raise ImportError(
            "torch and torch_geometric are required for to_pyg().\n"
            "Install: pip install torch torch_geometric"
        )
    edge_index = torch.tensor(
        np.stack([raw["edge_row"], raw["edge_col"]], axis=0).astype(np.int64),
        dtype=torch.long,
    )
    year = torch.tensor(raw["year"], dtype=torch.float32)
    return PyGData(
        edge_index=edge_index,
        year=year,
        num_nodes=raw["n_nodes"],
    )


def round_trip_test(h5_path: str | Path = _DEFAULT_H5) -> None:
    """Load graph and print summary — use as a sanity check."""
    print(f"Loading: {h5_path}")
    raw = load_h5(h5_path)

    n = raw["n_nodes"]
    e = raw["n_edges"]
    yr_min = raw["year"].min()
    yr_max = raw["year"].max()

    print(f"  Nodes : {n:,}")
    print(f"  Edges : {e:,}")
    print(f"  Year  : {yr_min:.0f} – {yr_max:.0f}")

    # Check 0-based indices are in range
    assert raw["edge_row"].min() >= 0,       "edge_row contains negative index"
    assert raw["edge_row"].max() < n,        "edge_row out of range"
    assert raw["edge_col"].min() >= 0,       "edge_col contains negative index"
    assert raw["edge_col"].max() < n,        "edge_col out of range"
    assert len(raw["year"]) == n,            "year length != n_nodes"
    print("  Index bounds: OK")

    # Reconstruct scipy sparse
    A = to_scipy_sparse(raw)
    assert A.shape == (n, n),               "sparse matrix shape mismatch"
    assert A.nnz == e,                      "edge count mismatch after sparse reconstruct"
    print(f"  Scipy sparse: {A.shape}, nnz={A.nnz:,} — OK")

    # PyG (if available)
    if HAS_TORCH:
        data = to_pyg(raw)
        assert data.num_nodes == n
        assert data.edge_index.shape == (2, e)
        assert data.year.shape == (n,)
        print(f"  PyG Data: num_nodes={data.num_nodes:,}, edge_index={tuple(data.edge_index.shape)} — OK")
    else:
        print("  PyG: skipped (torch not installed)")

    print("Round-trip test PASSED.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load APS HDF5 → round-trip test")
    parser.add_argument(
        "--h5", default=str(_DEFAULT_H5),
        help="Path to aps-2022-citation-graph.h5",
    )
    args = parser.parse_args()
    round_trip_test(args.h5)
