"""phase4_timecurves.py — Time Curves for temporal phase visualization.

Implements Bach et al. (IEEE TVCG 2015) Time Curves for APS citation dynamics.

Pipeline:
    NST embeddings (N × D)
    → per-year centroid (T × D)
    → T×T pairwise distance matrix
    → Time Curves (T × 2 curve)
    → cusp/loop detection
    → matplotlib plot

Loops  = recurring Zeitgeist phases (curve self-intersects)
Cusps  = sharp paradigm transitions (curve reverses sharply)

Usage:
    # After NST training:
    python src/phase4_timecurves.py \
        --embeddings data/exported/aps-nst-embeddings.npy \
        --meta       data/exported/aps-nst-embeddings-meta.npz \
        --out        data/analysis/

    # Proxy run (before NST, uses raw structural features):
    python src/phase4_timecurves.py --proxy \
        --features   data/exported/aps_nst_seed42_maxe500k_node_features.npy \
        --meta       data/exported/aps-nst-embeddings-meta.npz \
        --out        data/analysis/
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.spatial.distance import cdist
from scipy.linalg import eigh

_HERE = Path(__file__).parent
_ROOT = _HERE / ".."


# ---------------------------------------------------------------------------
# Core Time Curves algorithm
# ---------------------------------------------------------------------------

@dataclass
class TimeCurvesResult:
    coords:     np.ndarray          # [T, 2] curve coordinates
    years:      np.ndarray          # [T] year labels
    cusps:      list[int] = field(default_factory=list)    # indices of cusp years
    loops:      list[tuple[int,int]] = field(default_factory=list)  # (i,j) loop pairs
    stress:     float = 0.0


def _mds_init(D: np.ndarray) -> np.ndarray:
    """Classical MDS: embed T points in 2D from T×T distance matrix."""
    T = D.shape[0]
    D2 = D ** 2
    J = np.eye(T) - np.ones((T, T)) / T
    B = -0.5 * J @ D2 @ J
    # Two largest eigenvalues/vectors
    vals, vecs = eigh(B, subset_by_index=[T-2, T-1])
    coords = vecs * np.sqrt(np.maximum(vals, 0))
    return coords[:, ::-1]  # descending eigenvalue order → [T, 2]


def _stress(coords: np.ndarray, D: np.ndarray, weights: np.ndarray) -> float:
    """Normalised stress."""
    D_hat = cdist(coords, coords)
    diff  = D_hat - D
    return float(np.sum(weights * diff**2) / (np.sum(weights * D**2) + 1e-12))


def _smacof_step(coords: np.ndarray, D: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """One SMACOF (stress majorization) update step — vectorised."""
    T = D.shape[0]
    D_hat = cdist(coords, coords)
    D_hat_safe = np.where(D_hat < 1e-10, 1e-10, D_hat)

    # B matrix: B[i,j] = -w_ij * d_ij / d_hat_ij  (i≠j)
    B = -weights * D / D_hat_safe
    np.fill_diagonal(B, 0.0)
    np.fill_diagonal(B, -B.sum(axis=1))

    # W diagonal
    W = weights.sum(axis=1)  # [T]

    # New coords: (1/W[i]) * (B @ coords)[i]
    new_coords = (B @ coords) / np.maximum(W[:, None], 1e-12)
    return new_coords


def _temporal_smooth(coords: np.ndarray, weight: float) -> np.ndarray:
    """Pull each point toward midpoint of its temporal neighbours."""
    T = coords.shape[0]
    smooth = np.empty_like(coords)
    smooth[0]    = coords[1]
    smooth[-1]   = coords[-2]
    smooth[1:-1] = 0.5 * (coords[:-2] + coords[2:])
    return (1.0 - weight) * coords + weight * smooth


def time_curves(
    D:                np.ndarray,
    years:            np.ndarray,
    temporal_weight:  float = 0.3,
    n_iter:           int   = 300,
    tol:              float = 1e-5,
) -> TimeCurvesResult:
    """Compute Time Curves embedding.

    Parameters
    ----------
    D               : [T, T] symmetric pairwise distance matrix (T = number of years)
    years           : [T] year labels in temporal order
    temporal_weight : smoothing towards temporal neighbours (0 = pure SMACOF, 1 = pure smooth)
    n_iter          : max SMACOF iterations
    tol             : early-stop tolerance on stress improvement

    Returns
    -------
    TimeCurvesResult with 2D coords, cusp/loop annotations, and final stress
    """
    T = D.shape[0]
    assert D.shape == (T, T), "D must be square"
    assert len(years) == T

    # Uniform weights (can be extended to emphasise recent years)
    weights = np.ones((T, T))
    np.fill_diagonal(weights, 0.0)

    coords = _mds_init(D)
    prev_stress = _stress(coords, D, weights)

    for _ in range(n_iter):
        coords = _smacof_step(coords, D, weights)
        coords = _temporal_smooth(coords, temporal_weight)
        s = _stress(coords, D, weights)
        if abs(prev_stress - s) < tol:
            break
        prev_stress = s

    cusps = _detect_cusps(coords)
    loops = _detect_loops(coords, years)

    return TimeCurvesResult(coords=coords, years=years,
                            cusps=cusps, loops=loops, stress=prev_stress)


# ---------------------------------------------------------------------------
# Cusp and loop detection
# ---------------------------------------------------------------------------

def _detect_cusps(coords: np.ndarray, angle_threshold_deg: float = 90.0) -> list[int]:
    """Indices where the curve turns by more than threshold degrees."""
    T = coords.shape[0]
    cusps = []
    cos_thresh = np.cos(np.radians(angle_threshold_deg))
    for i in range(1, T - 1):
        v1 = coords[i]   - coords[i-1]
        v2 = coords[i+1] - coords[i]
        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if n1 < 1e-10 or n2 < 1e-10:
            continue
        cos_a = np.dot(v1, v2) / (n1 * n2)
        if cos_a < cos_thresh:
            cusps.append(i)
    return cusps


def _segments_intersect(p1, p2, p3, p4) -> bool:
    """True if segment p1-p2 properly intersects segment p3-p4."""
    def cross2d(a, b):
        return a[0] * b[1] - a[1] * b[0]

    d1, d2 = p2 - p1, p4 - p3
    denom = cross2d(d1, d2)
    if abs(denom) < 1e-12:
        return False
    t = cross2d(p3 - p1, d2) / denom
    u = cross2d(p3 - p1, d1) / denom
    return 1e-6 < t < 1 - 1e-6 and 1e-6 < u < 1 - 1e-6


def _detect_loops(
    coords: np.ndarray,
    years:  np.ndarray,
    min_gap: int = 5,
) -> list[tuple[int, int]]:
    """Pairs (i, j) where segment i→i+1 intersects segment j→j+1 (loop)."""
    T = coords.shape[0]
    loops = []
    for i in range(T - 1):
        for j in range(i + min_gap, T - 1):
            if _segments_intersect(coords[i], coords[i+1], coords[j], coords[j+1]):
                loops.append((i, j))
    return loops


# ---------------------------------------------------------------------------
# APS-specific: build distance matrix from embeddings
# ---------------------------------------------------------------------------

def build_distance_matrix(
    embeddings: np.ndarray,   # [N, D]
    year:       np.ndarray,   # [N] integer years
    year_min:   int = 1950,
    year_max:   int = 2022,
    space_dim:  Optional[int] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Per-year centroid → T×T Euclidean distance matrix.

    Parameters
    ----------
    embeddings : [N, D] node embeddings (NST or structural features)
    year       : [N] publication years (0 = missing)
    space_dim  : use only first space_dim dims (NST spatial coords); None = use all
    year_min/max : range of years to include

    Returns
    -------
    D     : [T, T] distance matrix
    years : [T] year labels
    """
    if space_dim is not None:
        emb = embeddings[:, :space_dim]
    else:
        emb = embeddings

    valid = (year >= year_min) & (year <= year_max)
    year_v = year[valid].astype(int)
    emb_v  = emb[valid]

    years_range = np.arange(year_min, year_max + 1)
    T = len(years_range)
    D_emb = emb_v.shape[1]

    centroids = np.zeros((T, D_emb), dtype=np.float32)
    counts    = np.zeros(T, dtype=int)

    for t, y in enumerate(years_range):
        mask = year_v == y
        if mask.sum() > 0:
            centroids[t] = emb_v[mask].mean(axis=0)
            counts[t]    = mask.sum()

    # Interpolate years with no papers (rare)
    for t in range(T):
        if counts[t] == 0:
            neighbours = [centroids[t2] for t2 in [t-1, t+1] if 0 <= t2 < T and counts[t2] > 0]
            if neighbours:
                centroids[t] = np.mean(neighbours, axis=0)

    D = cdist(centroids, centroids, metric="euclidean").astype(np.float64)
    return D, years_range


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_timecurves(
    result:   TimeCurvesResult,
    title:    str  = "APS Citation Network — Time Curves",
    out_path: Optional[Path] = None,
) -> None:
    try:
        import matplotlib
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available — skipping plot")
        return

    years = result.years
    coords = result.coords
    T = len(years)

    fig, ax = plt.subplots(figsize=(10, 8))

    # Colour the curve by year
    cmap = matplotlib.colormaps["plasma"]
    colours = cmap(np.linspace(0, 1, T - 1))

    for i in range(T - 1):
        ax.plot(coords[i:i+2, 0], coords[i:i+2, 1],
                color=colours[i], linewidth=1.8, alpha=0.8)

    # Year labels (every 10 years)
    for i, y in enumerate(years):
        if y % 10 == 0:
            ax.annotate(str(y), coords[i], fontsize=7, ha="center",
                        xytext=(0, 5), textcoords="offset points", color="dimgray")

    # Cusps
    for ci in result.cusps:
        ax.scatter(*coords[ci], color="red", s=80, zorder=5, marker="^",
                   label="cusp" if ci == result.cusps[0] else "")

    # Loops (mark midpoints)
    seen = set()
    for (li, lj) in result.loops:
        mid_i = 0.5 * (coords[li] + coords[li+1])
        mid_j = 0.5 * (coords[lj] + coords[lj+1])
        ax.plot([mid_i[0], mid_j[0]], [mid_i[1], mid_j[1]],
                "g--", linewidth=0.8, alpha=0.5)
        label = "loop" if (li, lj) not in seen else ""
        ax.scatter(*mid_i, color="green", s=50, zorder=5, marker="o", label=label)
        seen.add((li, lj))

    # Colourbar (year)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(years[0], years[-1]))
    sm.set_array([])
    plt.colorbar(sm, ax=ax, label="Year")

    if result.cusps or result.loops:
        ax.legend(fontsize=8)

    ax.set_title(f"{title}\n(stress={result.stress:.4f}, "
                 f"cusps={len(result.cusps)}, loops={len(result.loops)})")
    ax.set_xlabel("Dim 1")
    ax.set_ylabel("Dim 2")
    ax.set_aspect("equal")
    plt.tight_layout()

    if out_path:
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        print(f"Saved plot: {out_path}")
    else:
        plt.show()
    plt.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Time Curves for APS citation phases")
    parser.add_argument("--embeddings", default=None,
                        help="NST embeddings .npy [N, D] (space+time dims)")
    parser.add_argument("--features",   default=None,
                        help="Structural features .npy [N, 4] (proxy mode)")
    parser.add_argument("--meta",       default=str(_ROOT / "data/exported/aps-nst-embeddings-meta.npz"),
                        help="Meta npz with doi, year, membership arrays")
    parser.add_argument("--out",        default=str(_ROOT / "data/analysis"))
    parser.add_argument("--space_dim",  type=int, default=4,
                        help="Spatial dims to use from NST embeddings (default 4)")
    parser.add_argument("--year_min",   type=int, default=1950)
    parser.add_argument("--year_max",   type=int, default=2022)
    parser.add_argument("--temporal_weight", type=float, default=0.3)
    parser.add_argument("--n_iter",     type=int, default=300)
    parser.add_argument("--proxy",      action="store_true",
                        help="Use structural features instead of NST embeddings")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load metadata
    meta_path = Path(args.meta)
    print(f"Loading metadata: {meta_path}")
    meta = np.load(meta_path)
    year = meta["year"].ravel().astype(float)

    # Load embeddings
    if args.proxy:
        if args.features is None:
            raise ValueError("--features required in proxy mode")
        print(f"Proxy mode: loading structural features from {args.features}")
        emb = np.load(args.features)
        space_dim = None  # use all 4 features
        tag = "proxy"
    else:
        if args.embeddings is None:
            raise ValueError("--embeddings required (or use --proxy)")
        print(f"Loading NST embeddings: {args.embeddings}")
        emb = np.load(args.embeddings)
        space_dim = args.space_dim
        tag = "nst"

    print(f"  embeddings shape: {emb.shape}")
    print(f"  year range in meta: {int(year[year>0].min())}–{int(year[year>0].max())}")

    # Build distance matrix
    print(f"Building distance matrix ({args.year_min}–{args.year_max}) ...")
    D, years = build_distance_matrix(
        emb, year,
        year_min=args.year_min, year_max=args.year_max,
        space_dim=space_dim,
    )
    print(f"  D shape: {D.shape}, range [{D.min():.4f}, {D.max():.4f}]")

    # Normalise D to [0, 1] for stable optimisation
    D_norm = D / (D.max() + 1e-12)

    # Run Time Curves
    print(f"Running Time Curves (n_iter={args.n_iter}, temporal_weight={args.temporal_weight}) ...")
    result = time_curves(D_norm, years,
                         temporal_weight=args.temporal_weight,
                         n_iter=args.n_iter)

    print(f"  Final stress: {result.stress:.6f}")
    print(f"  Cusps ({len(result.cusps)}): years {[int(years[c]) for c in result.cusps]}")
    print(f"  Loops ({len(result.loops)}): year pairs "
          f"{[(int(years[i]), int(years[j])) for i,j in result.loops[:5]]}"
          f"{'...' if len(result.loops) > 5 else ''}")

    # Save results
    coords_path = out_dir / f"timecurves_{tag}_coords.npy"
    np.save(coords_path, result.coords)
    np.savez(out_dir / f"timecurves_{tag}_result.npz",
             coords=result.coords,
             years=years,
             cusps=np.array(result.cusps),
             loops=np.array(result.loops) if result.loops else np.empty((0, 2), int),
             stress=np.array(result.stress))
    print(f"Saved: {coords_path}")

    # Plot
    plot_timecurves(result,
                    title=f"APS Citation Network — Time Curves ({'NST' if tag=='nst' else 'structural features proxy'})",
                    out_path=out_dir / f"timecurves_{tag}_plot.png")


if __name__ == "__main__":
    main()
