# 🏛️ PyShield AI: Master Architecture & Implementation Document

This document serves as the complete engineering reference for PyShield AI. It details the system's purpose, architectural decisions, directory structure, and the complete chronological implementation of features.

---

## Part 1: The "What" and "Why" (System Overview)

**What is PyShield AI?**
PyShield is a full-stack security scanning and automated remediation platform. It analyzes Python code to detect security vulnerabilities, explains the risks, and generates safe, verified code patches using AI.

**Core Architectural Decisions (The "Why"):**
*   **Why AST over Regex?** Regular expressions are notoriously bad at parsing code; they flag commented-out code and miss complex, multi-line vulnerabilities. By using Python's `ast` (Abstract Syntax Tree) module, PyShield mathematically traverses the code's structure, eliminating false positives.
*   **Why a Local LLM (Ollama)?** Sending proprietary enterprise code to a third-party API like OpenAI is a massive security risk. Using Ollama with the `phi3` model keeps all source code completely on-device.
*   **Why Context Cropping?** Local LLMs crash or hallucinate when fed massive 500+ line repository files. PyShield solves this by cropping exactly 15 lines above and below the vulnerability, ensuring fast, accurate AI inference.
*   **Why the Validation Pipeline?** LLMs are non-deterministic and often write broken code. The Dual-Gate validation pipeline intercepts the AI's output, checks it for valid syntax, and rescans it in memory to guarantee the vulnerability is actually patched before the user ever sees it.

---

## Part 2: The "Where" (Directory & File Guide)

This section maps out the exact project structure and explains the responsibility of every directory and file.

### 1. Backend (`backend/app/`)
The FastAPI backend is built using a domain-driven design, separating routing, business logic, and database management.

*   **`main.py`**: The entry point. It initializes the FastAPI application, mounts the database, and defines all the API routes (`/scan`, `/scan/github`, `/scan/zip`, `/explain`, `/fix`).
*   **`db/`**: Handles data persistence.
    *   Contains the SQLAlchemy configuration and the SQLite database file (`pyshield.db`).
    *   Holds the `Scan`, `Finding`, and `Remediation` tables.
*   **`ai/`**: 
    *   Contains the AI integration logic. It connects to the local Ollama instance running on port `11434` and manages the specific prompt engineering required to force the AI to return raw code instead of conversational text.
*   **`schemas/`**:
    *   **`scan.py`**: Contains Pydantic models (e.g., `GitHubScanRequest`). This validates that incoming JSON requests from the frontend are formatted correctly before they hit the controller logic.
*   **`services/`**: The core business logic layer.
    *   **`diff_service.py`**: Uses Python's `difflib` to compare the original vulnerable code against the AI's proposed code, generating the Git-style Unified Diff.
    *   **`project_service.py`**: Handles OS-level operations. It uses `subprocess` to `git clone` repositories, extracts `.zip` files, and recursively traverses directories to find all `.py` files.
    *   **`validation_service.py`**: Houses the Dual-Gate validation logic (Syntax checking via `ast.parse` and the security regression rescan).
*   **`scanners/`**: The core deterministic detection engine.
    *   **`engine.py`**: The main orchestrator that takes a file, runs it through the AST parser, and applies all the rules.
    *   **`base.py`**: Defines the abstract base class that every security rule must follow.
    *   **`models.py`**: Internal data structures representing a found vulnerability before it is saved to the database.
    *   **`rules/`**: The modular rule definitions.
        *   `command_injection.py`: Detects `os.system` and `subprocess` without `shell=False`.
        *   `eval_exec.py`: Detects dangerous dynamic code execution.
        *   `hardcoded_secrets.py`: Detects passwords, API keys, or tokens in plain text.
        *   `sql_injection.py`: Detects raw, unparameterized SQL queries.

### 2. Frontend (`frontend/src/app/`)
The Next.js application serves as the user interface, prioritizing a seamless, single-page experience.

