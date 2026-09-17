import ast
from typing import List
from .models import Finding
from .base import SecurityRule

class ScannerEngine(ast.NodeVisitor):
    def __init__(self, rules: List[SecurityRule]):
        self.rules = rules
        self.findings: List[Finding] = []
        
        # NEW: Track variable assignments in this file
        # Format: {"variable_name": AST_Node_of_Value}
        self.variable_map = {}

    # NEW: Intercept every assignment (e.g., x = y)
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variable_map[target.id] = node.value
        self.generic_visit(node)

    def generic_visit(self, node: ast.AST):
        # Create the context dictionary to pass to our rules
        context = {
            "variable_map": self.variable_map
        }
        
        for rule in self.rules:
            # Pass the context into the rule!
            detected_findings = rule.analyze(node, context)
            self.findings.extend(detected_findings)
            
        super().generic_visit(node)

    def scan(self, code: str, file_path: str = "unknown") -> List[Finding]:
        self.findings = []
        self.variable_map = {} # Reset map for each new file
        
        tree = ast.parse(code)
        self.visit(tree)
        
        for finding in self.findings:
            finding.file = file_path
            
        return self.findings