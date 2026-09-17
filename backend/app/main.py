import os
import ast
import time
import shutil
import tempfile
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.scan import ScanRequest, ScanResponse, FindingSchema, ExplainResponse, StatusUpdateResponse, FixResponse, ValidationResponse
from app.scanners.engine import ScannerEngine
from app.scanners.rules.eval_exec import EvalRule
from app.scanners.rules.sql_injection import SQLInjectionRule
from app.scanners.rules.command_injection import CommandInjectionRule
from app.scanners.rules.hardcoded_secrets import HardcodedSecretsRule

from app.db.database import engine, Base, SessionLocal
from app.db.models import Scan, Finding, Remediation
from app.ai.ollama_provider import OllamaProvider

from app.services.diff_service import generate_unified_diff
from app.services.validation_service import ValidationPipeline
from app.schemas.scan import GitHubScanRequest
from app.services.project_service import clone_repo, extract_zip, find_python_files

from fastapi.middleware.cors import CORSMiddleware

# 1. Initialize database tables
Base.metadata.create_all(bind=engine)

# 2. Dependency to get DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. Initialize FastAPI and components
app = FastAPI(
    title="PyShield AI API",
    description="AI-Powered Python Code Security Scanner",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Allow Next.js frontend
    allow_credentials=True,
    allow_methods=["*"], # Allow GET, POST, PATCH, etc.
    allow_headers=["*"],
)


active_rules = [
    EvalRule(),
    SQLInjectionRule(),
    CommandInjectionRule(),
    HardcodedSecretsRule()
]
scanner = ScannerEngine(rules=active_rules)
validation_pipeline = ValidationPipeline(scanner_engine=scanner)
ai_provider = OllamaProvider(model_name="phi3")

def _process_multi_file_scan(source_name: str, files_dict: dict, db: Session):
    db_scan = Scan(file_name=source_name, code="MULTI_FILE_WORKSPACE")
    db.add(db_scan)
    db.flush()

    api_findings = []
    for rel_path, content in files_dict.items():
        try:
            raw_findings = scanner.scan(code=content, file_path=rel_path)
            for f in raw_findings:
                db_finding = Finding(
                    scan_id=db_scan.id,
                    rule_id=f.rule_id,
                    severity=f.severity,
                    message=f.message,
                    line=f.line,
                    file=f.file,
                    status="OPEN",
                    source=f.source,
                    sink=f.sink,
                    vulnerable_code=content  # Save the code of just this file
                )
                db.add(db_finding)
                api_findings.append(
                    FindingSchema(
                        rule_id=f.rule_id, severity=f.severity, message=f.message,
                        line=f.line, file=f.file, source=f.source, sink=f.sink
                    )
                )
        except SyntaxError:
            pass # Skip files with invalid Python syntax during bulk scans

    db.commit()
    return ScanResponse(status="success", total_findings=len(api_findings), findings=api_findings)


@app.get("/api/v1/health")
def health_check():
    return {"status": "online", "message": "PyShield AI is running.", "version": "1.0.0"}


@app.post("/api/v1/scan", response_model=ScanResponse)
def run_scan(request: ScanRequest, db: Session = Depends(get_db)):
    try:
        raw_findings = scanner.scan(code=request.code, file_path=request.file_name)

        # Persist scan to Database
        db_scan = Scan(file_name=request.file_name, code=request.code)
        db.add(db_scan)
        db.flush()  # Populates db_scan.id before commit

        api_findings = []
        for f in raw_findings:
            db_finding = Finding(
                scan_id=db_scan.id,
                rule_id=f.rule_id,
                severity=f.severity,
                message=f.message,
                line=f.line,
                file=f.file,
                source=f.source,
                sink=f.sink,
                status="OPEN"
            )
            db.add(db_finding)
            api_findings.append(
                FindingSchema(
                    rule_id=f.rule_id,
                    severity=f.severity,
                    message=f.message,
                    line=f.line,
                    file=f.file,
                    source=f.source,
                    sink=f.sink
                )
            )

        db.commit()

        return ScanResponse(
            status="success",
            total_findings=len(api_findings),
            findings=api_findings
        )
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Python syntax: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v1/findings/{finding_id}/explain", response_model=ExplainResponse)
def explain_finding(finding_id: int, db: Session = Depends(get_db)):
    # 1. Lookup finding in database
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    # 2. Check cache: return stored explanation if already generated
    if finding.ai_explanation:
        return ExplainResponse(
            finding_id=finding.id,
            rule_id=finding.rule_id,
            explanation=finding.ai_explanation,
            cached=True
        )

    # 3. Context Cropping (Prevents LLM overload on large repository files)
    # Fallback to the comment string only if the vulnerable_code wasn't saved
    original_code = finding.vulnerable_code if finding.vulnerable_code else f"# File: {finding.file} (Line {finding.line})\n# Issue: {finding.message}"
    
    code_lines = original_code.splitlines()
    if len(code_lines) > 30:
        target_idx = finding.line - 1
        # Extract +/- 15 lines around the vulnerable line
        start = max(0, target_idx - 15)
        end = min(len(code_lines), target_idx + 15)
        ai_input_code = "\n".join(code_lines[start:end])
    else:
        ai_input_code = original_code

    # 4. Generate explanation using our AI provider
    explanation_text = ai_provider.explain_finding(
        code_snippet=ai_input_code,
        rule_id=finding.rule_id,
        message=finding.message
    )

    # 5. Save explanation to database
    finding.ai_explanation = explanation_text
    db.commit()

    return ExplainResponse(
        finding_id=finding.id,
        rule_id=finding.rule_id,
        explanation=explanation_text,
        cached=False
    )

