from typing import List, Optional
from pydantic import BaseModel, Field


class ValidationViolation(BaseModel):
    severity: str = Field(..., description="error, warning, or info")
    rule_category: str
    check_failed: str
    description: str
    suggestion: str
    line_reference: Optional[str] = None


class CompliantRule(BaseModel):
    rule_category: str
    checks_passed: List[str]


class ValidationResult(BaseModel):
    overall_status: str = Field(..., description="pass, warning, or fail")
    overall_score: int
    summary: str
    violations: List[ValidationViolation]
    compliant_rules: List[CompliantRule]
