"""phase2b_zeitgeist_fit.py — Per-community power-law fitting (Zeitgeist hypothesis).

Tests the Zeitgeist hypothesis: the global APS citation distribution is a mixture
of subcommunity distributions, each individually scale-free.

For each Leiden community:
  - Extract in-degree distribution
  - Fit discrete power law via MLE (Clauset et al. method)
  - KS goodness-of-fit test
  - Compute temporal spread (publication year IQR)

Outputs:
  data/analysis/zeitgeist_community_fits.csv   — per-community results
  data/analysis/zeitgeist_summary.txt          — printed summary
  data/analysis/zeitgeist_gamma_dist.npy       — gamma_c array for plotting

Usage:
    python src/phase2b_zeitgeist_fit.py
    python src/phase2b_zeitgeist_fit.py --min_nodes 50 --xmin_strategy scan
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import h5py
import numpy as np
from scipy import stats

_HERE = Path(__file__).parent
_ROOT = _HERE / ".."

_DEFAULT_H5     = _ROOT / "data/exported/aps-2022-citation-graph.h5"
_DEFAULT_LEIDEN = _ROOT / "data/exported/aps-2022-leiden-1p00.npz"
_OUT_DIR        = _ROOT / "data/analysis"


# ---------------------------------------------------------------------------
# Power-law MLE (Clauset et al. 2009, discrete case)
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


def ks_pvalue(degrees: np.ndarray, xmin: int, gamma: float, n_boot: int = 500) -> float:
    """KS p-value via bootstrap (Clauset et al. §4).

    Fraction of bootstrap samples with KS stat >= observed KS stat.
    Uses n_boot=500 for speed; increase for publication-quality.
    """
    tail = degrees[degrees >= xmin].astype(float)
    n = len(tail)
    if n < 10 or np.isnan(gamma):
        return float("nan")

    # Observed KS stat against fitted power-law CDF
    def powerlaw_cdf(k: np.ndarray, g: float, xm: int) -> np.ndarray:
        return 1.0 - (k / xm) ** (1.0 - g)

    k_unique = np.unique(tail)
    empirical_cdf = np.array([np.mean(tail <= k) for k in k_unique])
    theoretical_cdf = powerlaw_cdf(k_unique, gamma, xmin)
    ks_obs = np.max(np.abs(empirical_cdf - theoretical_cdf))

    # Bootstrap: draw synthetic samples from power-law, refit, compute KS
    rng = np.random.default_rng(42)
    count_exceed = 0
    for _ in range(n_boot):
        # Inverse CDF sampling for discrete power law (approximate)
        u = rng.uniform(size=n)
        synth = np.floor(xmin * (1.0 - u) ** (1.0 / (1.0 - gamma))).astype(float)
        synth = np.clip(synth, xmin, None)
        g_synth = mle_powerlaw_exponent(synth, xmin)
        if np.isnan(g_synth):
            continue
        k_s = np.unique(synth)
        emp_s = np.array([np.mean(synth <= k) for k in k_s])
        th_s  = powerlaw_cdf(k_s, g_synth, xmin)
        ks_s  = np.max(np.abs(emp_s - th_s))
        if ks_s >= ks_obs:
            count_exceed += 1

    return count_exceed / n_boot


def find_xmin(degrees: np.ndarray, xmin_strategy: str = "fixed", fixed_xmin: int = 1) -> int:
    """Choose xmin for power-law fit.

    'fixed': use fixed_xmin (default 1 — fit whole tail).
    'scan':  scan xmin in [1, 20] and pick value minimising KS stat.
             More principled but 20x slower.
    """
    if xmin_strategy == "fixed":
        return fixed_xmin

    best_xmin, best_ks = 1, np.inf
    for xm in range(1, 21):
        tail = degrees[degrees >= xm].astype(float)
        if len(tail) < 10:
            break
        g = mle_powerlaw_exponent(tail, xm)
        if np.isnan(g):
            continue
        # KS between empirical and theoretical
        k_u = np.unique(tail)
        emp = np.array([np.mean(tail <= k) for k in k_u])
        th  = 1.0 - (k_u / xm) ** (1.0 - g)
        ks  = np.max(np.abs(emp - th))
        if ks < best_ks:
            best_ks, best_xmin = ks, xm
    return best_xmin


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def run(
    h5_path:      Path,
    leiden_path:  Path,
    out_dir:      Path,
    min_nodes:    int  = 30,
    xmin_strategy: str = "fixed",
    ks_boots:     int  = 200,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load graph
    print(f"Loading HDF5: {h5_path}")
    with h5py.File(h5_path, "r") as f:
        edge_col = f["edge_col"][:].ravel().astype(np.int32)
        year     = f["year"][:].ravel().astype(np.float32)
    N = len(year)
    in_degree = np.bincount(edge_col, minlength=N).astype(np.int32)
    print(f"  N={N:,}, max_indegree={in_degree.max()}")

    # Load Leiden membership
    print(f"Loading Leiden: {leiden_path}")
    d = np.load(leiden_path)
    membership    = d["membership"].astype(np.int32)
    n_communities = int(membership.max()) + 1
    print(f"  Communities: {n_communities}")

    # Per-community fitting
    rows = []
    gamma_list = []

    print(f"\nFitting power law per community (min_nodes={min_nodes}, xmin={xmin_strategy}) ...")
    for cid in range(n_communities):
        mask = membership == cid
        n    = mask.sum()
        if n < min_nodes:
            continue

        deg_c  = in_degree[mask]
        year_c = year[mask]
        year_c = year_c[year_c > 0]  # exclude missing years

        xmin  = find_xmin(deg_c, xmin_strategy)
        gamma = mle_powerlaw_exponent(deg_c, xmin)
        pval  = ks_pvalue(deg_c, xmin, gamma, n_boot=ks_boots)

        year_q25 = float(np.percentile(year_c, 25)) if len(year_c) else float("nan")
        year_q75 = float(np.percentile(year_c, 75)) if len(year_c) else float("nan")
        year_med = float(np.median(year_c)) if len(year_c) else float("nan")
        year_iqr = year_q75 - year_q25

        rows.append({
            "community_id": cid,
            "n_nodes":      n,
            "n_tail":       int((deg_c >= xmin).sum()),
            "xmin":         xmin,
            "gamma":        round(gamma, 4) if not np.isnan(gamma) else "nan",
            "ks_pvalue":    round(pval,  4) if not np.isnan(pval)  else "nan",
            "year_q25":     round(year_q25, 1),
            "year_q75":     round(year_q75, 1),
            "year_median":  round(year_med, 1),
            "year_iqr":     round(year_iqr, 1),
        })

        if not np.isnan(gamma):
            gamma_list.append(gamma)

        if (cid + 1) % 50 == 0:
            print(f"  ... {cid+1}/{n_communities} communities processed")

    print(f"  Fitted {len(rows)} communities with >= {min_nodes} nodes")

    # Save CSV
    csv_path = out_dir / "zeitgeist_community_fits.csv"
    fieldnames = list(rows[0].keys())
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\nSaved: {csv_path}")

    # Save gamma array
    gamma_arr = np.array(gamma_list, dtype=np.float32)
    np.save(out_dir / "zeitgeist_gamma_dist.npy", gamma_arr)

    # Summary
    valid_gamma = [float(r["gamma"]) for r in rows if r["gamma"] != "nan"]
    valid_pval  = [float(r["ks_pvalue"]) for r in rows if r["ks_pvalue"] != "nan"]
    n_plausible = sum(1 for p in valid_pval if p >= 0.05)

    summary_lines = [
        "=" * 60,
        "ZEITGEIST HYPOTHESIS — SUMMARY",
        "=" * 60,
        f"Communities analysed (n >= {min_nodes}): {len(rows)}",
        f"  Valid gamma fits:     {len(valid_gamma)}",
        f"  KS p >= 0.05 (power-law plausible): {n_plausible} / {len(valid_pval)} "
        f"({100*n_plausible/max(len(valid_pval),1):.1f}%)",
        "",
        "Gamma distribution across communities:",
        f"  mean  = {np.mean(valid_gamma):.3f}",
        f"  std   = {np.std(valid_gamma):.3f}",
        f"  median= {np.median(valid_gamma):.3f}",
        f"  min   = {np.min(valid_gamma):.3f}",
        f"  max   = {np.max(valid_gamma):.3f}",
        f"  [1,4] range: {sum(1 < g < 4 for g in valid_gamma)} / {len(valid_gamma)}",
        "",
        "Temporal spread (year IQR across communities):",
    ]
    year_iqrs = [float(r["year_iqr"]) for r in rows if not np.isnan(float(r["year_iqr"]))]
    summary_lines += [
        f"  mean IQR  = {np.mean(year_iqrs):.1f} years",
        f"  median IQR= {np.median(year_iqrs):.1f} years",
        f"  Temporally tight (IQR < 20y): "
        f"{sum(x < 20 for x in year_iqrs)} / {len(year_iqrs)} "
        f"({100*sum(x < 20 for x in year_iqrs)/max(len(year_iqrs),1):.1f}%)",
        "=" * 60,
    ]

    summary = "\n".join(summary_lines)
    print("\n" + summary)

    summary_path = out_dir / "zeitgeist_summary.txt"
    summary_path.write_text(summary)
    print(f"Saved: {summary_path}")

    # Global fit for comparison
    print("\nGlobal in-degree power-law fit (for comparison):")
    gamma_global = mle_powerlaw_exponent(in_degree, xmin=1)
    print(f"  gamma_global = {gamma_global:.4f}")
    print("  (Compare to per-community mean — if they differ, mixture structure is real)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Per-community power-law fitting")
    parser.add_argument("--h5",      default=str(_DEFAULT_H5))
    parser.add_argument("--leiden",  default=str(_DEFAULT_LEIDEN))
    parser.add_argument("--out",     default=str(_OUT_DIR))
    parser.add_argument("--min_nodes", type=int, default=30,
                        help="Minimum community size to fit (default 30)")
    parser.add_argument("--xmin_strategy", choices=["fixed", "scan"], default="fixed",
                        help="xmin selection: 'fixed' (fast) or 'scan' (principled, slower)")
    parser.add_argument("--ks_boots", type=int, default=200,
                        help="Bootstrap samples for KS p-value (default 200; use 500+ for paper)")
    args = parser.parse_args()

    run(
        h5_path       = Path(args.h5),
        leiden_path   = Path(args.leiden),
        out_dir       = Path(args.out),
        min_nodes     = args.min_nodes,
        xmin_strategy = args.xmin_strategy,
        ks_boots      = args.ks_boots,
    )


if __name__ == "__main__":
    main()
