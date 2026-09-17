from app.scanners.engine import ScannerEngine
from app.scanners.rules.command_injection import CommandInjectionRule
from app.scanners.rules.hardcoded_secrets import HardcodedSecretsRule

target_code = """
import os
import subprocess

def ping_server(ip_address):
    # DANGEROUS
    os.system(f"ping -c 4 {ip_address}")
    
    # DANGEROUS
    os.popen("ls -l " + ip_address)

api_key = os.environ.get("API_KEY")
api_key ="hihhh8484849494f4049409"
"""

scanner = ScannerEngine(rules=[CommandInjectionRule(), HardcodedSecretsRule()])
results = scanner.scan(target_code, file_path="network_utils.py")

for finding in results:
    print(f"[{finding.severity}] {finding.file}:{finding.line} - {finding.rule_id}: {finding.message}")