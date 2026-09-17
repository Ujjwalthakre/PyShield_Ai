# 🛡️ PyShield AI

> **Deterministic Python security scanning + local AI-powered remediation.**

PyShield AI is a comprehensive security scanning and AI-driven remediation platform for Python codebases.

Unlike conventional LLM wrappers that blindly send entire source files to an external API, PyShield AI combines **deterministic Python AST analysis** with **local AI models through Ollama** to identify vulnerabilities, explain security issues, and propose fixes while keeping source code on-device.

Every AI-generated remediation passes through an automated validation pipeline before it is presented to the developer, helping prevent invalid Python, ineffective patches, and regressions.

---

## ✨ Features

### 🔍 Deterministic AST Security Scanning

PyShield AI uses Python's built-in `ast` module instead of relying on regex-based source scanning.

The scanner can identify patterns associated with:

* Command injection
* `eval()` / `exec()` usage
* SQL injection
* Hardcoded secrets
* Other dangerous Python constructs through modular security rules

The scanner operates directly on Python's syntax tree, allowing rules to reason about actual Python constructs rather than simple text matches.

### 🤖 Offline AI Remediation

PyShield AI integrates with **Ollama** and a locally hosted `phi3` model.

This provides:

* Local source-code processing
* No requirement to upload proprietary code to a third-party LLM API
* AI-generated explanations
* AI-generated remediation suggestions
* Prompt-engineered security context

> **Note:** Running an AI model locally still requires the appropriate hardware/resources for the selected model.

### 📦 Multiple Input Sources

PyShield AI supports multiple ways to provide Python code:

* Raw Python snippets
* Local `.zip` project archives
* Public GitHub repositories

For GitHub repositories, the backend can clone the repository before scanning its Python files.

### ✂️ Smart Context Cropping

Instead of sending an entire source file to the AI model, PyShield extracts a focused context window around the vulnerability.

The remediation pipeline uses approximately:

```text
15 lines before the vulnerability
+
vulnerable code
+
15 lines after the vulnerability
```

This keeps prompts focused and helps avoid unnecessarily large LLM contexts when scanning large projects.

### 🛡️ Dual-Gate AI Validation

AI-generated fixes are not returned blindly.

Every proposed remediation goes through two validation stages.

#### Gate 1 — Syntax Validation

The generated Python is parsed using:

```python
ast.parse()
```

If the AI response produces invalid Python syntax, it is rejected.

#### Gate 2 — Security Regression Validation

The proposed fix is scanned again in memory using the deterministic security scanner.

The system checks whether the original vulnerability is still detected.

Only fixes that pass the validation pipeline are eligible to be returned to the developer.

### 📄 Git-Style Unified Diffs

PyShield AI generates unified diffs using Python's `difflib`.

Instead of simply returning an entire modified file, the interface can display the exact changes:

```diff
- vulnerable_code()
+ secure_code()
```

This makes security remediation easier to review.

### ⚡ Response Caching

AI explanations and remediation results can be cached locally.

Repeated identical requests can therefore avoid unnecessary model inference and return previously generated results much faster.

---

# 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │     Next.js UI       │
                         │   React + Tailwind   │
                         └──────────┬───────────┘
                                    │
                                    │ HTTP API
                                    ▼
                         ┌──────────────────────┐
                         │      FastAPI         │
                         │       Backend       │
                         └──────────┬───────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │ Project      │  │ AST Security │  │   SQLite /   │
          │ Ingestion    │  │ Scanner      │  │  SQLAlchemy  │
          └──────┬───────┘  └──────┬───────┘  └──────────────┘
                 │                 │
                 │                 ▼
                 │          ┌──────────────┐
                 │          │ Vulnerability│
                 │          │   Findings   │
                 │          └──────┬───────┘
                 │                 │
                 │                 ▼
                 │          ┌──────────────┐
                 └─────────►│   Context    │
                            │   Cropping    │
                            └──────┬───────┘
                                   │
                                   ▼
                            ┌──────────────┐
                            │   Ollama +   │
                            │    phi3      │
                            └──────┬───────┘
                                   │
                                   ▼
                            ┌──────────────┐
                            │ Validation   │
                            │    Gates     │
                            └──────┬───────┘
                                   │
                         ┌─────────┴─────────┐
                         │                   │
                         ▼                   ▼
                  Syntax Validation   Regression Scan
                         │                   │
                         └─────────┬─────────┘
                                   ▼
                            ┌──────────────┐
                            │ Unified Diff │
                            └──────┬───────┘
                                   │
                                   ▼
                            ┌──────────────┐
                            │   Next.js    │
                            │   Dashboard  │
                            └──────────────┘
