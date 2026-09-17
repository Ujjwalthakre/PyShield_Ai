import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

# 1. Submit vulnerable code
vulnerable_app = """import os

def ping_host(host):
    os.system("ping -c 1 " + host)
"""

print("1. Submitting scan...")
scan_res = requests.post(f"{BASE_URL}/scan", json={
    "code": vulnerable_app,
    "file_name": "network.py"
}).json()
print(f"Scan finished. Found {scan_res['total_findings']} issue(s).")

# 2. Request Fix for Finding ID 1
print("\n2. Requesting AI Fix & Unified Diff...")
fix_res = requests.post(f"{BASE_URL}/findings/1/fix").json()

print(f"Status: {fix_res['status']}")
print("\n--- PROPOSED CODE ---")
print(fix_res['proposed_code'])

print("\n--- UNIFIED DIFF ---")
print(fix_res['diff'])