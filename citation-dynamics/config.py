import os

# Project root
ROOT_DIR = os.getcwd()

# Data directories
DATA_RAW = os.path.join(ROOT_DIR, 'data', 'raw')          # optional full JSON
DATA_PROCESSED = os.path.join(ROOT_DIR, 'data', 'processed')  # canonical MAT/CSV
DATA_SAMPLE = os.path.join(ROOT_DIR, 'data', 'sample')    # small test datasets

# Experiments / outputs
EXPERIMENTS_DIR = os.path.join(ROOT_DIR, 'experiments')

# Convenience function to check paths
def check_paths():
    for p in [DATA_RAW, DATA_PROCESSED, DATA_SAMPLE, EXPERIMENTS_DIR]:
        if not os.path.exists(p):
            print(f'Warning: path does not exist: {p}')
        else:
            print(f'Found: {p}')

if __name__ == "__main__":
    check_paths()

    