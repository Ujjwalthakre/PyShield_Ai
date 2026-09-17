import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

# 1. Scan vulnerable command injection code
code = """import os
def ping(host):
    os.system("ping -c 1 " + host)
"""
print("1. Scanning code...")
scan_res = requests.post(f"{BASE_URL}/scan", json={"code": code, "file_name": "net.py"}).json()
print(f"Findings: {scan_res['total_findings']}")

# 2. Generate AI fix
print("\n2. Generating AI Fix...")
fix_res = requests.post(f"{BASE_URL}/findings/1/fix").json()
print(f"Status after fix generation: {fix_res['status']}")

# 3. Validate the fix
print("\n3. Validating proposed fix...")
val_res = requests.post(f"{BASE_URL}/findings/1/validate").json()
print(f"Status: {val_res['status']}")
print(f"Syntax Valid: {val_res['syntax_valid']}")
print(f"Resolved: {val_res['resolved']}")
print(f"Message: {val_res['message']}")