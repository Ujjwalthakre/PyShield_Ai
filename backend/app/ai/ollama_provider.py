import requests
from .base import AIProvider


class OllamaProvider(AIProvider):
    def __init__(self, model_name: str = "phi3", base_url: str = "http://127.0.0.1:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def _call_api(self, prompt: str) -> str:
        """Helper method to send the prompt to Ollama's REST API."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.exceptions.RequestException as e:
            return f"Error contacting Ollama: {str(e)}"

    def explain_finding(self, code_snippet: str, rule_id: str, message: str) -> str:
        prompt = f"""You are an expert Application Security Engineer. 
                A static analysis tool flagged the following Python code for a security vulnerability.

                Rule ID: {rule_id}
                Scanner Message: {message}

                Vulnerable Code:
                {code_snippet}

                Explain exactly WHY this code is dangerous in 2 or 3 short sentences. 
                Be concise and speak directly to a developer."""

        return self._call_api(prompt)

    def generate_fix(self, code_snippet: str, rule_id: str, message: str) -> str:
        prompt = f"""You are an automated code remediation AI. 
                Your ONLY purpose is to output raw, fixed Python code.

                You must follow these strict rules:
                1. Do NOT wrap the code in markdown formatting blocks (no ```python or ```).
                2. Do NOT output any conversational text, greetings, or explanations.
                3. Fix the vulnerability described below while keeping the original function intact.

                Vulnerability to fix:
                Rule ID: {rule_id}
                Scanner Message: {message}

                Vulnerable Code:
                {code_snippet}

                Fixed Code:"""

        return self._call_api(prompt)