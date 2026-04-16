"""build_synthesis_subgraph.py — Phase 5 (Q-SYNTH): 1-hop subgraph around gold DOIs.

Python port of src/synthesis/build_synthesis_subgraph.m

Reads:
    data/synthesis/k17-rgc-gold-dois.txt            51 gold DOIs (one per line)
    data/exported/aps-2022-citation-graph.h5        edge_row, edge_col, doi, n_nodes

Writes:
    data/synthesis/k17-rgc-subgraph.npz
        C_sub_row  int32[M×M nnz]   COO row indices of induced subgraph
        C_sub_col  int32[M×M nnz]   COO col indices of induced subgraph
        sub_idx    int32[M]         original 0-based node indices in full graph
        gold_mask  bool[M]          True for the 51 seed gold nodes
    data/synthesis/k17-rgc-subgraph-dois.txt
        One DOI per line, matching sub_idx order

Usage:
    python build_synthesis_subgraph.py
    python build_synthesis_subgraph.py --h5 PATH --gold PATH --out-dir PATH
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import scipy.sparse as sp

_HERE = Path(__file__).parent
_ROOT = _HERE / "../.."
_DEFAULT_H5    = _ROOT / "data/exported/aps-2022-citation-graph.h5"
_DEFAULT_GOLD  = _ROOT / "data/synthesis/k17-rgc-gold-dois.txt"
_DEFAULT_OUTDIR = _ROOT / "data/synthesis"


def load_gold_dois(path: Path) -> list[str]:
    lines = [l.strip() for l in path.read_text().splitlines()]
    return [l for l in lines if l]


def load_graph(h5_path: Path) -> tuple[sp.csr_matrix, np.ndarray]:
    """Load HDF5 → (CSR adjacency, doi byte-string array)."""
    print(f"Loading HDF5: {h5_path}")
    with h5py.File(h5_path, "r") as f:
        edge_row = f["edge_row"][:].ravel().astype(np.int32)
        edge_col = f["edge_col"][:].ravel().astype(np.int32)
        n_nodes  = int(f.attrs["n_nodes"])
        doi_raw  = f["doi"][:]         # bytes array

    doi = np.array([d.decode("ascii") for d in doi_raw])
    data = np.ones(len(edge_row), dtype=np.float32)
    C = sp.csr_matrix((data, (edge_row, edge_col)), shape=(n_nodes, n_nodes))
    print(f"  N={n_nodes:,}, E={C.nnz:,}")
    return C, doi


def build_subgraph(
    C: sp.csr_matrix,
    doi: np.ndarray,
    gold_dois: list[str],
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray, int, int]:
    """Extract 1-hop induced subgraph around gold DOIs.

    Returns
    -------
    C_sub     : csr_matrix[M×M]  induced subgraph adjacency
    sub_idx   : int32[M]         original 0-based node indices
    gold_mask : bool[M]          True for gold seed nodes
    n_found   : int              gold DOIs matched in corpus
    n_neighbors : int            1-hop neighbor count
    """
    # Match gold DOIs → node indices
    doi_to_idx = {d: i for i, d in enumerate(doi)}
    gold_idx = []
    n_missing = 0
    for gd in gold_dois:
        idx = doi_to_idx.get(gd)
        if idx is not None:
            gold_idx.append(idx)
        else:
            n_missing += 1

    n_found = len(gold_idx)
    print(f"  Gold DOIs matched: {n_found} / {len(gold_dois)} ({n_missing} missing from corpus)")
    if n_found == 0:
        sys.exit("ERROR: No gold DOIs found in corpus. Check DOI format.")

    gold_idx_arr = np.array(gold_idx, dtype=np.int64)

    # 1-hop expansion: gold cites others + others cite gold
    C_csr = C.tocsr()
    # Gold → others (rows)
    rows_out = C_csr[gold_idx_arr, :]
    _, nbr_out = rows_out.nonzero()

    # Others → gold (columns) — use CSC for fast column access
    C_csc = C.tocsc()
    cols_in = C_csc[:, gold_idx_arr]
    nbr_in, _ = cols_in.nonzero()

    all_idx = np.union1d(
        np.union1d(gold_idx_arr, nbr_out.astype(np.int64)),
        nbr_in.astype(np.int64),
    )
    all_idx = np.sort(all_idx)
    sub_idx = all_idx.astype(np.int32)
    n_sub = len(sub_idx)
    n_neighbors = n_sub - n_found

    print(f"  Gold seeds      : {n_found}")
    print(f"  1-hop neighbors : {n_neighbors}")
    print(f"  Subgraph nodes  : {n_sub}")

    # Induced subgraph
    C_sub = C_csr[all_idx, :][:, all_idx].tocsr()
    print(f"  C_sub: {n_sub}×{n_sub}, nnz={C_sub.nnz:,}")

    gold_mask = np.isin(all_idx, gold_idx_arr)

    return C_sub, sub_idx, gold_mask, n_found, n_neighbors


def save_outputs(
    out_dir: Path,
    C_sub: sp.csr_matrix,
    sub_idx: np.ndarray,
    gold_mask: np.ndarray,
    sub_dois: list[str],
    n_found: int,
    n_neighbors: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save sparse subgraph as COO npz
    coo = C_sub.tocoo()
    npz_path = out_dir / "k17-rgc-subgraph.npz"
    np.savez_compressed(
        npz_path,
        C_sub_row  = coo.row.astype(np.int32),
        C_sub_col  = coo.col.astype(np.int32),
        sub_idx    = sub_idx,
        gold_mask  = gold_mask,
        n_found    = np.array([n_found], dtype=np.int32),
        n_neighbors = np.array([n_neighbors], dtype=np.int32),
        n_sub      = np.array([len(sub_idx)], dtype=np.int32),
    )
    print(f"Saved: {npz_path}")

    # Save DOI list (human-readable, matches sub_idx order)
    doi_path = out_dir / "k17-rgc-subgraph-dois.txt"
    doi_path.write_text("\n".join(sub_dois) + "\n")
    print(f"Saved: {doi_path}")

    print(f"\nSummary: {len(sub_idx)} nodes ({n_found} gold seeds + {n_neighbors} neighbors), nnz={C_sub.nnz:,}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Q-SYNTH 1-hop subgraph")
    parser.add_argument("--h5",      default=str(_DEFAULT_H5),     help="HDF5 citation graph")
    parser.add_argument("--gold",    default=str(_DEFAULT_GOLD),   help="Gold DOI list (.txt)")
    parser.add_argument("--out-dir", default=str(_DEFAULT_OUTDIR), help="Output directory")
    args = parser.parse_args()

    h5_path  = Path(args.h5)
    gold_path = Path(args.gold)
    out_dir  = Path(args.out_dir)

    if not h5_path.exists():
        sys.exit(f"ERROR: HDF5 not found: {h5_path}\nRun build_aps_hdf5.py first.")
    if not gold_path.exists():
        sys.exit(f"ERROR: Gold DOI list not found: {gold_path}")

    gold_dois = load_gold_dois(gold_path)
    print(f"Gold DOIs loaded: {len(gold_dois)}")

    C, doi = load_graph(h5_path)
    C_sub, sub_idx, gold_mask, n_found, n_neighbors = build_subgraph(C, doi, gold_dois)

    sub_dois = [doi[i] for i in sub_idx]
    save_outputs(out_dir, C_sub, sub_idx, gold_mask, sub_dois, n_found, n_neighbors)


if __name__ == "__main__":
    main()
