import requests
import json

def test_simulation():
    url = "http://localhost:8000/v1/toxicity/simulate"
    payload = {
        "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O", # Aspirin
        "dose": 500,
        "duration": 24
    }
    
    print(f"[*] Testing Simulation API at {url}...")
    try:
        # Note: This assumes the backend server is running on localhost:8000
        # If it's not running, we'll just catch the exception
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("[+] Success! Simulation data received.")
            print(f"    Drug: {data['drug_info']['name']}")
            print(f"    Time points: {len(data['time_series']['time'])}")
            print(f"    Organs simulated: {list(data['organ_series'].keys())}")
        else:
            print(f"[-] Failed. Status: {response.status_code}")
            print(f"    Error: {response.text}")
    except Exception as e:
        print(f"[!] Could not connect to backend: {e}")
        print("[*] Manual verification required: Start 'backend/main.py' and check '/v1/toxicity/simulate'.")

if __name__ == "__main__":
    test_simulation()
