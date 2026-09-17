from app.scanners.engine import ScannerEngine
from app.scanners.rules.eval_exec import EvalRule
from app.scanners.rules.sql_injection import SQLInjectionRule

target_code = """
def get_user(user_id):
    # DANGEROUS: f-string
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    
    # DANGEROUS: .format()
    cursor.execute("SELECT * FROM users WHERE id = {}".format(user_id))
    
    # SAFE: parameterized
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
"""

# Load multiple rules into our engine!
active_rules = [EvalRule(), SQLInjectionRule()]
scanner = ScannerEngine(rules=active_rules)

print("Scanning code...")
results = scanner.scan(target_code)

if not results:
    print("✅ No vulnerabilities found!")
else:
    print(f"❌ Found {len(results)} vulnerabilities:")
    for finding in results:
        print(f"  [{finding.severity}] {finding.rule_id} at line {finding.line}: {finding.message}")