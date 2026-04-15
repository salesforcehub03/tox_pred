import os
import pandas as pd
import numpy as np
import json
import re
import logging
from typing import Dict, Any, Optional, List, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ToxDataEngine")

class ToxDataEngine:
    """
    Advanced ETL and Feature Engineering engine for Toxicological Data.
    Ingests drug-specific clinical and preclinical Excel files into a structured feature matrix.
    """
    
    def __init__(self, data_dir: str = r"D:\AViiD\Tox_pred\kg_data", cache_path: str = r"D:\AViiD\research\data\tox_feature_store.json"):
        self.data_dir = data_dir
        self.cache_path = cache_path
        self.feature_store: Dict[str, Dict[str, Any]] = {}  # {drug_name: {features: [], targets: []}}
        
        # MedDRA-aligned families for binary text parsing (from toxicity_predictor.py reference)
        self.ae_families = {
            "hepat": ["liver", "hepat", "jaundice", "transaminase", "alt", "ast", "bilirubin", "cholestasis", "dili"],
            "renal": ["kidney", "renal", "nephro", "creatinine", "proteinuria", "oliguria", "anuria"],
            "cardiac": ["cardiac", "heart", "qt", "qrs", "arrhythm", "torsade", "myocardial"],
            "pulmonary": ["lung", "pulmonary", "pneumon", "dyspnoea", "respiratory", "bronch", "fibrosis"],
            "neuro": ["neuro", "seizure", "convulsion", "neuropathy", "tremor", "ataxia", "dizziness"],
            "hemato": ["anaemia", "thrombocytopenia", "neutropenia", "agranulocytosis"],
            "immune": ["hypersensitivity", "anaphyla", "stevens-johnson", "dermatitis", "rash"]
        }

    def _extract_numeric(self, val: Any) -> float:
        """Regex utility to extract the first float from a messy string (e.g. 'CL~43.9 L/h' -> 43.9)."""
        if pd.isna(val) or val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        
        # Regex to find numbers including decimals
        match = re.search(r"([-+]?\d*\.\d+|\d+)", str(val))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        return 0.0

    def _parse_text_signals(self, text: str) -> Dict[str, int]:
        """Parses free text into binary flags based on semantic families."""
        if pd.isna(text) or text is None:
            return {fam: 0 for fam in self.ae_families}
        
        text_lower = str(text).lower()
        flags = {}
        for fam, keywords in self.ae_families.items():
            flags[fam] = 1 if any(kw in text_lower for kw in keywords) else 0
        return flags

    def ingest_all(self, force_refresh: bool = False):
        """Orchestrates the ingestion of the 3 specified files."""
        if not force_refresh and os.path.exists(self.cache_path):
            with open(self.cache_path, "r") as f:
                self.feature_store = json.load(f)
            logger.info(f"Loaded {len(self.feature_store)} drug profiles from cache.")
            return

        # 1. Process Clinical Data (15 drugs, 16 sheets)
        clinical_path = os.path.join(self.data_dir, "clinical_data.xlsx")
        if os.path.exists(clinical_path):
            logger.info("Ingesting clinical_data.xlsx...")
            all_sheets = pd.read_excel(clinical_path, sheet_name=None, engine='openpyxl')
            for sheet_name, df in all_sheets.items():
                self._process_clinical_sheet(df, sheet_name)

        # 2. Process Preclinical Data (15 drugs, one sheet each)
        preclinical_path = os.path.join(self.data_dir, "preclinical_data.xlsx")
        if os.path.exists(preclinical_path):
            logger.info("Ingesting preclinical_data.xlsx...")
            all_sheets = pd.read_excel(preclinical_path, sheet_name=None, engine='openpyxl')
            for sheet_name, df in all_sheets.items():
                self._process_preclinical_sheet(df, sheet_name)

        # 3. Process Belinostat Deep Profile (8 sheets)
        belino_path = os.path.join(self.data_dir, "Belinostat_extracted_data.xlsx")
        if os.path.exists(belino_path):
            logger.info("Ingesting Belinostat_extracted_data.xlsx...")
            self._process_belinostat(belino_path)

        # 4. Save Cache
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, "w") as f:
            json.dump(self.feature_store, f, indent=4)
        logger.info(f"Ingestion complete. Saved {len(self.feature_store)} profiles.")

    def _process_clinical_sheet(self, df: pd.DataFrame, sheet_name: str):
        """Parses clinical drug sheets."""
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        # Clinical targets: Drug name, Sex, Dose, Cmax, AUC, t1/2, Clearance, ALT, AST, FAERS_Adverse_Events, Severity, Latency, Population
        for _, row in df.iterrows():
            drug_name = str(row.get('drug name', row.get('name', sheet_name))).strip()
            if not drug_name or drug_name.lower() == 'nan': continue
            
            if drug_name not in self.feature_store:
                self.feature_store[drug_name] = {"observations": []}
            
            obs = {
                "type": "clinical",
                "sex": str(row.get('sex', 'Unknown')),
                "dose": self._extract_numeric(row.get('dose')),
                "cmax": self._extract_numeric(row.get('cmax')),
                "auc": self._extract_numeric(row.get('auc')),
                "t_half": self._extract_numeric(row.get('t½', row.get('t1/2'))),
                "clearance": self._extract_numeric(row.get('clearance')),
                "alt": self._extract_numeric(row.get('alt')),
                "ast": self._extract_numeric(row.get('ast')),
                "population": str(row.get('population type', 'Healthy')),
                "severity": str(row.get('severity', 'Mild')),
                "latency": str(row.get('latency', 'Acute')),
                "ae_flags": self._parse_text_signals(row.get('faers adverse events', ''))
            }
            self.feature_store[drug_name]["observations"].append(obs)

    def _process_preclinical_sheet(self, df: pd.DataFrame, sheet_name: str):
        """Parses preclinical drug sheets."""
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        for _, row in df.iterrows():
            drug_name = str(row.get('drug', sheet_name)).strip()
            if drug_name not in self.feature_store:
                self.feature_store[drug_name] = {"observations": []}
            
            obs = {
                "type": "preclinical",
                "species": str(row.get('species', 'Unknown')),
                "dose": self._extract_numeric(row.get('dose')),
                "noael": self._extract_numeric(row.get('noael')),
                "loael": self._extract_numeric(row.get('loael')),
                "cmax": self._extract_numeric(row.get('cmax')),
                "auc": self._extract_numeric(row.get('auc')),
                "clinical_signs": self._parse_text_signals(row.get('clinical signs', ''))
            }
            self.feature_store[drug_name]["observations"].append(obs)

    def _process_belinostat(self, path: str):
        """Specialized parser for the 8-sheet Belinostat workbook."""
        xl = pd.ExcelFile(path, engine='openpyxl')
        drug_name = "Belinostat"
        if drug_name not in self.feature_store:
            self.feature_store[drug_name] = {"observations": []}
        
        # Sheet 5: PK Matrix
        if "PK Matrix" in xl.sheet_names:
            df_pk = xl.parse("PK Matrix")
            # Logic to extract species-specific overrides
            self.feature_store[drug_name]["pk_matrix"] = df_pk.to_dict(orient='records')
            
        # Sheet 8: AE Matrix (Grade 3/4)
        if "AE Matrix" in xl.sheet_names or any("AE" in s for s in xl.sheet_names):
            # Assume last sheet or specific named sheet
            sheet_ae = [s for s in xl.sheet_names if "AE" in s][-1]
            df_ae = xl.parse(sheet_ae)
            self.feature_store[drug_name]["grade_3_4_flags"] = df_ae.to_dict(orient='records')

    def get_feature_vector(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Constructs the 14-parameter POC feature vector for a drug.
        Prioritizes Clinical over Preclinical matches.
        """
        # Case-insensitive lookup
        match = None
        for drug in self.feature_store:
            if drug.lower() == query.lower():
                match = self.feature_store[drug]
                break
        
        if not match: return None
        
        # Aggregate logic for a 'Standard' vector
        clinical_obs = [o for o in match["observations"] if o["type"] == "clinical"]
        preclinical_obs = [o for o in match["observations"] if o["type"] == "preclinical"]
        
        # Start with default placeholders
        vec = {
            "dose_mg": 0.0, "cmax_ng_ml": 0.0, "auc_ng_h_ml": 0.0, "t_half_h": 0.0,
            "clearance": 0.0, "alt_u_l": 0.0, "ast_u_l": 0.0, "sex": "Unknown",
            "population": "Healthy", "noael": 0.0, "loael": 0.0, 
            "preclinical_ae_flags": {}, "ae_targets": {}
        }
        
        if clinical_obs:
            # Take the first clinical observation as the base
            o = clinical_obs[0]
            vec.update({
                "dose_mg": o["dose"], "cmax_ng_ml": o["cmax"], "auc_ng_h_ml": o["auc"],
                "t_half_h": o["t_half"], "clearance": o["clearance"],
                "alt_u_l": o["alt"], "ast_u_l": o["ast"],
                "sex": o["sex"], "population": o["population"], "ae_targets": o["ae_flags"]
            })
            
        if preclinical_obs:
            o = preclinical_obs[0]
            vec.update({
                "noael": o["noael"], "loael": o["loael"], "preclinical_ae_flags": o["clinical_signs"]
            })
            # If clinical data was missing PK, fill from preclinical (scaled)
            if vec["cmax_ng_ml"] == 0: vec["cmax_ng_ml"] = o["cmax"]
            if vec["auc_ng_h_ml"] == 0: vec["auc_ng_h_ml"] = o["auc"]

        return vec

if __name__ == "__main__":
    engine = ToxDataEngine()
    engine.ingest_all(force_refresh=True)
    f_vec = engine.get_feature_vector("Belinostat")
    print(f"Belinostat POC Vector: {json.dumps(f_vec, indent=4) if f_vec else 'Not Found'}")
