"""
Toxicity Prediction Engine — Ground-Truth Validation Harness
=============================================================
Runs each drug from ground_truth_db through the ToxicityPredictor,
compares predictions against published pharmacovigilance data,
and generates an accuracy scorecard.

Usage:
    python validate_engine.py              # Run all 17 drugs
    python validate_engine.py belinostat   # Run single drug
"""

import sys
import os
import json
import time
from datetime import datetime

# Setup paths
# Since we are in /tests, we need to add /src and /data to the path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(ROOT_DIR, "src"))
sys.path.append(os.path.join(ROOT_DIR, "data"))

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from ground_truth_db import GROUND_TRUTH, get_all_drugs
from toxicity_predictor import ToxicityPredictor

# =============================================================================
# RISK LEVEL ORDINAL MAPPING (for distance metrics)
# =============================================================================
RISK_LEVELS = {"none": 0, "low": 1, "moderate": 2, "high": 3}
ORGAN_MAP = {
    "liver": "DILI Risk",
    "lung": "Lung Injury Risk",
    "kidney": "Kidney Injury Risk",
    "heart": "Cardiac Risk",
    "brain": "Neuro Risk",
}


def risk_to_ordinal(level: str) -> int:
    """Convert risk string to numeric ordinal."""
    return RISK_LEVELS.get(level.strip().lower(), 0)


def ordinal_to_risk(val: int) -> str:
    for k, v in RISK_LEVELS.items():
        if v == val:
            return k.capitalize()
    return "None"


# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def score_organ_risk(predicted_risk: dict, expected_risk: dict) -> dict:
    """
    Compare predicted organ risk levels against ground truth.
    Returns per-organ results and aggregate accuracy.
    
    Scoring:
      - Exact match          = 1.0
      - Off by 1 level       = 0.5  (e.g., predicted Moderate, expected High)
      - Off by 2+ levels     = 0.0
    """
    results = {}
    total_score = 0
    total_count = 0
    
    for organ, expected_key in ORGAN_MAP.items():
        expected_level = expected_risk.get(organ, "none").strip().lower()
        
        pred_data = predicted_risk.get(expected_key, {})
        predicted_level = pred_data.get("label", "Low").strip().lower() if pred_data else "low"
        predicted_pct = pred_data.get("score", 0) if pred_data else 0
        
        expected_ord = risk_to_ordinal(expected_level)
        predicted_ord = risk_to_ordinal(predicted_level)
        
        distance = abs(expected_ord - predicted_ord)
        
        if distance == 0:
            accuracy = 1.0
            verdict = "✅ EXACT"
        elif distance == 1:
            accuracy = 0.5
            verdict = "🟡 CLOSE"
        else:
            accuracy = 0.0
            verdict = "❌ MISS"
        
        total_score += accuracy
        total_count += 1
        
        results[organ] = {
            "expected": expected_level.capitalize(),
            "predicted": predicted_level.capitalize(),
            "predicted_pct": predicted_pct,
            "accuracy": accuracy,
            "verdict": verdict,
        }
    
    results["_aggregate"] = {
        "score": total_score,
        "max_score": total_count,
        "accuracy_pct": round((total_score / total_count) * 100, 1) if total_count > 0 else 0,
    }
    
    return results


def score_ae_overlap(predicted_aes: list, known_aes: list) -> dict:
    """
    Score overlap between predicted adverse events and known AEs.
    Uses substring/keyword matching (case-insensitive).
    """
    if not predicted_aes or not known_aes:
        return {"overlap_pct": 0, "matched": [], "missed": known_aes or [], "total_known": len(known_aes or [])}
    
    predicted_terms = [ae.get("term", "").lower() for ae in predicted_aes]
    predicted_text = " ".join(predicted_terms)
    
    matched = []
    missed = []
    
    for known_ae in known_aes:
        known_lower = known_ae.lower()
        # Check if any significant word from known AE appears in any predicted term
        known_words = [w for w in known_lower.split() if len(w) > 3]
        
        found = False
        for pred_term in predicted_terms:
            # Direct substring check
            if known_lower in pred_term or pred_term in known_lower:
                found = True
                break
            # Keyword overlap check
            if any(kw in pred_term for kw in known_words):
                found = True
                break
        
        if found:
            matched.append(known_ae)
        else:
            missed.append(known_ae)
    
    total = len(known_aes)
    overlap_pct = round((len(matched) / total) * 100, 1) if total > 0 else 0
    
    return {
        "overlap_pct": overlap_pct,
        "matched": matched,
        "missed": missed,
        "total_known": total,
        "total_predicted": len(predicted_aes),
    }


