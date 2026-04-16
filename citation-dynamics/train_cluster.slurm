#!/bin/bash
#SBATCH --job-name=aps-nst
#SBATCH --partition=gpunodes
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH --gres=gpu:1
#SBATCH -t 1-00:00
#SBATCH --mail-user=daveed@cs.toronto.edu
#SBATCH --mail-type=END,FAIL
#SBATCH --output=logs/train_%j.out
#SBATCH --error=logs/train_%j.err

cd /w/20251/daveed/citation-dynamics
mkdir -p logs

source /w/20251/daveed/torch_env/bin/activate
export HF_HOME=/w/20251/daveed/hf_cache
export TORCH_HOME=/w/20251/daveed/torch_cache

nvidia-smi

python src/phase3_nst_train.py \
    --num_epochs 500 \
    --batch_size 2000 \
    --max_edges 500000 \
    --display_epoch 50 \
    --space_dim 4 \
    --time_dim 4 \
    --J_encoder 3 \
    --J_snowflake 3 \
    --J_partialorder 3 \
    --lr 1e-4 \
    --max_grad_norm 0.1

echo "Done."
