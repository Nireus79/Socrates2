"""
Insights endpoint - Project analysis: gaps, risks, opportunities.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..models.project import Project
from ..models.specification import Specification
from ..models.user import User

router = APIRouter(prefix="/api/v1/insights", tags=["insights"])


class Insight(BaseModel):
    """Single insight item."""
    type: str  # 'gap', 'risk', 'opportunity'
    title: str
    description: str
    severity: str  # 'low', 'medium', 'high'
    category: Optional[str] = None
    recommendations: List[str]


class InsightSummary(BaseModel):
    """Summary statistics for insights."""
    total_insights: int
    gaps_count: int
    risks_count: int
    opportunities_count: int
    coverage_percentage: float
    most_covered_category: Optional[str] = None
    least_covered_category: Optional[str] = None


class InsightsResponse(BaseModel):
    """Response model for insights endpoint."""
    success: bool
    project_id: str
    project_name: str
    insights: List[Insight]
    summary: InsightSummary


# List of expected specification categories for gap analysis
EXPECTED_CATEGORIES = [
    "goals",
    "requirements",
    "tech_stack",
    "scalability",
    "security",
    "performance",
    "testing",
    "monitoring",
    "data_retention",
    "disaster_recovery"
]


@router.get("/{project_id}", response_model=InsightsResponse)
def get_insights(
    project_id: str,
    insight_type: Optional[str] = Query(None, description="Filter by type: gaps, risks, opportunities, all"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> InsightsResponse:
    """
    Get project insights including gaps, risks, and opportunities.

    Args:
        project_id: Project UUID
        insight_type: Optional filter (gaps, risks, opportunities)
        current_user: Authenticated user
        db: Database session

    Returns:
        InsightsResponse with insights list and summary

    Example:
        GET /api/v1/insights/proj-123?insight_type=gaps
        Authorization: Bearer <token>
    """
    # 1. Get project with authorization check
    project = db.query(Project).where(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # 2. Get specifications and analyze coverage
    specs = db.query(Specification).where(
        Specification.project_id == project_id,
        Specification.is_current == True
    ).all()

    # Count specifications by category
    specs_by_category = {}
    for spec in specs:
        category = spec.category
        specs_by_category[category] = specs_by_category.get(category, 0) + 1

    # 3. Generate insights
    insights = []

    # Gaps: Missing categories
    if not insight_type or insight_type == "gaps":
        for category in EXPECTED_CATEGORIES:
            if category not in specs_by_category or specs_by_category[category] == 0:
                gap_insight = Insight(
                    type="gap",
                    title=f"Missing {category.replace('_', ' ')} specifications",
                    description=f"No {category.replace('_', ' ')} requirements defined for project",
                    severity="high" if category in ["security", "testing"] else "medium",
                    category=category,
                    recommendations=[
                        f"Define {category.replace('_', ' ')} requirements",
                        f"Review industry best practices for {category.replace('_', ' ')}",
                        "Document all assumptions and constraints"
                    ]
                )
                insights.append(gap_insight)

    # Risks: Low confidence specs
    if not insight_type or insight_type == "risks":
        low_confidence_specs = [s for s in specs if s.confidence and float(s.confidence) < 0.7]
        if low_confidence_specs:
            risk_insight = Insight(
                type="risk",
                title="Low confidence specifications",
                description=f"Found {len(low_confidence_specs)} specifications with low confidence scores",
                severity="medium",
                category=None,
                recommendations=[
                    "Review and validate low-confidence specifications",
                    "Update specifications with more detail",
                    "Conduct additional analysis or research"
                ]
            )
            insights.append(risk_insight)

    # Opportunities: Areas with many specs that could be optimized
    if not insight_type or insight_type == "opportunities":
        well_covered = {cat: count for cat, count in specs_by_category.items() if count >= 5}
        if well_covered:
            opp_insight = Insight(
                type="opportunity",
                title="Well-specified areas ready for implementation",
                description=f"Categories {list(well_covered.keys())} have detailed specifications",
                severity="low",  # Severity doesn't apply to opportunities
                category=None,
                recommendations=[
                    "Prioritize implementation of well-specified areas",
                    "Use detailed specifications to guide development",
                    "Consider sharing specifications with development team"
                ]
            )
            insights.append(opp_insight)

    # 4. Calculate coverage statistics
    covered_categories = len([c for c in EXPECTED_CATEGORIES if c in specs_by_category and specs_by_category[c] > 0])
    coverage_percentage = (covered_categories / len(EXPECTED_CATEGORIES)) * 100

    most_covered = max(specs_by_category.items(), key=lambda x: x[1])[0] if specs_by_category else None
    least_covered = min(
        (cat for cat in EXPECTED_CATEGORIES if cat not in specs_by_category or specs_by_category[cat] == 0),
        default=None
    )

    summary = InsightSummary(
        total_insights=len(insights),
        gaps_count=len([i for i in insights if i.type == "gap"]),
        risks_count=len([i for i in insights if i.type == "risk"]),
        opportunities_count=len([i for i in insights if i.type == "opportunity"]),
        coverage_percentage=round(coverage_percentage, 1),
        most_covered_category=most_covered,
        least_covered_category=least_covered
    )

    return InsightsResponse(
        success=True,
        project_id=str(project.id),
        project_name=project.name,
        insights=insights,
        summary=summary
    )
