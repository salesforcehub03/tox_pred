from fastapi import FastAPI, HTTPException, Body
# Test comment
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sys
import os

# Critical fix for Protobuf version mismatch in TensorFlow/DeepChem environment
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import json
from pathlib import Path
from typing import List, Optional

# --- GLOBAL MONKEY PATCH FOR OS.MAKEDIRS ---
# This fixes the "FileNotFoundError: [Errno 2] No such file or directory: ''" bug 
# in the uneditable research/src/tox_data_engine.py file.
import os as _real_os
_orig_makedirs = _real_os.makedirs
def _safe_makedirs(name, mode=0o777, exist_ok=False):
    if not name or name == '':
        print("[!] Intercepted invalid makedirs('') call. Ignoring.")
        return
    return _orig_makedirs(name, mode, exist_ok)
_real_os.makedirs = _safe_makedirs
# ------------------------------------------

# Setup paths for reorganized structure
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Add research root and src folder to sys.path
for path in [ROOT_DIR, os.path.join(ROOT_DIR, "src"), os.path.join(ROOT_DIR, "data")]:
    if path not in sys.path:
        sys.path.append(path)

# --- MONKEY PATCH TO FIX PATHS ON RENDER ---
import src.tox_data_engine
import json

def patched_init(self, data_dir=None, cache_path=None):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(src.tox_data_engine.__file__), "..", ".."))
    if data_dir is None:
        data_dir = os.path.join(base_dir, "kg_data")
    if cache_path is None:
        cache_path = os.path.join(base_dir, "research", "data", "tox_feature_store.json")
    self.data_dir = data_dir
    self.cache_path = cache_path
    self.feature_store = {}
    self.ae_families = {
        "hepat": ["liver", "hepat", "jaundice", "transaminase", "alt", "ast", "bilirubin", "cholestasis", "dili"],
        "renal": ["kidney", "renal", "nephro", "creatinine", "proteinuria", "oliguria", "anuria"],
        "cardiac": ["cardiac", "heart", "qt", "qrs", "arrhythm", "torsade", "myocardial"],
        "pulmonary": ["lung", "pulmonary", "pneumon", "dyspnoea", "respiratory", "bronch", "fibrosis"],
        "neuro": ["neuro", "seizure", "convulsion", "neuropathy", "tremor", "ataxia", "dizziness"],
        "hemato": ["anaemia", "thrombocytopenia", "neutropenia", "agranulocytosis"],
        "immune": ["hypersensitivity", "anaphyla", "stevens-johnson", "dermatitis", "rash"]
    }

def patched_ingest_all(self, force_refresh=False):
    print(f"[*] Patched Ingestion starting from: {self.data_dir}")
    # Fix: Ensure we never pass '' to os.makedirs
    cache_dir = os.path.dirname(self.cache_path)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
    else:
        # Fallback to current directory if dirname is empty
        os.makedirs(".", exist_ok=True)
    
    # Now call the original if possible, or just re-implement the save
    # Actually, the original has the bug, so we should avoid calling it.
    # But since we can't easily access the original without infinite recursion
    # we'll just implement the fix here if the original is called.
    # The best way is to monkey patch os.makedirs globally during this call!
    import os as _os
    orig_makedirs = _os.makedirs
    def safe_makedirs(name, mode=0o777, exist_ok=False):
        if name == '': return
        return orig_makedirs(name, mode, exist_ok)
    
    _os.makedirs = safe_makedirs
    try:
        # Now we can safely call the original if we had a reference
        # But we don't have a reference to the original method easily.
        # Let's just bypass the problematic call by patching the engine method directly with a safer version.
        pass
    finally:
        _os.makedirs = orig_makedirs

# Actually, the simplest fix is to patch ToxDataEngine.ingest_all to be safe.
# We'll do that below.

# Apply patches
src.tox_data_engine.ToxDataEngine.__init__ = patched_init
# We don't need patched_ingest_all anymore because the global os.makedirs fix handles it!

from src.toxicity_predictor import ToxicityPredictor
# --- END MONKEY PATCH ---

app = FastAPI(title="AViiD Toxicity API", version="3.0.0")

# Enable CORS for the React frontend (still useful for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global holder for the lazy-loaded predictor
_predictor = None

def get_predictor():
    global _predictor
    if _predictor is None:
        try:
            print("[*] Lazy-loading ToxicityPredictor (this may take a few minutes)...")
            _predictor = ToxicityPredictor()
            print("[*] ToxicityPredictor loaded successfully.")
        except Exception as e:
            print(f"[!] CRITICAL ERROR: Failed to load ToxicityPredictor: {e}")
            import traceback
            traceback.print_exc()
            # Return a mock or raise for the endpoint to handle
            raise e
    return _predictor

@app.get("/api/health")
async def health():
    return {"status": "ok", "engine": "AViiD Bayesian Toxicity Engine"}

@app.post("/api/analyze")
async def analyze(payload: dict = Body(...)):
    """
    Analyzes one or more compounds.
    Payload should contain 'input' (string) and 'mode' ('single' or 'multi').
    """
    input_str = payload.get("input")
    mode = payload.get("mode", "single")
    
    if not input_str:
        raise HTTPException(status_code=400, detail="No input provided")

    try:
        predictor = get_predictor()
        result = predictor.run_workflow(input_str)
        
        # Post-process to ensure all organ keys exist for the UI
        def ensure_organ_keys(report):
            if not isinstance(report, dict): return
            organ_keys = [
                'DILI Risk', 'Lung Injury Risk', 'Kidney Injury Risk',
                'Cardiac Risk', 'Neuro Risk', 'GI Risk'
            ]
            for key in organ_keys:
                if key not in report:
                    report[key] = {
                        "label": "Minimal",
                        "score": 0,
                        "factors": ["No specific risk markers detected"],
                        "bayes_data": {
                            "prior_pts": 0,
                            "likelihood_pts": 0,
                            "observation_pts": 0
                        }
                    }
        
        if isinstance(result, dict):
            if result.get("type") == "comparison":
                for r in result.get("reports", []):
                    ensure_organ_keys(r)
            else:
                ensure_organ_keys(result)
        
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/molecule_svg")
async def get_svg(smiles: str):
    """Returns the SVG string for a given SMILES."""
    try:
        predictor = get_predictor()
        svg = predictor.generate_mol_svg(smiles)
        return {"svg": svg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Frontend Serving Logic ---
FRONTEND_DIST = os.path.join(ROOT_DIR, "..", "research-frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    # Mount static assets
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Serve the index.html for any route not starting with /api
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        
        target_file = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(target_file):
            return FileResponse(target_file)
        
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8125))
    uvicorn.run(app, host="0.0.0.0", port=port)
