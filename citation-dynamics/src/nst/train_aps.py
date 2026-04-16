"""train_aps.py — Train Neural Spacetime on the APS citation graph.

Mirrors deps/nst/arxiv_embedding/train_real.py but uses the APS adapter
and a smaller model suitable for CPU training (no GPU on this machine).

Model configuration (defaults):
    feature_dim = 4    (engineered structural features)
    space_dim   = 4    (spatial embedding dimension)
    time_dim    = 4    (temporal partial-order dimension)
    J_encoder   = 6    (encoder depth, reduced from 10)
    J_snowflake = 3
    J_partialorder = 3

Outputs:
    data/exported/aps-nst-model.pt          — trained model weights
    data/exported/aps-nst-embeddings.npy    — [N, space_dim+time_dim] node embeddings
    data/exported/aps-nst-embeddings-meta.npz — doi, year, membership arrays for plotting

Usage:
    python src/nst/train_aps.py
    python src/nst/train_aps.py --num_epochs 200 --batch_size 2000 --max_edges 200000
    python src/nst/train_aps.py --num_epochs 2000 --max_edges 500000  # full run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn.utils import clip_grad_norm_
from torch.utils.data import DataLoader, TensorDataset

# Wire up NST module path (deps/nst/arxiv_embedding/)
_HERE  = Path(__file__).parent
_ROOT  = _HERE / "../.."
_NST   = _ROOT / "deps/nst/arxiv_embedding"
sys.path.insert(0, str(_NST))

from neural_spacetime import NeuralSpacetime  # noqa: E402  (path added above)

from aps_adapter import FEATURE_DIM, load_aps_data  # noqa: E402


# ---------------------------------------------------------------------------
# Training loop (adapted from real_train_functions.py)
# ---------------------------------------------------------------------------

def _criterion_time(x_u: torch.Tensor, x_v: torch.Tensor) -> tuple[torch.Tensor, float]:
    """Temporal partial-order loss: penalise edge u→v where time[u] >= time[v]."""
    sigmoid = torch.nn.Sigmoid()
    diff = x_u - x_v
    sigmoid_diff_sum = torch.mean(sigmoid(10 * diff), dim=-1)
    loss = torch.mean(sigmoid_diff_sum)

    relu = torch.nn.ReLU()
    relu_diff_sum = torch.sum(relu(diff), dim=-1)
    total_correct = (relu_diff_sum == 0).sum().item() / relu_diff_sum.shape[0]
    loss = loss * (1 - total_correct)

    return loss, total_correct


def train(
    data_x: torch.Tensor,
    data_y: torch.Tensor,
    feature_dim:   int   = FEATURE_DIM,
    space_dim:     int   = 4,
    time_dim:      int   = 4,
    batch_size:    int   = 2000,
    num_epochs:    int   = 500,
    lr:            float = 1e-4,
    weight_decay:  float = 1e-4,
    max_grad_norm: float = 1.0,
    display_epoch: int   = 50,
    device: torch.device = torch.device("cpu"),
) -> nn.Module:
    """Train NeuralSpacetime and return the trained model.

    data_x layout: [feat_v (cited/older) || feat_u (citing/newer)] per edge u→v.
    Model is called as model(feat_v, feat_u) so that po_x tracks the OLDER (cited)
    node and po_y tracks the NEWER (citing) node — matching the OGBN-Arxiv convention
    in real_train_functions.py. The time criterion then correctly scores orderings where
    time[older] < time[newer].
    """
    model = NeuralSpacetime(
        N  = feature_dim,
        D  = space_dim,
        T  = time_dim,
        J_encoder       = 6,
        J_snowflake     = 3,
        J_partialorder  = 3,
    ).to(device)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"NeuralSpacetime: {n_params:,} trainable parameters")

    criterion_space = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    loader = DataLoader(
        TensorDataset(data_x, data_y),
        batch_size=batch_size,
        shuffle=True,
    )

    for epoch in range(1, num_epochs + 1):
        running_loss = running_space = running_time = 0.0
        distortions: list[torch.Tensor] = []
        correct = 0.0

        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()

            # data_x = [feat_v (cited/older) || feat_u (citing/newer)]
            # Call model(feat_v, feat_u) so po_x = time[cited], po_y = time[citing].
            # diff = time[cited] - time[citing] < 0 for correct ordering → matches
            # the OGBN-Arxiv convention in the upstream real_train_functions.py.
            distance, po_x, po_y = model(inputs[:, :feature_dim], inputs[:, feature_dim:])
            distance = distance.squeeze(1)

            connected = labels != 0
            if connected.sum() == 0:
                continue

            loss_space = criterion_space(distance[connected], labels[connected])
            loss_time, correct = _criterion_time(po_x[connected], po_y[connected])
            loss = loss_space + loss_time

            loss.backward()
            clip_grad_norm_(model.parameters(), max_grad_norm)
            optimizer.step()

            running_loss  += loss.item()
            running_space += loss_space.item()
            running_time  += loss_time.item()
            distortions.append((labels[connected] / distance[connected].clamp(min=1e-8)).detach())

        n_batches = max(len(loader), 1)
        avg_loss  = running_loss  / n_batches
        avg_space = running_space / n_batches
        avg_time  = running_time  / n_batches

        if epoch % display_epoch == 0:
            if distortions:
                dist_all = torch.cat(distortions)
                dist_str = f"distortion avg={dist_all.mean():.3f} std={dist_all.std():.3f}"
            else:
                dist_str = "distortion avg=nan std=nan"
            print(
                f"Epoch {epoch:4d} | loss {avg_loss:.4f} "
                f"(space {avg_space:.4f}, time {avg_time:.4f}) | "
                f"{dist_str} | order_correct={correct:.3f}"
            )

        # Early exit on NaN — indicates gradient explosion; reduce lr and retry
        if not torch.isfinite(torch.tensor(avg_loss)):
            print(
                f"\nERROR: NaN/Inf loss detected at epoch {epoch}. "
                "Training diverged. Try: lower --lr (current default 1e-4), "
                "tighter --max_grad_norm, or fewer encoder layers (J_encoder)."
            )
            break

    return model


# ---------------------------------------------------------------------------
# Embedding export
# ---------------------------------------------------------------------------

@torch.no_grad()
def export_embeddings(
    model:         nn.Module,
    node_features: np.ndarray,
    h5_path:       Path,
    leiden_path:   Path,
    out_dir:       Path,
    device:        torch.device = torch.device("cpu"),
    batch_size:    int          = 4096,
) -> None:
    """Run all nodes through the encoder and save embeddings.

    Saves:
        aps-nst-embeddings.npy          float32[N, D+T]
        aps-nst-embeddings-meta.npz     doi, year, membership arrays
    """
    model.eval()
    N = node_features.shape[0]
    D_T = model.D + model.T

    feat_t = torch.from_numpy(node_features).to(device)
    emb    = torch.zeros(N, D_T, dtype=torch.float32)

    for start in range(0, N, batch_size):
        end = min(start + batch_size, N)
        enc = model.encoder(feat_t[start:end])
        emb[start:end] = enc.cpu()

    emb_np = emb.numpy()
    emb_path = out_dir / "aps-nst-embeddings.npy"
    np.save(emb_path, emb_np)
    print(f"Saved embeddings: {emb_path}  shape={emb_np.shape}")

    # Save metadata for plotting
    with h5py.File(h5_path, "r") as f:  # h5py imported at top of module
        doi  = f["doi"][:]
        year = f["year"][:].ravel()
    d = np.load(leiden_path)
    membership = d["membership"]
    meta_path = out_dir / "aps-nst-embeddings-meta.npz"
    np.savez_compressed(meta_path, doi=doi, year=year, membership=membership)
    print(f"Saved metadata:   {meta_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Train NST on APS citation graph")
    parser.add_argument("--h5",          default=str(_ROOT / "data/exported/aps-2022-citation-graph.h5"))
    parser.add_argument("--leiden",      default=str(_ROOT / "data/exported/aps-2022-leiden-1p00.npz"))
    parser.add_argument("--out",         default=str(_ROOT / "data/exported"))
    parser.add_argument("--max_edges",   type=int,   default=500_000)
    parser.add_argument("--batch_size",  type=int,   default=2000)
    parser.add_argument("--num_epochs",  type=int,   default=500)
    parser.add_argument("--space_dim",   type=int,   default=4)
    parser.add_argument("--time_dim",    type=int,   default=4)
    parser.add_argument("--display_epoch", type=int, default=50)
    parser.add_argument("--seed",        type=int,   default=42)
    parser.add_argument("--lr",          type=float, default=1e-4,
                        help="AdamW learning rate (default 1e-4; original NST uses 1e-4)")
    parser.add_argument("--weight_decay", type=float, default=1e-4)
    parser.add_argument("--max_grad_norm", type=float, default=1.0)
    parser.add_argument("--force_rebuild", action="store_true")
    args = parser.parse_args()

    device = torch.device("cpu")
    print(f"Device: {device}")

    h5_path     = Path(args.h5)
    leiden_path = Path(args.leiden)
    out_dir     = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    data_x, data_y, node_features = load_aps_data(
        h5_path     = h5_path,
        leiden_path = leiden_path,
        max_edges   = args.max_edges,
        seed        = args.seed,
        force_rebuild = args.force_rebuild,
    )
    print(f"Training on {data_x.shape[0]:,} edges, feature_dim={FEATURE_DIM}")

    # Train
    model = train(
        data_x,
        data_y,
        feature_dim   = FEATURE_DIM,
        space_dim     = args.space_dim,
        time_dim      = args.time_dim,
        batch_size    = args.batch_size,
        num_epochs    = args.num_epochs,
        lr            = args.lr,
        weight_decay  = args.weight_decay,
        max_grad_norm = args.max_grad_norm,
        display_epoch = args.display_epoch,
        device        = device,
    )

    # Save model
    model_path = out_dir / "aps-nst-model.pt"
    torch.save(model.state_dict(), model_path)
    print(f"Saved model: {model_path}")

    # Export embeddings
    export_embeddings(model, node_features, h5_path, leiden_path, out_dir, device)


if __name__ == "__main__":
    main()
