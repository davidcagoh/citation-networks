"""aps_adapter.py — APS citation graph data adapter for Neural Spacetime training.

Mirrors arxiv_generation.py but replaces OGB/SPECTER features with
engineered structural features derived from the APS HDF5 + Leiden output.

Node features (dim=4):
    0: year_norm       — publication year normalised to [0, 1] over 1893–2022
    1: log_indegree    — log1p(in_degree), normalised by max
    2: log_outdegree   — log1p(out_degree), normalised by max
    3: community_norm  — Leiden community ID normalised by n_communities

Edge weight:
    Cosine similarity of node feature vectors, clipped to [0.01, 1.0].
    (Same convention as arxiv_generation.py, adapted for low-dim features.)

Outputs:
    data_x : float32[E_sample, 8]   — [feat_v || feat_u] for each sampled edge u→v
    data_y : float32[E_sample]      — edge weight (cosine similarity)
    node_features : float32[N, 4]   — per-node feature matrix (for embedding export)

Usage:
    from aps_adapter import load_aps_data
    data_x, data_y, node_features = load_aps_data()

    python aps_adapter.py   # quick self-test
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path

import h5py
import numpy as np
import torch

_HERE = Path(__file__).parent
_ROOT = _HERE / ".."
_DEFAULT_H5     = _ROOT / "data/exported/aps-2022-citation-graph.h5"
_DEFAULT_LEIDEN = _ROOT / "data/exported/aps-2022-leiden-1p00.npz"
_DEFAULT_CACHE  = _ROOT / "data/exported"

FEATURE_DIM = 4          # dimensionality of engineered node features
YEAR_MIN    = 1893.0
YEAR_MAX    = 2022.0


# ---------------------------------------------------------------------------
# Feature construction
# ---------------------------------------------------------------------------

def _build_node_features(
    year: np.ndarray,
    edge_row: np.ndarray,
    edge_col: np.ndarray,
    membership: np.ndarray,
    n_communities: int,
) -> np.ndarray:
    """Return float32[N, FEATURE_DIM] node feature matrix."""
    N = len(year)

    # Year normalised to [0, 1]; missing years (0.0 in HDF5) map to 0.0
    year_norm = np.clip(
        (year - YEAR_MIN) / (YEAR_MAX - YEAR_MIN), 0.0, 1.0
    ).astype(np.float32)

    # Degree features
    in_deg  = np.bincount(edge_col, minlength=N).astype(np.float32)
    out_deg = np.bincount(edge_row, minlength=N).astype(np.float32)
    log_in  = np.log1p(in_deg)
    log_out = np.log1p(out_deg)
    max_in  = log_in.max()  if log_in.max()  > 0 else 1.0
    max_out = log_out.max() if log_out.max() > 0 else 1.0
    log_in_norm  = (log_in  / max_in ).astype(np.float32)
    log_out_norm = (log_out / max_out).astype(np.float32)

    # Community normalised to [0, 1]
    comm_norm = (membership.astype(np.float32) / max(n_communities - 1, 1))

    features = np.stack([year_norm, log_in_norm, log_out_norm, comm_norm], axis=1)
    assert features.shape == (N, FEATURE_DIM)
    return features


def _compute_edge_weights(
    features: np.ndarray,
    edge_row: np.ndarray,
    edge_col: np.ndarray,
) -> np.ndarray:
    """Cosine similarity of src/dst feature vectors, clipped to [0.01, 1.0]."""
    f_src = features[edge_row]   # [E, F]
    f_dst = features[edge_col]   # [E, F]

    norm_src = np.linalg.norm(f_src, axis=1, keepdims=True).clip(min=1e-8)
    norm_dst = np.linalg.norm(f_dst, axis=1, keepdims=True).clip(min=1e-8)
    cos_sim = (f_src / norm_src * (f_dst / norm_dst)).sum(axis=1)
    return cos_sim.clip(0.01, 1.0).astype(np.float32)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_aps_data(
    h5_path:     Path | str = _DEFAULT_H5,
    leiden_path: Path | str = _DEFAULT_LEIDEN,
    cache_dir:   Path | str = _DEFAULT_CACHE,
    max_edges:   int        = 1_000_000,
    seed:        int        = 42,
    force_rebuild: bool     = False,
) -> tuple[torch.Tensor, torch.Tensor, np.ndarray]:
    """Load and preprocess APS data for NST training.

    Parameters
    ----------
    h5_path      : HDF5 citation graph (build_aps_hdf5.py output)
    leiden_path  : Leiden membership .npz (leiden_cluster.py output)
    cache_dir    : directory for cached tensors
    max_edges    : number of edges to sample (default 1M; full graph has 9.8M)
    seed         : RNG seed for edge sampling
    force_rebuild: ignore cache and rebuild

    Returns
    -------
    data_x : torch.float32[E_sample, 2*FEATURE_DIM]  — [feat_v || feat_u] per edge
    data_y : torch.float32[E_sample]                  — cosine-similarity edge weight
    node_features : np.float32[N, FEATURE_DIM]         — for embedding export
    """
    h5_path     = Path(h5_path)
    leiden_path = Path(leiden_path)
    cache_dir   = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    tag       = f"aps_nst_seed{seed}_maxe{max_edges // 1000}k"
    dx_path   = cache_dir / f"{tag}_data_x.pt"
    dy_path   = cache_dir / f"{tag}_data_y.pt"
    feat_path = cache_dir / f"{tag}_node_features.npy"

    if not force_rebuild and dx_path.exists() and dy_path.exists() and feat_path.exists():
        print("Loading cached APS NST data …")
        data_x        = torch.load(dx_path)
        data_y        = torch.load(dy_path)
        node_features = np.load(feat_path)
        print(f"  data_x : {tuple(data_x.shape)}")
        print(f"  data_y : {tuple(data_y.shape)}")
        return data_x, data_y, node_features

    print("Building APS NST data from scratch …")

    # --- Load graph ---
    print(f"  Loading HDF5: {h5_path}")
    with h5py.File(h5_path, "r") as f:
        edge_row = f["edge_row"][:].ravel().astype(np.int32)
        edge_col = f["edge_col"][:].ravel().astype(np.int32)
        year     = f["year"][:].ravel().astype(np.float32)
    N = len(year)
    E = len(edge_row)
    print(f"  N={N:,}, E={E:,}")

    # --- Load Leiden membership ---
    print(f"  Loading Leiden: {leiden_path}")
    d = np.load(leiden_path)
    membership   = d["membership"].astype(np.int32)
    n_communities = int(membership.max()) + 1
    print(f"  Communities: {n_communities}")

    # --- Build node features ---
    node_features = _build_node_features(year, edge_row, edge_col, membership, n_communities)

    # --- Sample edges ---
    rng = np.random.default_rng(seed)
    if max_edges < E:
        idx = rng.choice(E, size=max_edges, replace=False)
        idx.sort()
        e_row = edge_row[idx]
        e_col = edge_col[idx]
        print(f"  Sampled {max_edges:,} / {E:,} edges")
    else:
        e_row = edge_row
        e_col = edge_col
        print(f"  Using all {E:,} edges")

    # --- Edge weights ---
    print("  Computing edge weights (cosine similarity) …")
    weights = _compute_edge_weights(node_features, e_row, e_col)

    # --- Pack tensors: data_x[i] = [feat_v || feat_u] for edge u→v ---
    f_src = node_features[e_row]  # source (u, citing)
    f_dst = node_features[e_col]  # dest   (v, cited)
    # Convention matches arxiv: metric(x_v, x_u) so data_x = [feat_v || feat_u]
    data_x = torch.from_numpy(np.concatenate([f_dst, f_src], axis=1))  # [E, 2*F]
    data_y = torch.from_numpy(weights)                                   # [E]

    print(f"  data_x : {tuple(data_x.shape)}, dtype={data_x.dtype}")
    print(f"  data_y : {tuple(data_y.shape)}, min={data_y.min():.3f}, max={data_y.max():.3f}")

    # --- Cache ---
    torch.save(data_x, dx_path)
    torch.save(data_y, dy_path)
    np.save(feat_path, node_features)
    print(f"  Cached to {cache_dir}/")

    return data_x, data_y, node_features


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    data_x, data_y, nf = load_aps_data(max_edges=50_000, force_rebuild=True)
    print("\nSelf-test summary:")
    print(f"  node features : {nf.shape}, range [{nf.min():.3f}, {nf.max():.3f}]")
    print(f"  data_x        : {tuple(data_x.shape)}")
    print(f"  data_y        : mean={data_y.mean():.4f}, std={data_y.std():.4f}")
    assert data_x.shape[1] == 2 * FEATURE_DIM, "feature width mismatch"
    assert data_x.shape[0] == data_y.shape[0], "x/y length mismatch"
    print("PASSED.")