```

---

# 🔄 Remediation Data Flow

The complete remediation pipeline follows these stages:

### 1. Ingest

The backend accepts one of the supported project sources:

```text
Raw Python
ZIP archive
GitHub repository
```

GitHub repositories are cloned and ZIP archives are extracted before scanning.

### 2. Scan

The AST engine traverses Python files and applies the configured security rules.

```text
Python Source
      │
      ▼
   ast.parse()
      │
      ▼
AST Traversal
      │
      ▼
Security Rules
      │
      ▼
Vulnerability Findings
```

### 3. Crop Context

When a vulnerability is identified, PyShield extracts a focused source-code window around the vulnerable line.

```text
         Full Source File
┌─────────────────────────────────┐
│                                 │
│          unrelated code         │
│                                 │
│          unrelated code         │
│                                 │
│ ───── context begins ─────────  │
│                                 │
│       vulnerable code           │
│                                 │
│ ───── context ends ───────────  │
│                                 │
│          unrelated code         │
│                                 │
└─────────────────────────────────┘
```

Approximately 15 lines above and below the vulnerability are included in the AI context.

### 4. Prompt

The cropped context is passed to the local Ollama model together with security-focused instructions.

### 5. Generate

The local `phi3` model generates:

* An explanation of the vulnerability
* A proposed remediation
* Updated source code or remediation output

### 6. Syntax Gate

The generated Python is parsed using `ast.parse()`.

```text
AI Response
    │
    ▼
ast.parse()
    │
 ┌──┴──┐
 │     │
Valid Invalid
 │     │
 ▼     ▼
Next  Reject
```

### 7. Regression Gate

The proposed code is scanned again using the same deterministic security engine.

The system verifies that the vulnerability is no longer detected.

### 8. Diff Generation

A unified diff is generated with Python's `difflib`.

### 9. Deliver

The validated remediation and diff are returned to the Next.js dashboard.

---

# 🧰 Tech Stack

## Frontend

| Technology   | Purpose                   |
| ------------ | ------------------------- |
| Next.js 14   | Web application framework |
| React        | UI                        |
| Tailwind CSS | Styling                   |
| TypeScript   | Frontend development      |

## Backend

| Technology   | Purpose                        |
| ------------ | ------------------------------ |
| FastAPI      | REST API                       |
| Python 3.10+ | Backend runtime                |
| Python `ast` | Deterministic source analysis  |
| SQLAlchemy   | ORM                            |
| SQLite       | Local database                 |
| Pydantic     | API validation                 |
| `difflib`    | Unified diff generation        |
| Subprocess   | Git/Ollama process integration |

## AI

| Technology | Purpose                 |
| ---------- | ----------------------- |
| Ollama     | Local LLM runtime       |
| `phi3`     | Local remediation model |

---

# 📂 Project Structure

```text
pyshield-ai/
│
├── backend/
│   │
│   ├── app/
│   │   │
│   │   ├── ai/
│   │   │   └── # AI provider integrations
│   │   │
│   │   ├── db/
│   │   │   └── # Database models and session management
│   │   │
│   │   ├── scanners/
│   │   │   │
│   │   │   ├── rules/
│   │   │   │   ├── command_injection.py
│   │   │   │   ├── eval_exec.py
│   │   │   │   ├── hardcoded_secrets.py
│   │   │   │   └── sql_injection.py
│   │   │   │
│   │   │   ├── base.py
│   │   │   ├── engine.py
│   │   │   └── models.py
│   │   │
│   │   ├── schemas/
│   │   │   └── scan.py
│   │   │
│   │   ├── services/
│   │   │   ├── diff_service.py
│   │   │   ├── project_service.py
│   │   │   └── validation_service.py
│   │   │
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   │
│   ├── src/
│   │   └── app/
│   │       ├── page.tsx
│   │       ├── layout.tsx
│   │       └── globals.css
│   │
│   ├── tailwind.config.ts
│   ├── package.json
│   └── ...
│
└── README.md
```

---

# 🚀 Getting Started

## Prerequisites

Before installing PyShield AI, make sure you have the following installed:

* Linux or WSL 2
* Python 3.10+
* Node.js 20+
* npm
* Git
* Ollama

You will also need enough system resources to run the selected local LLM.

---

# 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd pyshield-ai
```