*   **`page.tsx`**: The master dashboard component. It manages all React state (`scanMode`, `findings`, `fixResult`), handles the tabbed UI switching (Snippet/GitHub/ZIP), dynamically colors severity badges, and renders the unified diff outputs.
*   **`globals.css`**: Configures Tailwind CSS and handles custom application-wide styling (like the dark mode background and scrollbars).

---

## Part 3: The "How" (Implementation Journey)

This outlines the exact steps and problem-solving journey taken to build this platform from scratch.

**Phase 1: The Deterministic Scanner**
*   Built the AST scanner engine to replace basic regex.
*   Created modular rules for Command Injection, SQL Injection, `eval()`, and Hardcoded Secrets.

**Phase 2: The Full-Stack Foundation**
*   Set up FastAPI and Next.js.
*   Created the SQLite database with SQLAlchemy to track `Scans` and `Findings`.
*   Built the basic UI to accept a raw code snippet and display the vulnerabilities in cards with dynamic severity coloring (Critical = Red, Low = Blue).

**Phase 3: The AI Integration & Prompt Engineering**
*   Integrated Ollama (`phi3`).
*   Built the `/explain` endpoint to generate human-readable risk assessments.
*   Built the `/fix` endpoint using prompt engineering to force the LLM to return strictly patched code without markdown formatting.

**Phase 4: Diff Generation & Validation (The "Enterprise" Features)**
*   Implemented `difflib` to generate Git-style Unified Diffs (showing red `-` removals and green `+` additions).
*   Built the **Validation Pipeline** to catch AI hallucinations. If the AI hallucinates, the status updates to `SYNTAX_ERROR` or `REGRESSION_DETECTED` instead of `FIX_GENERATED`.

**Phase 5: Scaling to Repositories & System Optimization**
*   Upgraded the system from single-snippet scanning to massive multi-file scanning.
*   Implemented `POST /scan/github` to clone remote repos to isolated temporary directories.
*   Implemented `POST /scan/zip` using `FormData` for local project uploads.
*   **Critical Fix - Context Cropping:** Discovered that large files froze the local AI. Implemented logic to slice +/- 15 lines around the vulnerability before sending it to Ollama.
*   **Critical Fix - Caching:** Discovered the AI was regenerating fixes on every click. Implemented database caching so subsequent clicks on `/explain` or `/fix` load instantly from SQLite.
*   **Critical Fix - Environment:** Diagnosed and bypassed WSL 1 Node.js path limitations and resolved detached Ollama background processes blocking port `11434`.

---

## Part 4: Data Flow (The Life of a Scan)

To understand how all these files work together, here is the lifecycle of a single user request:

1.  **Ingestion:** The user pastes a GitHub URL in `page.tsx` and clicks Scan. The frontend sends a JSON payload to `main.py` (`POST /api/v1/scan/github`).
2.  **Processing:** `main.py` passes the URL to `project_service.py`, which clones the repo into a temporary folder and finds all `.py` files.
3.  **Scanning:** `main.py` sends the files to `scanners/engine.py`. The engine converts the code to an AST and runs it against the rules in `scanners/rules/`.
4.  **Storage:** Findings are saved to the SQLite database via the SQLAlchemy models in `db/`. The backend returns the findings to the Next.js UI.
5.  **Remediation Request:** The user clicks "Fix with AI". `page.tsx` calls `POST /findings/{id}/fix`.
6.  **Context Extraction:** `main.py` pulls the specific vulnerable code from the DB, crops it to a maximum of 30 lines, and sends it to `ai/`.
7.  **AI & Validation:** Ollama generates a fix. `validation_service.py` intercepts it, tests the syntax, and rescans it for regressions.
8.  **Diffing & Delivery:** `diff_service.py` creates the visual diff, saves it to the DB, and returns it to `page.tsx` where it renders in green and red on the dashboard.