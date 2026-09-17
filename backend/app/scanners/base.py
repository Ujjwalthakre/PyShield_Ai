import ast
from typing import List
from .models import Finding

class SecurityRule:
    rule_id: str = "BASE"
    severity: str = "INFO"

    def analyze(self, node: ast.AST, context: dict = None) -> List[Finding]:
        """
        Takes an AST node and an optional context dictionary (for variable tracking).
        """
        return []