Replace `<YOUR_REPOSITORY_URL>` with the URL of your GitHub repository.

---

# 2. Start Ollama

Install Ollama for your operating system, then pull/run the `phi3` model.

```bash
ollama run phi3
```

Keep Ollama available while using PyShield AI.

You can verify that Ollama is responding before starting the application.

---

# 3. Setup the FastAPI Backend

Open a terminal and navigate to the backend:

```bash
cd backend
```

Create a Python virtual environment:

### Linux / WSL

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

---

## Install Backend Dependencies

PyShield AI includes a `requirements.txt` file containing the backend dependencies.

Install everything with:

```bash
pip install -r requirements.txt
```

If you are setting up the project without the requirements file, the core dependencies include:

```bash
pip install fastapi uvicorn sqlalchemy pydantic python-multipart
```

---

## Start the Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The API should be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is typically available at:

```text
http://127.0.0.1:8000/docs
```

---

# 4. Setup the Next.js Frontend

Open another terminal.

From the project root:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The dashboard should be available at:

```text
http://localhost:3000
```

---

# 🖥️ Running the Complete Application

PyShield AI requires three components to be available:

### Terminal 1 — Ollama

```bash
ollama run phi3
```

### Terminal 2 — FastAPI

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Terminal 3 — Next.js

```bash
cd frontend
npm run dev
```

Then open:

```text
http://localhost:3000
```

---

# 🔐 Supported Security Rules

PyShield AI uses a modular rule architecture.

Current rule modules include:

```text
backend/app/scanners/rules/
├── command_injection.py
├── eval_exec.py
├── hardcoded_secrets.py
└── sql_injection.py
```

Each rule can inspect the Python AST and report security findings through the scanner's common rule interface.

This architecture makes it possible to add additional security rules without rewriting the scanning engine.

---

# 🧠 Why AST-Based Scanning?

Traditional regex-based scanners search for text patterns.

For example:

```python
eval(
```

However, source code is structured, and the same security-relevant operation can appear in different syntactic forms.

PyShield AI instead parses Python into an Abstract Syntax Tree:

```text
Python Source
      │
      ▼
   AST Parser
      │
      ▼
Abstract Syntax Tree
      │
      ▼
Security Rules
      │
      ▼
Findings
```

This gives individual security rules access to structured Python constructs such as:

* Function calls
* Imports
* Assignments
* Constants
* Expressions
* Arguments
* Attribute access

The result is a scanner architecture that is easier to extend than a collection of regular expressions.

> **Important:** No static analyzer can guarantee zero false positives or zero false negatives across arbitrary Python programs. PyShield's AST approach is designed to make its configured rules deterministic and structurally aware; the actual detection quality depends on each rule's implementation and scope.

---

# 🤖 Why Local AI?

PyShield AI is designed around the principle that source code should remain local whenever possible.

Traditional cloud-based AI remediation commonly follows:

```text
Source Code
    │
    ▼
External API
    │
    ▼
LLM
    │
    ▼
Suggested Fix
```

PyShield instead uses:

```text
Source Code
    │
    ▼
Local Backend
    │
    ▼
Ollama
    │
    ▼
Local LLM
    │
    ▼
Suggested Fix
```

