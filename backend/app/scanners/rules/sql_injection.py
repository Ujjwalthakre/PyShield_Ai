import ast
from typing import List
from ..base import SecurityRule
from ..models import Finding

class SQLInjectionRule(SecurityRule):
    rule_id = "SQL-001"
    severity = "HIGH"

    def analyze(self, node: ast.AST, context: dict = None) -> List[Finding]:
        findings = []
        
        if not isinstance(node, ast.Call):
            return findings
            
        if isinstance(node.func, ast.Attribute) and node.func.attr == "execute":
            if not node.args:
                return findings
                
            first_arg = node.args[0]
            
            # 3. Check f-strings (ast.JoinedStr)
            if isinstance(first_arg, ast.JoinedStr):
                is_identifier = False
                
                # Loop through the parts of the f-string
                for i, part in enumerate(first_arg.values):
                    # When we find the dynamic variable...
                    if isinstance(part, ast.FormattedValue):
                        # Look at the text part immediately before it
                        if i > 0 and isinstance(first_arg.values[i-1], ast.Constant):
                            # Convert to uppercase to make checking easy
                            prev_text = first_arg.values[i-1].value.upper()
                            
                            # Does the text right before the variable end with ORDER BY?
                            if prev_text.strip().endswith("ORDER BY") or prev_text.strip().endswith("FROM"):
                                is_identifier = True
                                break
                
                # Provide the correct, specific remediation message
                if is_identifier and prev_text.strip().endswith("ORDER BY"):
                    msg = f"SQL Injection (Identifier). Cannot parameterize 'ORDER BY'. Use a strict allowlist."
                elif is_identifier and prev_text.strip().endswith("FROM"):
                    msg = f"SQL Injection (Identifier). Cannot parameterize 'FROM'. Use a strict allowlist."
                else:
                    msg = "SQL Injection (Value). Use parameterized queries (e.g., %s or ?)."

                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=msg,
                        line=node.lineno
                    )
                )

            # 4. Check for .format() (Keeping your previous work!)
            elif isinstance(first_arg, ast.Call) and isinstance(first_arg.func, ast.Attribute):
                if first_arg.func.attr == "format":
                    findings.append(
                        Finding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message="SQL Injection (Value). .format() used in SQL execution. Use parameterized queries.",
                            line=node.lineno
                        )
                    )
                    
        return findings