def score_structural_alerts(detected_alerts: list, expected_alerts: list) -> dict:
    """Check if expected structural alerts were detected."""
    if not expected_alerts:
        return {"expected": [], "detected": [], "sensitivity": 100.0, "note": "No alerts expected"}
    
    detected_names = [a.get("alert", "").lower() for a in detected_alerts if a.get("alert") != "None detected"]
    detected_keys = [a.get("matched_key", "").lower() for a in detected_alerts]
    
    found = []
    missed = []
    
    for exp in expected_alerts:
        exp_lower = exp.lower()
        if any(exp_lower in d for d in detected_names) or any(exp_lower in k for k in detected_keys):
            found.append(exp)
        else:
            missed.append(exp)
    
    total = len(expected_alerts)
    sensitivity = round((len(found) / total) * 100, 1) if total > 0 else 100.0
    
    return {
        "expected": expected_alerts,
        "detected_count": len(detected_names),
        "found": found,
        "missed": missed,
        "sensitivity": sensitivity,
    }


# =============================================================================
# MAIN VALIDATION RUNNER
# =============================================================================

def validate_single_drug(predictor, drug_key: str, ground_truth: dict, verbose: bool = True) -> dict:
    """Run validation for a single drug."""
    gt = ground_truth
    drug_name = gt["name"]
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"  VALIDATING: {drug_name}")
        print(f"{'='*70}")
    
    # Run prediction using drug name (more realistic for user-facing validation)
    start_time = time.time()
    try:
        report = predictor.run_workflow(gt["lookup_name"])
    except Exception as e:
        print(f"  [!] WORKFLOW FAILED for {drug_name}: {e}")
        return {"drug": drug_name, "status": "FAILED", "error": str(e)}
    elapsed = round(time.time() - start_time, 1)
    
    if not report or not isinstance(report, dict):
        return {"drug": drug_name, "status": "EMPTY_REPORT"}
    
    # --- 1. Organ Risk Accuracy ---
    organ_score = score_organ_risk(report, gt["known_organ_risks"])
    
    # --- 2. AE Overlap ---
    predicted_aes = report.get("Predicted AE", [])
    ae_score = score_ae_overlap(predicted_aes, gt["known_adverse_events"])
    
    # --- 3. Structural Alert Sensitivity ---
    alerts = report.get("Structural Alerts", [])
    alert_score = score_structural_alerts(alerts, gt.get("expected_structural_alerts", []))
    
    # --- 4. DeepChem Predictions Summary ---
    dc_preds = report.get("DeepChem Prediction", {}).get("predictions", {})
    dc_note = report.get("DeepChem Prediction", {}).get("note", "")
    top_targets = sorted(dc_preds.items(), key=lambda x: x[1], reverse=True)[:3] if dc_preds else []
    
    # --- 5. ADME Gating ---
    adme = report.get("ADME Gating", {})
    
    # --- 6. AE Concordance (built-in engine metric) ---
    concordance = report.get("AE Concordance", {})
    
    # Compile result
    result = {
        "drug": drug_name,
        "drug_key": drug_key,
        "status": "COMPLETE",
        "elapsed_sec": elapsed,
        "resolved_smiles": report.get("SMILES", ""),
        "resolved_name": report.get("Name", ""),
        "organ_risk": organ_score,
        "ae_overlap": ae_score,
        "structural_alerts": alert_score,
        "deepchem_top3": top_targets,
        "deepchem_note": dc_note,
        "adme_gating": adme,
        "ae_concordance": concordance,
        "faers_count": len(report.get("FAERS Top 5", [])),
        "pubmed_density": report.get("PubMed Confidence", {}).get("density", 0),
    }
    
    if verbose:
        print_drug_scorecard(result)
    
    return result


