"""leiden_cluster.py — Leiden community detection on APS citation graph.

Replaces deps/+leiden/ MATLAB wrapper. Uses leidenalg + igraph (pure Python).

Reads:
    data/exported/aps-2022-citation-graph.h5   (or any HDF5 with edge_row/edge_col)

Writes:
    data/exported/aps-2022-leiden-{resolution}.npz
        membership  int32[N]   community label per node

Usage:
    python leiden_cluster.py
    python leiden_cluster.py --h5 PATH --resolution 1.0 --out PATH
    python leiden_cluster.py --subgraph data/synthesis/k17-rgc-subgraph.npz \
                              --dois    data/synthesis/k17-rgc-subgraph-dois.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import h5py
import igraph as ig
import leidenalg
import numpy as np

_HERE = Path(__file__).parent
_ROOT = _HERE / "../.."
_DEFAULT_H5  = _ROOT / "data/exported/aps-2022-citation-graph.h5"
_DEFAULT_OUT = _ROOT / "data/exported"


def load_edges_from_hdf5(h5_path: Path) -> tuple[np.ndarray, np.ndarray, int]:
    with h5py.File(h5_path, "r") as f:
        row      = f["edge_row"][:].ravel().astype(np.int32)
        col      = f["edge_col"][:].ravel().astype(np.int32)
        n_nodes  = int(f.attrs["n_nodes"])
    return row, col, n_nodes


def load_edges_from_npz(npz_path: Path) -> tuple[np.ndarray, np.ndarray, int]:
    """Load COO edges from a subgraph .npz (build_synthesis_subgraph output)."""
    d = np.load(npz_path)
    row = d["C_sub_row"].astype(np.int32)
    col = d["C_sub_col"].astype(np.int32)
    n_nodes = int(d["n_sub"][0])
    return row, col, n_nodes


def build_igraph(row: np.ndarray, col: np.ndarray, n_nodes: int,
                 directed: bool = True) -> ig.Graph:
    """Build igraph from COO edge arrays."""
    print(f"Building igraph: {n_nodes:,} nodes, {len(row):,} edges (directed={directed})")
    edges = list(zip(row.tolist(), col.tolist()))
    G = ig.Graph(n=n_nodes, edges=edges, directed=directed)
    return G


def run_leiden(
    G: ig.Graph,
    resolution: float = 1.0,
    n_iterations: int = -1,
    seed: int = 42,
) -> np.ndarray:
    """Run Leiden with ModularityVertexPartition.

    Parameters
    ----------
    resolution   : higher → more, smaller communities
    n_iterations : -1 runs until convergence
    seed         : random seed for reproducibility
    """
    print(f"Running Leiden (resolution={resolution}, n_iterations={n_iterations}, seed={seed})")
    partition = leidenalg.find_partition(
        G,
        leidenalg.ModularityVertexPartition,
        n_iterations=n_iterations,
        seed=seed,
    )
    membership = np.array(partition.membership, dtype=np.int32)
    n_communities = membership.max() + 1
    sizes = np.bincount(membership)
    print(f"  Communities : {n_communities:,}")
    print(f"  Largest     : {sizes.max():,} nodes")
    print(f"  Median size : {int(np.median(sizes))}")
    print(f"  Modularity  : {partition.modularity:.4f}")
    return membership


def main() -> None:
    parser = argparse.ArgumentParser(description="Leiden clustering on APS citation graph")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--h5",        default=str(_DEFAULT_H5), help="Full graph HDF5")
    group.add_argument("--subgraph",  help="Subgraph .npz (from build_synthesis_subgraph.py)")
    parser.add_argument("--resolution",   type=float, default=1.0,  help="Leiden resolution (default 1.0)")
    parser.add_argument("--n-iterations", type=int,   default=-1,   help="Leiden iterations (-1 = converge)")
    parser.add_argument("--seed",         type=int,   default=42,   help="RNG seed")
    parser.add_argument("--undirected",   action="store_true",       help="Treat graph as undirected")
    parser.add_argument("--out",          default=str(_DEFAULT_OUT), help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.out)
    directed = not args.undirected

    if args.subgraph:
        npz_path = Path(args.subgraph)
        if not npz_path.exists():
            sys.exit(f"ERROR: subgraph file not found: {npz_path}")
        print(f"Loading subgraph: {npz_path}")
        row, col, n_nodes = load_edges_from_npz(npz_path)
        tag = npz_path.stem
    else:
        h5_path = Path(args.h5)
        if not h5_path.exists():
            sys.exit(f"ERROR: HDF5 not found: {h5_path}\nRun build_aps_hdf5.py first.")
        print(f"Loading graph: {h5_path}")
        row, col, n_nodes = load_edges_from_hdf5(h5_path)
        tag = "aps-2022"

    G = build_igraph(row, col, n_nodes, directed=directed)
    membership = run_leiden(G, args.resolution, args.n_iterations, args.seed)

    out_dir.mkdir(parents=True, exist_ok=True)
    res_str = f"{args.resolution:.2f}".replace(".", "p")
    out_path = out_dir / f"{tag}-leiden-{res_str}.npz"
    np.savez_compressed(out_path, membership=membership)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
