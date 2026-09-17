from dataclasses import dataclass

@dataclass
class Finding:
    rule_id: str
    severity: str
    message: str
    line: int
    file: str = ""
    source: str = ""
    sink: str = ""