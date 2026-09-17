from app.scanners.engine import ScannerEngine
from app.scanners.rules.command_injection import CommandInjectionRule
from app.services.validation_service import ValidationPipeline

# 1. Setup our engine and pipeline
scanner = ScannerEngine(rules=[CommandInjectionRule()])
pipeline = ValidationPipeline(scanner_engine=scanner)

print("🧪 Testing Edge Case 1: AI generates invalid Python syntax")
broken_ai_code = "Here is your code:\ndef ping(ip): os.system(ip)"

result_1 = pipeline.validate_fix(
    proposed_code=broken_ai_code, 
    original_rule_id="CMD-001"
)
print(f"Status: {result_1.status} (Expected: SYNTAX_ERROR)")
print(f"Message: {result_1.error_message}")


print("\n🧪 Testing Edge Case 2: AI generates valid code, but fails to fix the vulnerability")
# The AI kept os.system instead of switching to subprocess!
stubborn_ai_code = """
import os
def ping(ip):
    # Added a comment, but still vulnerable!
    os.system("ping -c 1 " + ip)
"""

result_2 = pipeline.validate_fix(
    proposed_code=stubborn_ai_code, 
    original_rule_id="CMD-001"
)
print(f"Status: {result_2.status} (Expected: FIX_FAILED)")
print(f"Message: {result_2.error_message}")
print(f"Remaining Findings: {len(result_2.remaining_findings)}")