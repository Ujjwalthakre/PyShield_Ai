from app.scanners.engine import ScannerEngine
from app.scanners.rules.command_injection import CommandInjectionRule

target_code = """
import os

def handle_request(request):
    # 1. Source: Untrusted data from request
    user_input = request.args
    
    # 2. Sink: Reaches execution
    os.system(user_input)
    
    # 3. Safe hardcoded usage
    safe_cmd = "ls -l"
    os.system(safe_cmd)
"""

scanner = ScannerEngine(rules=[CommandInjectionRule()])
results = scanner.scan(target_code, file_path="app.py")

for finding in results:
    print(f"[{finding.severity}] {finding.rule_id}: {finding.message} Data flows from {finding.source} to {finding.sink} at line {finding.line}.")