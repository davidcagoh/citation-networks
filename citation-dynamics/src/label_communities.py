"""label_communities.py — Print top-5 cited papers per large community for hand-labelling.

For each of the 25 communities with >=30 nodes, computes in-degree within the full
graph and prints the top-5 papers (DOI + year) so the user can assign a physics-area
label (condensed matter / particle / quantum optics / etc.).

Also writes data/analysis/community_labels_template.csv with columns:
  community_id, n_nodes, year_median, year_iqr, gamma, physics_label (blank)
  plus 5 columns doi_top1..doi_top5 and year_top1..year_top5.

Fill in physics_label by hand after running this script.

Usage:
    python src/label_communities.py
    python src/label_communities.py --min_nodes 30 --top_n 5
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import h5py
import numpy as np

_HERE = Path(__file__).parent
_ROOT = _HERE / ".."

_DEFAULT_H5     = _ROOT / "data/exported/aps-2022-citation-graph.h5"
_DEFAULT_LEIDEN = _ROOT / "data/exported/aps-2022-leiden-1p00.npz"
_DEFAULT_FITS   = _ROOT / "data/analysis/zeitgeist_community_fits.csv"
_OUT_CSV        = _ROOT / "data/analysis/community_labels_template.csv"


def load_data(
    h5_path: Path,
    leiden_path: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    with h5py.File(h5_path, "r") as f:
        doi  = np.array([d.decode() if isinstance(d, bytes) else d for d in f["doi"][:]])
        year = f["year"][:].ravel().astype(float)
        col  = f["edge_col"][:].ravel().astype(np.int64)
        n    = int(f.attrs["n_nodes"])
    membership = np.load(leiden_path)["membership"].ravel().astype(np.int32)
    return doi, year, col, membership, n


def compute_indegree(col: np.ndarray, n: int) -> np.ndarray:
    indeg = np.zeros(n, dtype=np.int64)
    np.add.at(indeg, col, 1)
    return indeg


def load_fits(fits_path: Path) -> dict[int, dict]:
    fits: dict[int, dict] = {}
    with open(fits_path, newline="") as fh:
        for row in csv.DictReader(fh):
            cid = int(row["community_id"])
            fits[cid] = row
    return fits


def main(min_nodes: int = 30, top_n: int = 5) -> None:
    print("Loading HDF5 + Leiden …")
    doi, year, col, membership, n = load_data(_DEFAULT_H5, _DEFAULT_LEIDEN)
    print(f"  {n:,} nodes, {len(col):,} edges loaded")

    indeg = compute_indegree(col, n)
    fits  = load_fits(_DEFAULT_FITS)

    community_ids, counts = np.unique(membership, return_counts=True)
    large = [(int(c), int(k)) for c, k in zip(community_ids, counts) if k >= min_nodes]
    large.sort(key=lambda x: -x[1])
    print(f"  {len(large)} communities with ≥{min_nodes} nodes\n")

    fieldnames = (
        ["community_id", "n_nodes", "year_median", "year_iqr", "gamma", "physics_label"]
        + [f"doi_top{i+1}" for i in range(top_n)]
        + [f"year_top{i+1}" for i in range(top_n)]
    )
    rows = []

    for cid, n_nodes in large:
        mask   = membership == cid
        nodes  = np.where(mask)[0]
        top_idx = nodes[np.argsort(indeg[nodes])[::-1][:top_n]]

        fit = fits.get(cid, {})
        row: dict = {
            "community_id": cid,
            "n_nodes":      n_nodes,
            "year_median":  fit.get("year_median", ""),
            "year_iqr":     fit.get("year_iqr", ""),
            "gamma":        fit.get("gamma", ""),
            "physics_label": "",
        }
        for rank, idx in enumerate(top_idx):
            row[f"doi_top{rank+1}"]  = doi[idx]
            row[f"year_top{rank+1}"] = int(year[idx]) if year[idx] > 0 else ""
        rows.append(row)

        print(f"Community {cid:3d}  n={n_nodes:6,}  "
              f"γ={fit.get('gamma','?'):>6}  "
              f"median_year={fit.get('year_median','?')}")
        for rank, idx in enumerate(top_idx):
            yr = int(year[idx]) if year[idx] > 0 else "?"
            print(f"  #{rank+1}  {yr}  {doi[idx]}")
        print()

    _OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(_OUT_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Template written → {_OUT_CSV}")
    print("Fill in the 'physics_label' column, then save as community_labels.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min_nodes", type=int, default=30)
    parser.add_argument("--top_n",     type=int, default=5)
    args = parser.parse_args()
    main(args.min_nodes, args.top_n)
