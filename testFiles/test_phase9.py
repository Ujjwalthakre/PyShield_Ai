from app.ai.no_ai_provider import NoAIProvider
from app.ai.ollama_provider import OllamaProvider

# We instantiate our provider
ai = OllamaProvider()

# Fake finding data
code = "os.system(user_input)"
rule = "CMD-001"
msg = "Command Injection detected."

print("--- AI Explanation ---")
explanation = ai.explain_finding(code, rule, msg)
print(explanation)

print("\n--- AI Fix ---")
fix = ai.generate_fix(code, rule, msg)
print(fix)