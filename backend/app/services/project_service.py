import os
import subprocess
import zipfile
from typing import Dict

def find_python_files(directory: str) -> Dict[str, str]:
    """Recursively finds all .py files and returns a dictionary of {relative_filepath: text_content}."""
    files_dict = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                # Keep paths relative to the root for clean UI display (e.g., 'src/app.py')
                rel_path = os.path.relpath(full_path, directory)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        files_dict[rel_path] = f.read()
                except Exception:
                    pass # Skip unreadable or binary files safely
    return files_dict

def clone_repo(repo_url: str, target_dir: str):
    """Clones a GitHub repository into the target directory using a shallow clone for speed."""
    subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, target_dir],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def extract_zip(zip_path: str, target_dir: str):
    """Extracts a ZIP file into the target directory."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)