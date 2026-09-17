from datetime import datetime
from sqlalchemy import ForeignKey, String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    # Store source code so findings can reference their context
    code: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="scan")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"))
    rule_id: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    line: Mapped[int] = mapped_column(Integer, nullable=False)
    file: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="OPEN")
    source: Mapped[str] = mapped_column(String, nullable=True)
    sink: Mapped[str] = mapped_column(String, nullable=True)
    ai_explanation: Mapped[str] = mapped_column(Text, nullable=True)
    # NEW: Store the specific file's code so the AI Remediation engine has context
    vulnerable_code: Mapped[str] = mapped_column(Text, nullable=True)

    scan: Mapped["Scan"] = relationship("Scan", back_populates="findings")
    remediations: Mapped[list["Remediation"]] = relationship("Remediation", back_populates="finding")


class Remediation(Base):
    __tablename__ = "remediations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"))
    original_code: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_code: Mapped[str] = mapped_column(Text, nullable=False)
    unified_diff: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    finding: Mapped["Finding"] = relationship("Finding", back_populates="remediations")