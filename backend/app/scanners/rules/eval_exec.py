import ast
from typing import List
from ..base import SecurityRule
from ..models import Finding

class EvalRule(SecurityRule):
    rule_id = "PY-001"
    severity = "CRITICAL"

    def analyze(self, node: ast.AST, context: dict = None) -> List[Finding]:
        findings = []
        
        # Is it a function call?
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            # Is the function named 'eval'?
            if node.func.id in ["eval", "exec"]:
                finding = Finding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"Dangerous use of {node.func.id} detected. Can lead to Remote Code Execution.",
                    line=node.lineno
                )
                findings.append(finding)
                
        return findings