def print_drug_scorecard(result: dict):
    """Print a formatted scorecard for a single drug."""
    print(f"\n  📊 SCORECARD: {result['drug']}")
    print(f"  ├── Resolved As: {result['resolved_name']} | SMILES: {result['resolved_smiles'][:50]}...")
    print(f"  ├── Runtime: {result['elapsed_sec']}s | FAERS Hits: {result['faers_count']} | PubMed Density: {result['pubmed_density']}%")
    print(f"  ├── DeepChem: {result['deepchem_note'][:80]}")
    
    # Organ Risk Table
    organ = result["organ_risk"]
    print(f"  │")
    print(f"  ├── ORGAN RISK ACCURACY: {organ['_aggregate']['accuracy_pct']}%")
    print(f"  │   {'Organ':<12} {'Expected':<12} {'Predicted':<14} {'Score%':<8} {'Verdict'}")
    print(f"  │   {'─'*60}")
    for o in ["liver", "lung", "kidney", "heart", "brain"]:
        d = organ[o]
        print(f"  │   {o.capitalize():<12} {d['expected']:<12} {d['predicted']:<8} ({d['predicted_pct']:>3}%) {d['accuracy']:<8} {d['verdict']}")
    
    # AE Overlap
    ae = result["ae_overlap"]
    print(f"  │")
    print(f"  ├── AE OVERLAP: {ae['overlap_pct']}% ({len(ae['matched'])}/{ae['total_known']} known AEs matched)")
    if ae["matched"]:
        print(f"  │   ✅ Matched: {', '.join(ae['matched'][:5])}")
    if ae["missed"]:
        print(f"  │   ❌ Missed:  {', '.join(ae['missed'][:5])}")
    
    # Structural Alerts
    sa = result["structural_alerts"]
    print(f"  │")
    print(f"  ├── STRUCTURAL ALERT SENSITIVITY: {sa['sensitivity']}%")
    if sa.get("found"):
        print(f"  │   ✅ Found: {', '.join(sa['found'])}")
    if sa.get("missed"):
        print(f"  │   ❌ Missed: {', '.join(sa['missed'])}")
    
    # AE Concordance (engine built-in)
    conc = result["ae_concordance"]
    print(f"  │")
    print(f"  └── ENGINE AE CONCORDANCE: {conc.get('concordance_pct', 0)}%")
    print()


