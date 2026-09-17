import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

# 1. Run a scan with a vulnerable snippet
scan_payload = {
    "code": "import os\ndef run_cmd(cmd):\n    os.system(cmd)",
    "file_name": "danger.py"
}

print("1. Submitting scan...")
scan_res = requests.post(f"{BASE_URL}/scan", json=scan_payload).json()
print(f"Total findings detected: {scan_res['total_findings']}")

# 2. Request AI explanation for Finding ID 1
print("\n2. Requesting AI explanation for Finding #1...")
explain_res = requests.post(f"{BASE_URL}/findings/1/explain").json()
print(f"Rule: {explain_res['rule_id']}")
print(f"Cached: {explain_res['cached']}")
print(f"Explanation:\n{explain_res['explanation']}")

# 3. Call it a second time to verify database caching
print("\n3. Requesting AI explanation again (verifying cache)...")
cached_res = requests.post(f"{BASE_URL}/findings/1/explain").json()
print(f"Cached: {cached_res['cached']} (Expected: True)")