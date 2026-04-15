import os
import sys

# Setup paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, "research", "src"))

import src.tox_data_engine

def run_pre_ingest():
    print("[*] Starting Pre-Deployment Ingestion...")
    # Initialize with relative paths for the container environment
    base_dir = ROOT_DIR
    data_dir = os.path.join(base_dir, "kg_data")
    cache_path = os.path.join(base_dir, "research", "data", "tox_feature_store.json")
    
    engine = src.tox_data_engine.ToxDataEngine(data_dir=data_dir, cache_path=cache_path)
    # Note: We don't use the monkey patch here because we want to use the actual engine
    # But wait, original engine has hardcoded paths. We MUST pass them.
    engine.ingest_all(force_refresh=True)
    print(f"[*] Pre-ingestion complete. Cache saved to {cache_path}")

if __name__ == "__main__":
    run_pre_ingest()