def print_final_report(all_results: list):
    """Print the aggregate validation report."""
    completed = [r for r in all_results if r["status"] == "COMPLETE"]
    failed = [r for r in all_results if r["status"] != "COMPLETE"]
    
    print(f"\n{'='*70}")
    print(f"  FINAL VALIDATION REPORT")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Drugs Tested: {len(all_results)} | Completed: {len(completed)} | Failed: {len(failed)}")
    print(f"{'='*70}")
    
    if failed:
        print(f"\n  ⚠️  FAILED DRUGS:")
        for f in failed:
            print(f"     - {f['drug']}: {f.get('error', f['status'])}")
    
    if not completed:
        print("  No successful validations to report.")
        return
    
    # Aggregate Organ Accuracy
    total_organ_score = sum(r["organ_risk"]["_aggregate"]["score"] for r in completed)
    total_organ_max = sum(r["organ_risk"]["_aggregate"]["max_score"] for r in completed)
    overall_organ_accuracy = round((total_organ_score / total_organ_max) * 100, 1) if total_organ_max > 0 else 0
    
    # Per-organ accuracy
    organ_scores = {}
    for organ in ["liver", "lung", "kidney", "heart", "brain"]:
        scores = [r["organ_risk"][organ]["accuracy"] for r in completed]
        organ_scores[organ] = round(sum(scores) / len(scores) * 100, 1)
    
    # Aggregate AE Overlap
    avg_ae_overlap = round(sum(r["ae_overlap"]["overlap_pct"] for r in completed) / len(completed), 1)
    
    # Aggregate Alert Sensitivity
    alert_sensitivities = [r["structural_alerts"]["sensitivity"] for r in completed]
    avg_alert_sensitivity = round(sum(alert_sensitivities) / len(alert_sensitivities), 1)
    
    # Aggregate Concordance
    concordances = [r["ae_concordance"].get("concordance_pct", 0) for r in completed]
    avg_concordance = round(sum(concordances) / len(concordances), 1)
    
    print(f"\n  ┌─────────────────────────────────────────────────────────┐")
    print(f"  │  AGGREGATE METRICS                                      │")
    print(f"  ├─────────────────────────────────────────────────────────┤")
    print(f"  │  Overall Organ Risk Accuracy:  {overall_organ_accuracy:>6}%                  │")
    print(f"  │  Average AE Overlap:           {avg_ae_overlap:>6}%                  │")
    print(f"  │  Structural Alert Sensitivity: {avg_alert_sensitivity:>6}%                  │")
    print(f"  │  Engine AE Concordance:        {avg_concordance:>6}%                  │")
    print(f"  └─────────────────────────────────────────────────────────┘")
    
    print(f"\n  PER-ORGAN ACCURACY:")
    print(f"  {'Organ':<12} {'Accuracy':<10} {'Grade'}")
    print(f"  {'─'*35}")
    for organ, score in organ_scores.items():
        grade = "🟢 A" if score >= 80 else ("🟡 B" if score >= 60 else ("🟠 C" if score >= 40 else "🔴 D"))
        print(f"  {organ.capitalize():<12} {score:>6}%    {grade}")
    
    # Risk Confusion Matrix (Simple)
    print(f"\n  RISK LEVEL CONFUSION MATRIX:")
    print(f"  {'Expected →':<16} {'High':<10} {'Moderate':<10} {'Low':<10} {'None':<10}")
    print(f"  {'─'*46}")
    for pred_level in ["High", "Moderate", "Low", "None"]:
        counts = {"High": 0, "Moderate": 0, "Low": 0, "None": 0}
        for r in completed:
            for organ in ["liver", "lung", "kidney", "heart", "brain"]:
                d = r["organ_risk"][organ]
                if d["predicted"].lower() == pred_level.lower():
                    counts[d["expected"]] = counts.get(d["expected"], 0) + 1
        print(f"  Pred {pred_level:<10} {counts['High']:<10} {counts['Moderate']:<10} {counts['Low']:<10} {counts['None']:<10}")
    
    # Per-Drug Summary Table
    print(f"\n  PER-DRUG SUMMARY:")
    print(f"  {'Drug':<28} {'Organ%':<10} {'AE%':<8} {'Alert%':<10} {'Conc%':<8} {'Time'}")
    print(f"  {'─'*74}")
    for r in sorted(completed, key=lambda x: x["organ_risk"]["_aggregate"]["accuracy_pct"], reverse=True):
        print(f"  {r['drug']:<28} "
              f"{r['organ_risk']['_aggregate']['accuracy_pct']:>5}%    "
              f"{r['ae_overlap']['overlap_pct']:>4}%    "
              f"{r['structural_alerts']['sensitivity']:>5}%    "
              f"{r['ae_concordance'].get('concordance_pct', 0):>4}%    "
              f"{r['elapsed_sec']:>5}s")
    
    # Worst Misses (for enhancement targeting)
    print(f"\n  🔍 TOP MISSES (Enhancement Targets):")
    misses = []
    for r in completed:
        for organ in ["liver", "lung", "kidney", "heart", "brain"]:
            d = r["organ_risk"][organ]
            if d["accuracy"] == 0.0:
                misses.append({
                    "drug": r["drug"],
                    "organ": organ,
                    "expected": d["expected"],
                    "predicted": d["predicted"],
                    "predicted_pct": d["predicted_pct"],
                })
    
    if misses:
        for m in misses[:15]:
            print(f"  ❌ {m['drug']:<25} {m['organ'].capitalize():<10} "
                  f"Expected: {m['expected']:<10} Got: {m['predicted']} ({m['predicted_pct']}%)")
    else:
        print(f"  ✅ No critical misses found!")
    
    print(f"\n{'='*70}")


def save_results(all_results: list, output_path: str):
    """Save detailed results to JSON for further analysis."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  📁 Detailed results saved to: {output_path}")


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    # Parse args
    single_drug = None
    if len(sys.argv) > 1:
        single_drug = sys.argv[1].lower().replace(" ", "_").replace("-", "_")
    
    print("=" * 70)
    print("  TOXICITY PREDICTION ENGINE — GROUND TRUTH VALIDATION")
    print("=" * 70)
    
    # Initialize predictor
    print("\n[*] Initializing ToxicityPredictor (DeepChem + BioBERT + RDKit)...")
    predictor = ToxicityPredictor()
    
    # Select drugs to validate
    if single_drug:
        if single_drug in GROUND_TRUTH:
            drugs_to_test = {single_drug: GROUND_TRUTH[single_drug]}
        else:
            print(f"[!] Drug '{single_drug}' not found in ground truth database.")
            print(f"    Available: {', '.join(GROUND_TRUTH.keys())}")
            return
    else:
        drugs_to_test = GROUND_TRUTH
    
    print(f"[*] Testing {len(drugs_to_test)} drug(s)...\n")
    
    # Run validation
    all_results = []
    for drug_key, gt in drugs_to_test.items():
        result = validate_single_drug(predictor, drug_key, gt)
        all_results.append(result)
    
    # Print final report
    print_final_report(all_results)
    
    # Save results
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "validation_results.json")
    save_results(all_results, output_path)


if __name__ == "__main__":
    main()