This can be particularly useful when working with proprietary or sensitive code that should not be sent to an external AI provider.

---

# 🛡️ AI Safety Pipeline

AI-generated code should not automatically be considered correct.

PyShield therefore treats the LLM as a remediation assistant rather than the final authority.

```text
                  AI Generated Fix
                         │
                         ▼
                 ┌───────────────┐
                 │ Syntax Gate   │
                 │   ast.parse   │
                 └───────┬───────┘
                         │
                    Valid Python?
                    /          \
                  NO            YES
                  │              │
                  ▼              ▼
               Reject      Regression Gate
                                │
                                ▼
                         Run Security Scan
                                │
                         Vulnerability Gone?
                           /           \
                         NO             YES
                         │               │
                         ▼               ▼
                      Reject          Accept
                                         │
                                         ▼
                                  Generate Diff
                                         │
                                         ▼
                                   Return Result
```

This approach provides a deterministic verification layer around probabilistic AI output.

---

# 📊 Unified Diff Example

Instead of returning an opaque AI response, PyShield can present changes in a Git-style format.

Example:

```diff
- result = eval(user_input)
+ result = ast.literal_eval(user_input)
```

The developer can then review exactly what changed before applying the remediation.

---

# 💾 Caching

PyShield AI supports local caching of AI-generated explanations and remediation results.

The goal is to avoid repeatedly invoking the local model for identical requests.

Conceptually:

```text
Request
   │
   ▼
Cache Lookup
   │
 ┌─┴──────────────┐
 │                │
Cache Hit      Cache Miss
 │                │
 ▼                ▼
Return         Ollama
Result            │
                  ▼
               Validate
                  │
                  ▼
              Store Cache
                  │
                  ▼
               Return
```

This can significantly reduce repeated inference time during development.

---

# 🧪 Validation Philosophy

PyShield AI follows a layered security model:

```text
┌─────────────────────────────┐
│       Developer Code        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│    Deterministic Scanner    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       AI Remediation        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      Syntax Validation      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│    Security Regression      │
│          Scan               │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Unified Diff          │
└─────────────────────────────┘
```

The AI is therefore positioned between deterministic detection and deterministic validation.

---

# 📡 API

The backend is powered by FastAPI.

When the backend is running, interactive API documentation is available through:

```text
http://127.0.0.1:8000/docs
```

The exact available endpoints depend on the implementation in:

```text
backend/app/main.py
```

Pydantic schemas used by the API are located under:

```text
backend/app/schemas/
```

---

# 🧩 Extending PyShield AI

One of the project's goals is to make security rules modular.

To add a new rule:

1. Create a rule inside:

```text
backend/app/scanners/rules/
```

2. Implement the required rule interface from:

```text
backend/app/scanners/base.py
```

3. Add the rule to the scanner configuration/registration used by:

```text
backend/app/scanners/engine.py
```

4. Test the rule against vulnerable and non-vulnerable examples.

Example future rules could cover:

```text
Path Traversal
Insecure Deserialization
Weak Cryptography
SSRF
Insecure Temporary Files
Unsafe YAML Loading
Weak Password Hashing
Insecure HTTP Usage
JWT Misconfiguration
```

---

# 🧪 Recommended Development Workflow

A typical development workflow looks like this:

```text
1. Write Python code
       ↓
2. Run PyShield scan
       ↓
3. Review findings
       ↓
4. Request AI remediation
       ↓
5. AI generates proposed fix
       ↓
6. Syntax validation
       ↓
7. Security regression scan
       ↓
8. Review unified diff
       ↓
9. Apply changes
       ↓
10. Re-scan project
```

---

# ⚠️ Security Considerations

PyShield AI is intended to assist developers with identifying and remediating security issues. It should not be treated as a replacement for a complete application security program.

Keep in mind:

