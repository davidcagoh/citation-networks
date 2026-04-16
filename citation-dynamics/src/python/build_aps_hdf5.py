"""build_aps_hdf5.py — Build APS citation graph HDF5 from CSV + JSON metadata.

Reads:
    data/processed/aps-dataset-citations-2022.csv   (9.8M citation pairs)
    <metadata_dir>/.../*.json                        (pubDate per DOI)

Writes:
    data/exported/aps-2022-citation-graph.h5
        /edge_row  int32[E]       source node index, 0-based
        /edge_col  int32[E]       dest node index, 0-based
        /year      float32[N]     publication year (0.0 if unknown)
        /doi       bytes[N]       DOI string per node (ASCII)
        attrs: n_nodes, n_edges, created

Node ordering: first-occurrence order from CSV reading (replicates MATLAB doi_map).

Usage:
    python build_aps_hdf5.py
    python build_aps_hdf5.py --csv PATH --metadata PATH --out PATH
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import h5py
import numpy as np

_HERE = Path(__file__).parent
_ROOT = _HERE / "../.."
_DEFAULT_CSV  = _ROOT / "data/processed/aps-dataset-citations-2022.csv"
_DEFAULT_META = Path("/Users/davidgoh/LocalFiles/2024_duke_thesis_deprecated/cs493/aps-dataset-metadata-2022")
_DEFAULT_OUT  = _ROOT / "data/exported/aps-2022-citation-graph.h5"


# ---------------------------------------------------------------------------
# Step 1: Build doi_map (first-occurrence order) from CSV
# ---------------------------------------------------------------------------

def build_doi_map_and_edges(csv_path: Path) -> tuple[dict[str, int], list[int], list[int]]:
    """Read CSV, assign node indices in first-occurrence order.

    Returns
    -------
    doi_map : dict[str, int]  0-based node index per DOI
    row     : list[int]       COO source indices
    col     : list[int]       COO dest indices
    """
    doi_map: dict[str, int] = {}
    row: list[int] = []
    col: list[int] = []

    print(f"Reading CSV: {csv_path}")
    t0 = time.time()
    n_lines = 0

    with open(csv_path, "r", encoding="utf-8") as fh:
        next(fh)  # skip header
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            comma = line.index(",")
            a = line[:comma]
            b = line[comma + 1:]

            if a not in doi_map:
                doi_map[a] = len(doi_map)
            if b not in doi_map:
                doi_map[b] = len(doi_map)

            row.append(doi_map[a])
            col.append(doi_map[b])

            n_lines += 1
            if n_lines % 1_000_000 == 0:
                print(f"  {n_lines:,} edges read  ({time.time()-t0:.1f}s)")

    print(f"  Done: {n_lines:,} edges, {len(doi_map):,} unique nodes  ({time.time()-t0:.1f}s)")
    return doi_map, row, col


# ---------------------------------------------------------------------------
# Step 2: Parse pubDate from JSON metadata
# ---------------------------------------------------------------------------

def build_pubdate_map(metadata_dir: Path) -> dict[str, float]:
    """Walk metadata directory, extract {doi: year} for all JSON files."""
    print(f"Scanning metadata: {metadata_dir}")
    t0 = time.time()

    pubdate: dict[str, float] = {}
    n_files = 0
    n_errors = 0

    for json_path in metadata_dir.rglob("*.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as fh:
                obj = json.load(fh)
            doi = obj.get("id", "")
            date_str = obj.get("date", "")
            if doi and date_str:
                year = float(date_str[:4])
                pubdate[doi] = year
        except Exception:
            n_errors += 1

        n_files += 1
        if n_files % 100_000 == 0:
            print(f"  {n_files:,} files scanned  ({time.time()-t0:.1f}s)")

    print(f"  Done: {n_files:,} files, {len(pubdate):,} dates found, {n_errors} errors  ({time.time()-t0:.1f}s)")
    return pubdate


# ---------------------------------------------------------------------------
# Step 3: Assemble arrays and write HDF5
# ---------------------------------------------------------------------------

def write_hdf5(
    out_path: Path,
    doi_map: dict[str, int],
    row: list[int],
    col: list[int],
    pubdate_map: dict[str, float],
) -> None:
    N = len(doi_map)
    E = len(row)

    print(f"Assembling arrays: N={N:,}, E={E:,}")

    # doi array: index → DOI string
    doi_arr = [""] * N
    for doi_str, idx in doi_map.items():
        doi_arr[idx] = doi_str

    # year array
    year_arr = np.zeros(N, dtype=np.float32)
    n_matched = 0
    for i, doi_str in enumerate(doi_arr):
        y = pubdate_map.get(doi_str, 0.0)
        if y:
            year_arr[i] = y
            n_matched += 1
    print(f"  Year coverage: {n_matched:,} / {N:,} nodes ({100*n_matched/N:.1f}%)")

    edge_row = np.array(row, dtype=np.int32)
    edge_col = np.array(col, dtype=np.int32)

    # Deduplicate edges (keep first occurrence; sparse sum would also work)
    print("  Deduplicating edges...")
    edge_pairs = np.unique(np.stack([edge_row, edge_col], axis=1), axis=0)
    edge_row = edge_pairs[:, 0].astype(np.int32)
    edge_col = edge_pairs[:, 1].astype(np.int32)
    E_dedup = len(edge_row)
    print(f"  Edges after dedup: {E_dedup:,} (dropped {E - E_dedup:,} duplicates)")

    # Encode DOI strings as fixed-length ASCII bytes for simple HDF5 storage
    max_len = max((len(s) for s in doi_arr), default=0)
    doi_bytes = np.array([s.encode("ascii") for s in doi_arr],
                         dtype=f"S{max(max_len, 1)}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    print(f"Writing HDF5: {out_path}")
    with h5py.File(out_path, "w") as f:
        f.create_dataset("edge_row", data=edge_row, compression="gzip", compression_opts=4)
        f.create_dataset("edge_col", data=edge_col, compression="gzip", compression_opts=4)
        f.create_dataset("year",     data=year_arr, compression="gzip", compression_opts=4)
        f.create_dataset("doi",      data=doi_bytes, compression="gzip", compression_opts=4)
        f.attrs["n_nodes"] = np.int32(N)
        f.attrs["n_edges"] = np.int32(E_dedup)
        f.attrs["created"] = time.strftime("%Y-%m-%d")

    print(f"Done.")
    print(f"  /edge_row : int32[{E_dedup:,}]")
    print(f"  /edge_col : int32[{E_dedup:,}]")
    print(f"  /year     : float32[{N:,}]")
    print(f"  /doi      : S{max_len}[{N:,}]")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Build APS HDF5 citation graph")
    parser.add_argument("--csv",      default=str(_DEFAULT_CSV),  help="Citations CSV path")
    parser.add_argument("--metadata", default=str(_DEFAULT_META), help="JSON metadata directory")
    parser.add_argument("--out",      default=str(_DEFAULT_OUT),  help="Output HDF5 path")
    parser.add_argument("--skip-metadata", action="store_true",
                        help="Skip JSON scan; year will be all zeros")
    args = parser.parse_args()

    csv_path  = Path(args.csv)
    meta_dir  = Path(args.metadata)
    out_path  = Path(args.out)

    if not csv_path.exists():
        sys.exit(f"ERROR: CSV not found: {csv_path}")

    doi_map, row, col = build_doi_map_and_edges(csv_path)

    if args.skip_metadata:
        pubdate_map: dict[str, float] = {}
        print("Skipping metadata scan (--skip-metadata).")
    elif not meta_dir.exists():
        print(f"WARNING: metadata dir not found: {meta_dir}")
        print("Continuing without year data (year will be zeros).")
        pubdate_map = {}
    else:
        pubdate_map = build_pubdate_map(meta_dir)

    write_hdf5(out_path, doi_map, row, col, pubdate_map)


if __name__ == "__main__":
    main()
