from fastapi import FastAPI, HTTPException, Body
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

# Setup paths for reorganized structure
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Add research root and src folder to sys.path
for path in [ROOT_DIR, os.path.join(ROOT_DIR, "src"), os.path.join(ROOT_DIR, "data")]:
    if path not in sys.path:
        sys.path.append(path)

from src.toxicity_predictor import ToxicityPredictor

app = FastAPI(title="AViiD Toxicity API", version="3.0.0")

# Enable CORS for the React frontend (still useful for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Toxicity Predictor once
predictor = ToxicityPredictor()

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
