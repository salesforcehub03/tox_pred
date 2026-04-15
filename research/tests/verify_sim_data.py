import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from simulation_engine import SimulationEngine

def test_excel_integration():
    engine = SimulationEngine()
    
    # Test case: Belinostat
    # We expect the engine to find Belinostat_extracted_data.xlsx 
    # and override the default parameters.
    test_params = {
        "drug_name": "Belinostat",
        "dose": 500,
        "organ_risks": {
            "Liver": {"score": 85, "threshold": 5.0}
        }
    }
    
    print("[*] Running simulation for Belinostat...")
    results = engine.run_simulation(test_params)
    
    # Check what parameters were used (we need to expose them or check the manager)
    ext_params = engine.data_manager.get_parameters("Belinostat")
    
    if ext_params:
        print("[+] SUCCESS: Excel data found for Belinostat.")
        print(f"    Sources: {ext_params.get('source')}")
        print(f"    Extracted Parameters: { {k:v for k,v in ext_params.items() if k != 'source'} }")
    else:
        print("[-] FAIL: No Excel data found. Check if kg_data folder is visible.")
    
    print(f"[*] Final Kidney Stress: {results['organs']['Liver']['final_stress']:.2f}%")

if __name__ == "__main__":
    test_excel_integration()
