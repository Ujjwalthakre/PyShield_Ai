import ast
from typing import List
from ..base import SecurityRule
from ..models import Finding


class HardcodedSecretsRule(SecurityRule):
    rule_id = "SEC-001"
    severity = "HIGH"

    def analyze(self, node: ast.AST, context: dict = None) -> List[Finding]:
        findings = []

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # Check for hardcoded secrets in variable names
                    if "password" in target.id.lower() or "secret" in target.id.lower() or "api_key" in target.id.lower():
                        if isinstance(node.value, ast.Constant):
                            findings.append(
                                Finding(
                                    rule_id=self.rule_id,
                                    severity=self.severity,
                                    message=f"Hardcoded secret detected in variable '{target.id}'. Consider using environment variables or secure vaults.",
                                    line=node.lineno
                                )
                            )
        return findings