from abc import ABC, abstractmethod

class AIProvider(ABC):
    """
    The strict blueprint that all AI providers must follow.
    """
    
    @abstractmethod
    def explain_finding(self, code_snippet: str, rule_id: str, message: str) -> str:
        """
        Takes the vulnerable code and the scanner message, and returns 
        a developer-friendly explanation of why it's dangerous.
        """
        pass

    @abstractmethod
    def generate_fix(self, code_snippet: str, rule_id: str, message: str) -> str:
        """
        Takes the vulnerable code and returns ONLY the fixed Python code.
        """
        pass