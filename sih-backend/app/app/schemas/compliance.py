from typing import Any, Literal

from pydantic import BaseModel, Field


class Declaration(BaseModel):
    field: str
    value: Any
    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )


class Violation(BaseModel):
    # Backward-compatible fields
    field: str = ""
    status: Literal["FAIL", "REVIEW"] = "FAIL"
    reason: str = ""

    # Full Rule Engine information
    rule: str = ""
    issue: str = ""
    expected: str = ""
    detected: Any = None
    severity: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    evidence: str = ""


class ComplianceResponse(BaseModel):
    scan_id: str
    filename: str

    status: Literal["PASS", "FAIL", "REVIEW"]

    declarations: list[Declaration]
    violations: list[Violation]

    message: str