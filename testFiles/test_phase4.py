from app.scanners.engine import ScannerEngine
from app.scanners.rules.sql_injection import SQLInjectionRule

target_code = """
def search_users(user_id, sort_col):
    # This is a VALUE injection (Safe to parameterize)
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    
    # This is an IDENTIFIER injection (Must use allowlist)
    cursor.execute(f"SELECT * FROM users ORDER BY {sort_col}")
    cursor.execute(f"SELECT * FROM {table_name} WHERE status = 'active'")
"""

scanner = ScannerEngine(rules=[SQLInjectionRule()])
results = scanner.scan(target_code, file_path="db_queries.py")

for finding in results:
    print(f"[{finding.severity}] Line {finding.line}: {finding.message}")