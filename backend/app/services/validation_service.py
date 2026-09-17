import ast
from dataclasses import dataclass
from typing import List
from app.scanners.engine import ScannerEngine
from app.scanners.models import Finding

@dataclass
class ValidationResult:
    is_valid_syntax: bool
    is_resolved: bool
    status: str
    error_message: str = ""
    remaining_findings: List[Finding] = None

class ValidationPipeline:
    def __init__(self, scanner_engine: ScannerEngine):
        self.scanner = scanner_engine

    def validate_fix(self, proposed_code: str, original_rule_id: str, file_path: str = "snippet.py") -> ValidationResult:
        # Step 1: Syntax Validation
        try:
            ast.parse(proposed_code)
        except SyntaxError as e:
            return ValidationResult(
                is_valid_syntax=False,
                is_resolved=False,
                status="SYNTAX_ERROR",
                error_message=f"Syntax Error on line {e.lineno}: {e.msg}",
                remaining_findings=[]
            )

        # Step 2: Rescan proposed code
        new_findings = self.scanner.scan(code=proposed_code, file_path=file_path)

        # Step 3: Check if original vulnerability is still present
        original_still_present = any(f.rule_id == original_rule_id for f in new_findings)

        if original_still_present:
            return ValidationResult(
                is_valid_syntax=True,
                is_resolved=False,
                status="FIX_FAILED",
                error_message=f"Rule {original_rule_id} is still triggered by the proposed code.",
                remaining_findings=new_findings
            )

        # Step 4: Check if new security issues were introduced
        if len(new_findings) > 0:
            return ValidationResult(
                is_valid_syntax=True,
                is_resolved=False,
                status="REGRESSION_DETECTED",
                error_message="Fix introduced new security vulnerabilities.",
                remaining_findings=new_findings
            )

        return ValidationResult(
            is_valid_syntax=True,
            is_resolved=True,
            status="VERIFIED",
            error_message="",
            remaining_findings=[]
        )