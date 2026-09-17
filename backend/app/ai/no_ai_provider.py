from .base import AIProvider

class NoAIProvider(AIProvider):
    """
    A fallback provider that just returns generic deterministic messages 
    when AI is disabled or unavailable.
    """

    def explain_finding(self, code_snippet: str, rule_id: str, message: str) -> str:
        return f"[Deterministic Fallback] Rule {rule_id} triggered: {message}. No AI configured to provide deeper analysis."

    def generate_fix(self, code_snippet: str, rule_id: str, message: str) -> str:
        return "# Fix generation requires an active AI provider. Please fix manually based on the scanner message."