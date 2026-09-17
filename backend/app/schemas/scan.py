from pydantic import BaseModel
from typing import List, Optional

# 1. What the user sends to us
class ScanRequest(BaseModel):
    code: str
    file_name: str = "unknown.py"

# 2. What a single finding looks like in JSON
class FindingSchema(BaseModel):
    id: int
    rule_id: str
    severity: str
    message: str
    line: int
    file: str
    source: Optional[str] = ""
    sink: Optional[str] = ""

# 3. What we send back to the user
class ScanResponse(BaseModel):
    status: str
    total_findings: int
    findings: List[FindingSchema]

class ExplainResponse(BaseModel):
    finding_id: int
    rule_id: str
    explanation: str
    cached: bool


class StatusUpdateResponse(BaseModel):
    finding_id: int
    updated_status: str


class FixResponse(BaseModel):
    finding_id: int
    rule_id: str
    original_code: str
    proposed_code: str
    diff: str
    status: str

class ValidationResponse(BaseModel):
    finding_id: int
    rule_id: str
    status: str
    syntax_valid: bool
    resolved: bool
    message: str


class GitHubScanRequest(BaseModel):
    repo_url: str


