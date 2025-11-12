"""
Base data models for Socrates framework.

Defines core data structures used by analyzers, exporters, and domains.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    """Severity levels for quality issues and conflicts."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    # Also support alternate names
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Question(BaseModel):
    """Represents a question in a domain."""

    question_id: str = Field(..., description="Unique question identifier")
    text: str = Field(..., description="Question text")
    category: str = Field(..., description="Question category")
    difficulty: str = Field(
        default="medium", description="Question difficulty level"
    )
    tags: List[str] = Field(default_factory=list, description="Question tags")
    follow_up_questions: List[str] = Field(
        default_factory=list, description="IDs of follow-up questions"
    )
    examples: List[str] = Field(
        default_factory=list, description="Examples for this question"
    )
    help_text: Optional[str] = Field(
        default=None, description="Additional help text for the question"
    )
    example_answer: Optional[str] = Field(
        default=None, description="Example answer for this question"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="Questions that must be answered first"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return self.model_dump()


class ExportFormat(BaseModel):
    """Represents an export format for specifications."""

    format_id: Optional[str] = Field(default=None, description="Unique format identifier")
    name: Optional[str] = Field(default=None, description="Format name (e.g., Python, JavaScript)")
    description: Optional[str] = Field(default=None, description="Format description")
    file_extension: Optional[str] = Field(default=None, description="File extension (e.g., .py)")
    mime_type: Optional[str] = Field(default=None, description="MIME type (e.g., text/x-python)")
    template_id: Optional[str] = Field(default=None, description="Template ID for this format")
    is_compiled: Optional[bool] = Field(
        default=False, description="Whether format is for compiled languages"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return self.model_dump()


class ConflictRule(BaseModel):
    """Represents a rule for detecting specification conflicts."""

    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    severity: SeverityLevel = Field(
        default=SeverityLevel.MEDIUM, description="Conflict severity level"
    )
    domains: List[str] = Field(
        default_factory=list, description="Domains this rule applies to"
    )
    pattern: str = Field(
        default="", description="Pattern or condition for detecting this conflict"
    )
    condition: Optional[str] = Field(
        default=None, description="Condition for detecting this conflict"
    )
    remediation: str = Field(
        default="", description="Suggested remediation for this conflict"
    )
    message: Optional[str] = Field(
        default=None, description="Message to display when conflict is detected"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        data = self.model_dump()
        # Convert enum to string if present
        if "severity" in data and isinstance(data["severity"], SeverityLevel):
            data["severity"] = data["severity"].value
        return data


class QualityAnalyzer(BaseModel):
    """Represents a quality analyzer for specifications."""

    analyzer_id: str = Field(..., description="Unique analyzer identifier")
    name: str = Field(..., description="Analyzer name")
    description: str = Field(..., description="Analyzer description")
    analyzer_type: str = Field(..., description="Type of analyzer")
    enabled: bool = Field(default=True, description="Whether analyzer is enabled")
    required: bool = Field(
        default=False, description="Whether analyzer is required"
    )
    tags: List[str] = Field(
        default_factory=list, description="Tags for categorizing analyzer"
    )
    config: dict = Field(default_factory=dict, description="Analyzer configuration")

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return self.model_dump()