@app.patch("/api/v1/findings/{finding_id}/status", response_model=StatusUpdateResponse)
def update_finding_status(finding_id: int, new_status: str, db: Session = Depends(get_db)):
    # 1. Lookup finding in database
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    # 2. Update status
    finding.status = new_status
    db.commit()

    return StatusUpdateResponse(
        finding_id=finding.id,
        updated_status=new_status,
    )


@app.post("/api/v1/findings/{finding_id}/fix", response_model=FixResponse)
def generate_fix(finding_id: int, db: Session = Depends(get_db)):
    # 1. Look up finding & associated scan
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    parent_scan = db.query(Scan).filter(Scan.id == finding.scan_id).first()
    # original_code = parent_scan.code if parent_scan and parent_scan.code else f"# File: {finding.file} line {finding.line}"
    original_code = finding.vulnerable_code if finding.vulnerable_code else f"# File: {finding.file} line {finding.line}"

    # --- NEW: CONTEXT CROPPING ---
    # If the file is massive, extract only +/- 15 lines around the vulnerability
    # so the local AI model doesn't freeze.
    code_lines = original_code.splitlines()
    if len(code_lines) > 30:
        target_idx = finding.line - 1
        start = max(0, target_idx - 15)
        end = min(len(code_lines), target_idx + 15)
        ai_input_code = "\n".join(code_lines[start:end])
    else:
        ai_input_code = original_code
    # -----------------------------


    # --- CACHE CHECK ---
    existing_remediation = db.query(Remediation).filter(Remediation.finding_id == finding.id).order_by(Remediation.id.desc()).first()
    if existing_remediation:    
        return FixResponse(
            finding_id=finding.id,
            rule_id=finding.rule_id,
            original_code=existing_remediation.original_code,
            proposed_code=existing_remediation.proposed_code,
            diff=existing_remediation.unified_diff,
            status=finding.status
        )
    # ----------------------------

   # --- ADD PRINT STATEMENTS HERE ---
    print(f"\n[DEBUG] Requesting AI fix for finding {finding_id}...")
    print(f"[DEBUG] Cropped code size: {len(ai_input_code.splitlines())} lines.")
    start_time = time.time()
    
    proposed_code = ai_provider.generate_fix(
        code_snippet=ai_input_code,
        rule_id=finding.rule_id,
        message=finding.message
    )
    
    end_time = time.time()
    print(f"[DEBUG] AI finished in {round(end_time - start_time, 2)} seconds.")

    # --- THE VALIDATION PIPELINE (PHASE 13 INTEGRATION) ---
    validation_status = "FIX_VALIDATED"

    # Gate 1: Syntax Validation
    # Checks if the AI hallucinated markdown or wrote broken Python
    try:
        ast.parse(proposed_code)
    except SyntaxError:
        validation_status = "SYNTAX_ERROR"
    
    # Gate 2: Security Regression Validation
    # If syntax is valid, rescan the AI's new code to ensure it actually patched the bug
    if validation_status == "FIX_VALIDATED":
        # We temporarily scan the proposed code in memory
        new_findings = scanner.scan(code=proposed_code, file_path="memory_check.py")
        
        # Check if the original rule_id still exists in the AI's output
        is_still_vulnerable = any(f.rule_id == finding.rule_id for f in new_findings)
        if is_still_vulnerable:
            validation_status = "REGRESSION_DETECTED"
    # ------------------------------------------------------

    # 3. Calculate unified diff
    diff = generate_unified_diff(
        original_code=original_code,
        fixed_code=proposed_code,
        file_name=finding.file
    )

    # 4. Save remediation record & update finding status
    remediation = Remediation(
        finding_id=finding.id,
        original_code=original_code,
        proposed_code=proposed_code,
        unified_diff=diff
    )
    finding.status = "FIX_GENERATED"
    db.add(remediation)
    db.commit()

    return FixResponse(
        finding_id=finding.id,
        rule_id=finding.rule_id,
        original_code=original_code,
        proposed_code=proposed_code,
        diff=diff,
        status=finding.status
    )


@app.post("/api/v1/findings/{finding_id}/validate", response_model=ValidationResponse)
def validate_finding_fix(finding_id: int, db: Session = Depends(get_db)):
    # 1. Fetch finding and latest remediation
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    remediation = (
        db.query(Remediation)
        .filter(Remediation.finding_id == finding_id)
        .order_by(Remediation.id.desc())
        .first()
    )
    if not remediation:
        raise HTTPException(
            status_code=400, 
            detail="No remediation generated for this finding yet. Call /fix first."
        )

    # 2. Run validation pipeline
    result = validation_pipeline.validate_fix(
        proposed_code=remediation.proposed_code,
        original_rule_id=finding.rule_id,
        file_path=finding.file
    )

    # 3. Update finding status in database
    finding.status = result.status
    db.commit()

    return ValidationResponse(
        finding_id=finding.id,
        rule_id=finding.rule_id,
        status=finding.status,
        syntax_valid=result.is_valid_syntax,
        resolved=result.is_resolved,
        message="Vulnerability successfully remediated and verified." if result.is_resolved else result.error_message
    )


@app.post("/api/v1/scan/github", response_model=ScanResponse)
def scan_github(request: GitHubScanRequest, db: Session = Depends(get_db)):
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            clone_repo(request.repo_url, temp_dir)
            files_dict = find_python_files(temp_dir)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to clone repository: {str(e)}")

        return _process_multi_file_scan(source_name=request.repo_url, files_dict=files_dict, db=db)


@app.post("/api/v1/scan/zip", response_model=ScanResponse)
def scan_zip(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .zip archive.")

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "upload.zip")
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        try:
            extract_zip(zip_path, extract_dir)
            files_dict = find_python_files(extract_dir)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract or read zip: {str(e)}")

        return _process_multi_file_scan(source_name=file.filename, files_dict=files_dict, db=db)

