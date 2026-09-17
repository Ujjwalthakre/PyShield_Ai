# backend/app/services/diff_service.py
import difflib

def sanitize_ai_code(code: str) -> str:
    lines = code.strip().splitlines()
    cleaned_lines = []
    for line in lines:
        if line.strip().startswith("```"):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()

def generate_unified_diff(original_code: str, fixed_code: str, file_name: str = "snippet.py") -> str:
    cleaned_fixed = sanitize_ai_code(fixed_code)

    original_lines = [line if line.endswith("\n") else line + "\n" for line in original_code.strip().splitlines(keepends=True)]
    fixed_lines = [line if line.endswith("\n") else line + "\n" for line in cleaned_fixed.strip().splitlines(keepends=True)]

    diff = difflib.unified_diff(
        original_lines,
        fixed_lines,
        fromfile=f"a/{file_name}",
        tofile=f"b/{file_name}",
        lineterm=""
    )
    return "\n".join(diff)