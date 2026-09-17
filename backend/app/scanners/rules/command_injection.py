import ast
from typing import List
from ..base import SecurityRule
from ..models import Finding

class CommandInjectionRule(SecurityRule):
    rule_id = "CMD-001"
    severity = "CRITICAL"

    def analyze(self, node: ast.AST, context: dict = None) -> List[Finding]:
        findings = []
        if context is None:
            context = {}
            
        variable_map = context.get("variable_map", {})
        
        if not isinstance(node, ast.Call):
            return findings

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "os" and node.func.attr in ["system", "popen"]:
                
                # 1. Get the argument passed to os.system()
                if not node.args:
                    return findings
                arg = node.args[0]
                
                # 2. Check if the argument is a variable (ast.Name)
                if isinstance(arg, ast.Name):
                    var_name = arg.id
                    
                    # 3. Look up where this variable came from in our context!
                    if var_name in variable_map:
                        original_value = variable_map[var_name]
                        
                        # Check if the original value came from an untrusted SOURCE (like 'request')
                        if isinstance(original_value, ast.Attribute) and isinstance(original_value.value, ast.Name):
                            if original_value.value.id == "request":
                                findings.append(
                                    Finding(
                                        rule_id=self.rule_id,
                                        severity=self.severity,
                                        message=f"Tainted Command Injection: '{var_name}' comes from 'request' and is passed to os.{node.func.attr}().",
                                        line=node.lineno,
                                        sink=f"os.{node.func.attr}()",
                                        source=f"request.{original_value.attr}"
                                    )
                                )
                                return findings
                
                # If it's not a tracked variable, just do the standard check
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity="MEDIUM", # Downgraded to medium because we can't prove it's user input
                        message=f"Possible Command Injection: os.{node.func.attr}() detected.",
                        line=node.lineno
                    )
                )
                    
        return findings