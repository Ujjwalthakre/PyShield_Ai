from app.ai.ollama_provider import OllamaProvider

ai = OllamaProvider()

vulnerable_code = """
import os
def ping(ip):
    os.system("ping -c 4 " + ip)
"""

print("🧠 Asking Ollama to explain the vulnerability...\n")
explanation = ai.explain_finding(
    code_snippet=vulnerable_code,
    rule_id="CMD-001",
    message="Command Injection risk: os.system() detected."
)
print("--- AI EXPLANATION ---")
print(explanation)


print("\n🛠️ Asking Ollama to generate a fix...\n")
fix = ai.generate_fix(
    code_snippet=vulnerable_code,
    rule_id="CMD-001",
    message="Command Injection risk: os.system() detected."
)
print("--- AI FIX (RAW CODE) ---")
print(fix)