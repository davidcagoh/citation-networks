"""utils.py — Shared I/O and statistical helpers for citation-dynamics.

Import from any script in src/:
    from utils import load_h5, load_leiden, compute_indegree
    from utils import mle_powerlaw_exponent, ks_pvalue
"""

from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_h5(h5_path: Path) -> dict:
    """Load APS HDF5 citation graph.

    Returns dict with keys:
        doi      : str ndarray [N]
        year     : float32 ndarray [N]
        edge_row : int32 ndarray [E]
        edge_col : int32 ndarray [E]
        n_nodes  : int
        n_edges  : int
    """
    with h5py.File(h5_path, "r") as f:
        edge_row = f["edge_row"][:].ravel().astype(np.int32)
        edge_col = f["edge_col"][:].ravel().astype(np.int32)
        year     = f["year"][:].ravel().astype(np.float32)
        n_nodes  = int(f.attrs["n_nodes"])
        n_edges  = int(f.attrs.get("n_edges", len(edge_row)))
        doi = np.array(
            [d.decode("ascii") if isinstance(d, bytes) else d for d in f["doi"][:]],
            dtype=str,
        ) if "doi" in f else np.array([], dtype=str)
    return dict(
        doi=doi,
        year=year,
        edge_row=edge_row,
        edge_col=edge_col,
        n_nodes=n_nodes,
        n_edges=n_edges,
    )


def load_leiden(leiden_path: Path) -> np.ndarray:
    """Return membership int32 array [N] from a Leiden .npz."""
    return np.load(leiden_path)["membership"].ravel().astype(np.int32)


def compute_indegree(edge_col: np.ndarray, n_nodes: int) -> np.ndarray:
    """Compute in-degree for each node from edge_col COO array."""
    indeg = np.zeros(n_nodes, dtype=np.int64)
    np.add.at(indeg, edge_col, 1)
    return indeg


# ---------------------------------------------------------------------------
# Power-law fitting (Clauset et al. 2009, discrete case)
# ---------------------------------------------------------------------------

def mle_powerlaw_exponent(degrees: np.ndarray, xmin: int) -> float:
    """Maximum-likelihood estimate of power-law exponent γ.

    Only uses values >= xmin. Returns nan if fewer than 2 values qualify.
    Formula: γ = 1 + n [Σ ln(k_i / (xmin - 0.5))]^{-1}
    """
    tail = degrees[degrees >= xmin].astype(float)
    n = len(tail)
    if n < 2:
        return float("nan")
    return 1.0 + n / np.sum(np.log(tail / (xmin - 0.5)))


def ks_pvalue(
    degrees: np.ndarray,
    xmin: int,
    gamma: float,
    n_boot: int = 500,
) -> float:
    """Bootstrap KS p-value for a power-law fit (Clauset et al. §4).

    Returns the fraction of bootstrap samples whose KS stat >= observed.
    n_boot=500 for publication quality; 200 for quick checks.
    """
    tail = degrees[degrees >= xmin].astype(float)
    n = len(tail)
    if n < 10 or np.isnan(gamma):
        return float("nan")

    def _powerlaw_cdf(k: np.ndarray, g: float, xm: int) -> np.ndarray:
        return 1.0 - (k / xm) ** (1.0 - g)

    k_unique = np.unique(tail)
    empirical_cdf    = np.array([np.mean(tail <= k) for k in k_unique])
    theoretical_cdf  = _powerlaw_cdf(k_unique, gamma, xmin)
    ks_obs = np.max(np.abs(empirical_cdf - theoretical_cdf))

    rng = np.random.default_rng(42)
    count_exceed = 0
    for _ in range(n_boot):
        u = rng.uniform(size=n)
        synth = np.floor(xmin * (1.0 - u) ** (1.0 / (1.0 - gamma))).astype(float)
        synth = np.clip(synth, xmin, None)
        g_synth = mle_powerlaw_exponent(synth, xmin)
        if np.isnan(g_synth):
            continue
        k_s = np.unique(synth)
        emp_s = np.array([np.mean(synth <= k) for k in k_s])
        th_s  = _powerlaw_cdf(k_s, g_synth, xmin)
        ks_s  = np.max(np.abs(emp_s - th_s))
        if ks_s >= ks_obs:
            count_exceed += 1

    return count_exceed / n_boot