* Static analysis has inherent limitations.
* Security rules only detect patterns they are explicitly designed to recognize.
* AI-generated fixes can still be incomplete or inappropriate.
* Passing the configured validation gates does not prove that code is secure.
* Developers should review proposed patches before applying them.
* Dependency vulnerabilities require separate dependency/security scanning.
* Runtime behavior may differ from static-analysis results.
* Local AI models may produce incorrect explanations or remediation suggestions.

For production security programs, PyShield should be used alongside appropriate testing, code review, dependency scanning, secret management, and other security controls.

---

# 🔒 Privacy

PyShield AI is designed to support local code analysis and local AI remediation.

With Ollama running locally:

```text
Python Code
     │
     ▼
PyShield Backend
     │
     ▼
Local Ollama
     │
     ▼
Local Model
```

Source-code context used for remediation can therefore remain within the local environment rather than being sent to a third-party hosted LLM API.

Actual privacy characteristics also depend on the surrounding environment, configuration, operating system, network setup, and any external integrations you add.

---

# 🛠️ Troubleshooting

## Ollama is not responding

Make sure Ollama is installed and running.

Then try:

```bash
ollama run phi3
```

---

## Backend command fails

Make sure the virtual environment is activated:

```bash
source venv/bin/activate
```

Then reinstall dependencies:

```bash
pip install -r requirements.txt
```

Start the server again:

```bash
uvicorn app.main:app --reload
```

---

## Frontend dependencies are missing

From the frontend directory:

```bash
npm install
```

Then:

```bash
npm run dev
```

---

## Port 8000 is already in use

Start FastAPI on another port:

```bash
uvicorn app.main:app --reload --port 8001
```

If the frontend expects a specific backend URL, update the corresponding frontend/API configuration accordingly.

---

## Port 3000 is already in use

Next.js can be started on another port:

```bash
npm run dev -- -p 3001
```

---

# 🗺️ Roadmap

Potential future improvements include:

* [ ] Additional AST security rules
* [ ] More comprehensive taint/data-flow analysis
* [ ] Dependency vulnerability scanning
* [ ] Configurable security rule severity
* [ ] SARIF report generation
* [ ] CI/CD integration
* [ ] GitHub Actions integration
* [ ] Pull request remediation workflows
* [ ] Multi-model Ollama support
* [ ] User-selectable local models
* [ ] Improved AI patch validation
* [ ] Test generation for proposed fixes
* [ ] Automatic unit-test execution
* [ ] Security scan history
* [ ] Project-level dashboards
* [ ] Authentication and role-based access control

---

# 🤝 Contributing

Contributions are welcome.

To contribute:

```bash
git clone <YOUR_REPOSITORY_URL>
cd pyshield-ai
```

Create a branch:

```bash
git checkout -b feature/your-feature
```

Make your changes, test them, and commit:

```bash
git add .
git commit -m "Add your feature"
```

Push your branch:

```bash
git push origin feature/your-feature
```

Then open a Pull Request on GitHub.

When contributing security rules, please include representative vulnerable and non-vulnerable examples where possible.

---

# 📜 License

Add your preferred license to the repository.

For example:

```text
MIT License
```

If using MIT, add a `LICENSE` file containing the official MIT license text.

---

# 👨‍💻 Project Overview

PyShield AI combines three ideas into a single developer security workflow:

```text
             ┌─────────────────────┐
             │ Deterministic AST   │
             │       Scanner       │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │ Local AI Remediation│
             │   Ollama + phi3     │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │ Automated Validation│
             │ Syntax + Regression │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │ Developer-Friendly  │
             │    Unified Diff     │
             └─────────────────────┘
```

**PyShield AI** is built to make Python security analysis more deterministic, remediation more private, and AI-generated fixes easier to validate and review.

---

## ⭐ If you find PyShield AI useful

Consider giving the repository a ⭐ on GitHub and contributing security rules, improvements, documentation, or integrations.

---

## 📌 Quick Start

For experienced users:

```bash
# Clone
git clone <YOUR_REPOSITORY_URL>
cd pyshield-ai

# Terminal 1 - Ollama
ollama run phi3

# Terminal 2 - Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 3 - Frontend
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

API:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```
