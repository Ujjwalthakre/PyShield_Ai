from app.scanners.engine import ScannerEngine
from app.scanners.rules.eval_exec import EvalRule

target_code = """
import os

user_input = "2 + 2"
# Safe string
safe = "exec(user_input)"

# Dangerous calls
exec(user_input)
"""

# 1. Initialize our rules
active_rules = [EvalRule()]

# 2. Boot up the engine with our rules
scanner = ScannerEngine(rules=active_rules)

# 3. Run the scan
print("Scanning code...")
results = scanner.scan(target_code)

# 4. Print results
if not results:
    print("✅ No vulnerabilities found!")
else:
    print(f"❌ Found {len(results)} vulnerabilities:")
    for finding in results:
        print(f"  [{finding.severity}] {finding.file}:{finding.line} - {finding.rule_id}: {finding.message}")