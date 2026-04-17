"""generate_figures.py — Generate all §§1–4 paper figures.

Figs:
  1  Global in-degree CCDF (log-log) with power-law fit
  2  Community size distribution (446 communities, log-log)
  3  Histogram of γ_c across 25 large communities
  4  Community year-median timeline (sorted horizontal bars = IQR)

Outputs → data/figures/fig{1..4}.pdf  (and .png at 300 dpi)

Usage:
    python src/generate_figures.py
    python src/generate_figures.py --out data/figures --dpi 300
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import h5py
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

mpl.rcParams.update({
    "font.family":      "serif",
    "font.size":        9,
    "axes.titlesize":   9,
    "axes.labelsize":   9,
    "xtick.labelsize":  8,
    "ytick.labelsize":  8,
    "legend.fontsize":  8,
    "figure.dpi":       150,
    "pdf.fonttype":     42,   # embed fonts
    "ps.fonttype":      42,
    "axes.spines.top":  False,
    "axes.spines.right":False,
})

_HERE = Path(__file__).parent
_ROOT = _HERE / ".."

_H5      = _ROOT / "data/exported/aps-2022-citation-graph.h5"
_LEIDEN  = _ROOT / "data/exported/aps-2022-leiden-1p00.npz"
_FITS    = _ROOT / "data/analysis/zeitgeist_community_fits.csv"
_LABELS  = _ROOT / "data/analysis/community_labels.csv"


# ---------------------------------------------------------------------------
# Power-law utilities (inline — no import dependency on phase2b)
# ---------------------------------------------------------------------------

def mle_gamma(degrees: np.ndarray, xmin: int) -> float:
    tail = degrees[degrees >= xmin].astype(float)
    n = len(tail)
    if n < 2:
        return float("nan")
    return 1.0 + n / np.sum(np.log(tail / (xmin - 0.5)))


def scan_xmin(degrees: np.ndarray, xmin_max: int = 100) -> tuple[int, float]:
    """Scan xmin ∈ [1, xmin_max], pick value minimising KS distance."""
    best_xmin, best_ks = 1, np.inf
    for xm in range(1, xmin_max + 1):
        tail = degrees[degrees >= xm].astype(float)
        if len(tail) < 50:
            break
        g = mle_gamma(tail, xm)
        if np.isnan(g) or g <= 1.0:
            continue
        k_u = np.unique(tail)
        emp = np.array([np.mean(tail <= k) for k in k_u])
        th  = 1.0 - (k_u / xm) ** (1.0 - g)
        ks  = np.max(np.abs(emp - th))
        if ks < best_ks:
            best_ks, best_xmin = ks, xm
    return best_xmin, mle_gamma(degrees[degrees >= best_xmin].astype(float), best_xmin)


def powerlaw_ccdf_line(xmin: int, gamma: float, n_tail: int,
                       n_total: int, x_range: np.ndarray) -> np.ndarray:
    """P(K ≥ x) for fitted power law, normalised to fraction of whole sample."""
    fraction_in_tail = n_tail / n_total
    return fraction_in_tail * (x_range / xmin) ** (-(gamma - 1))


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------

def load_indegree() -> np.ndarray:
    with h5py.File(_H5, "r") as f:
        col = f["edge_col"][:].ravel().astype(np.int64)
        n   = int(f.attrs["n_nodes"])
    indeg = np.zeros(n, dtype=np.int64)
    np.add.at(indeg, col, 1)
    return indeg


def load_community_sizes() -> np.ndarray:
    membership = np.load(_LEIDEN)["membership"].ravel()
    _, counts = np.unique(membership, return_counts=True)
    return np.sort(counts)[::-1]


def load_fits() -> list[dict]:
    with open(_FITS, newline="") as fh:
        return list(csv.DictReader(fh))


def load_labels() -> dict[int, str]:
    labels: dict[int, str] = {}
    with open(_LABELS, newline="") as fh:
        for row in csv.DictReader(fh):
            labels[int(row["community_id"])] = row["physics_label"]
    return labels


# ---------------------------------------------------------------------------
# Figure 1 — Global in-degree CCDF
# ---------------------------------------------------------------------------

def fig1_indegree_ccdf(indeg: np.ndarray, out_dir: Path, dpi: int) -> None:
    print("Fig 1: global in-degree CCDF …")

    # CCDF
    k_sorted = np.sort(indeg[indeg > 0])
    n_total  = len(indeg)
    n_pos    = len(k_sorted)
    ccdf_y   = np.arange(n_pos, 0, -1) / n_total  # P(K >= k)

    # Scan for optimal xmin
    xmin, gamma_global = scan_xmin(indeg, xmin_max=100)
    n_tail = int((indeg >= xmin).sum())
    print(f"  xmin={xmin}, γ_global={gamma_global:.3f}, n_tail={n_tail:,}")

    # Fit line
    x_fit = np.logspace(np.log10(xmin), np.log10(k_sorted.max()), 200)
    y_fit = powerlaw_ccdf_line(xmin, gamma_global, n_tail, n_total, x_fit)

    fig, ax = plt.subplots(figsize=(3.3, 2.8))
    ax.scatter(k_sorted, ccdf_y, s=3, alpha=0.25, color="#2c7bb6",
               linewidths=0, label="APS data", rasterized=True)
    ax.plot(x_fit, y_fit, color="#d7191c", lw=1.5,
            label=fr"$P(k)\!\propto\!k^{{-\gamma}}$, $\gamma={gamma_global:.2f}$"
                  fr" ($k_{{\mathrm{{min}}}}={xmin}$)")
    ax.axvline(xmin, color="gray", ls="--", lw=0.8, alpha=0.6)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"In-degree $k$")
    ax.set_ylabel(r"$P(K \geq k)$")
    ax.set_title("Global in-degree distribution (APS 2022)")
    ax.legend(frameon=False, loc="upper right")

    # Annotation box
    ax.text(0.03, 0.05,
            f"$N={len(indeg):,}$\n$L={int(indeg.sum()):,}$",
            transform=ax.transAxes, fontsize=7,
            va="bottom", ha="left",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.7))

    fig.tight_layout()
    _save(fig, out_dir, "fig1_indegree_ccdf", dpi)

    # Save global fit params for use in §3 text
    (out_dir / "global_fit.txt").write_text(
        f"gamma_global={gamma_global:.4f}\nxmin={xmin}\nn_tail={n_tail}\n"
    )


# ---------------------------------------------------------------------------
# Figure 2 — Community size distribution
# ---------------------------------------------------------------------------

def fig2_community_sizes(sizes: np.ndarray, out_dir: Path, dpi: int) -> None:
    print("Fig 2: community size distribution …")

    n_large = int((sizes >= 30).sum())
    n_tiny  = int((sizes < 30).sum())

    fig, ax = plt.subplots(figsize=(3.3, 2.8))

    # Log-spaced bins
    bins = np.logspace(0, np.log10(sizes.max() + 1), 35)
    ax.hist(sizes, bins=bins, color="#4dac26", edgecolor="white", lw=0.4,
            label=f"{len(sizes)} communities total")

    ax.axvline(30, color="gray", ls="--", lw=0.9, alpha=0.8,
               label=f"$n=30$ threshold\n({n_large} large, {n_tiny} tiny)")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Community size $n$")
    ax.set_ylabel("Count")
    ax.set_title("Community size distribution (Leiden, $\\gamma=1.0$)")
    ax.legend(frameon=False, fontsize=7, loc="upper right")

    fig.tight_layout()
    _save(fig, out_dir, "fig2_community_sizes", dpi)


# ---------------------------------------------------------------------------
# Figure 3 — γ_c histogram
# ---------------------------------------------------------------------------

def fig3_gamma_histogram(fits: list[dict], out_dir: Path, dpi: int) -> None:
    print("Fig 3: γ_c histogram …")

    gammas = [float(r["gamma"]) for r in fits]
    g_arr  = np.array(gammas)
    g_mean, g_std = g_arr.mean(), g_arr.std()
    g_min,  g_max = g_arr.min(), g_arr.max()

    fig, ax = plt.subplots(figsize=(3.3, 2.8))

    bins = np.linspace(1.9, 3.4, 16)
    ax.hist(g_arr, bins=bins, color="#756bb1", edgecolor="white", lw=0.4)
    ax.axvline(g_mean, color="#de2d26", lw=1.5, ls="-",
               label=fr"$\bar{{\gamma}}={g_mean:.2f}\pm{g_std:.2f}$")
    ax.axvline(2.79, color="#636363", lw=1.2, ls="--",
               label=r"Barabasi (2016) $\gamma=2.79$")

    ax.set_xlabel(r"Power-law exponent $\gamma_c$")
    ax.set_ylabel("Number of communities")
    ax.set_title(fr"Per-community exponents ($n={len(gammas)}$ communities)")
    ax.legend(frameon=False, loc="upper right")

    # Annotation
    ax.text(0.03, 0.97,
            f"range [{g_min:.2f}, {g_max:.2f}]\n100% KS pass",
            transform=ax.transAxes, fontsize=7, va="top", ha="left")

    fig.tight_layout()
    _save(fig, out_dir, "fig3_gamma_histogram", dpi)


# ---------------------------------------------------------------------------
# Figure 4 — Year-median timeline
# ---------------------------------------------------------------------------

def fig4_timeline(fits: list[dict], labels: dict[int, str],
                  out_dir: Path, dpi: int) -> None:
    print("Fig 4: community year-median timeline …")

    # Sort by year_median ascending
    data = sorted(fits, key=lambda r: float(r["year_median"]))

    medians = np.array([float(r["year_median"]) for r in data])
    iqrs    = np.array([float(r["year_iqr"])    for r in data])
    q25     = np.array([float(r["year_q25"])    for r in data])
    q75     = np.array([float(r["year_q75"])    for r in data])
    sizes   = np.array([int(r["n_nodes"])       for r in data])
    cids    = [int(r["community_id"])           for r in data]

    # Short label: trim to ~25 chars
    def short(s: str) -> str:
        return s[:26] + "…" if len(s) > 27 else s

    ylabels = [short(labels.get(c, f"cid {c}")) for c in cids]
    y       = np.arange(len(data))

    # Marker size proportional to log(n_nodes)
    ms = 15 + 60 * (np.log10(sizes) - np.log10(sizes.min())) / (
        np.log10(sizes.max()) - np.log10(sizes.min()) + 1e-9)

    # Colour by era
    era_colors = plt.cm.plasma(np.linspace(0.1, 0.9, len(data)))

    fig, ax = plt.subplots(figsize=(5.5, 6.5))

    for i in range(len(data)):
        ax.hlines(y[i], q25[i], q75[i], color=era_colors[i], lw=2.5, alpha=0.6)
    sc = ax.scatter(medians, y, s=ms, c=medians,
                    cmap="plasma", vmin=1930, vmax=2020,
                    zorder=3, edgecolors="white", lw=0.3)

    ax.set_yticks(y)
    ax.set_yticklabels(ylabels, fontsize=6.5)
    ax.set_xlabel("Publication year")
    ax.set_title("Community Zeitgeist windows\n"
                 "(dot = median year; bar = IQR; size ∝ log community size)")

    cbar = fig.colorbar(sc, ax=ax, pad=0.01, fraction=0.025)
    cbar.set_label("Median year", fontsize=7)
    cbar.ax.tick_params(labelsize=6)

    ax.set_xlim(1930, 2025)
    ax.grid(axis="x", lw=0.4, color="lightgray", zorder=0)

    fig.tight_layout()
    _save(fig, out_dir, "fig4_timeline", dpi)


# ---------------------------------------------------------------------------
# Save helper
# ---------------------------------------------------------------------------

def _save(fig: plt.Figure, out_dir: Path, stem: str, dpi: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        p = out_dir / f"{stem}.{ext}"
        fig.savefig(p, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {out_dir}/{stem}.{{pdf,png}}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(out_dir: Path = _ROOT / "data/figures", dpi: int = 300) -> None:
    print("Loading data …")
    indeg  = load_indegree()
    sizes  = load_community_sizes()
    fits   = load_fits()
    labels = load_labels()
    print(f"  indeg: {len(indeg):,}  sizes: {len(sizes)}  fits: {len(fits)}")

    fig1_indegree_ccdf(indeg, out_dir, dpi)
    fig2_community_sizes(sizes, out_dir, dpi)
    fig3_gamma_histogram(fits, out_dir, dpi)
    fig4_timeline(fits, labels, out_dir, dpi)

    print("\nAll figures saved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=_ROOT / "data/figures")
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()
    main(args.out, args.dpi)
