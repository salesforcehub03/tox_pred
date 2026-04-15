import pandas as pd
import os

files = [
    r'd:\AViiD\AViiD\PreclinicalData 1.xlsx',
    r'd:\AViiD\AViiD\Similar molecules Clinical.xlsx'
]

for f in files:
    print(f"\n[*] Checking: {f}")
    if os.path.exists(f):
        try:
            df = pd.read_excel(f).head(5)
            print("[+] Headers:", df.columns.tolist())
            print("[+] Sample data:\n", df)
        except Exception as e:
            print(f"[!] Error reading {f}: {e}")
    else:
        print("[!] File not found.")
