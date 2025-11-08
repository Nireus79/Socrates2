"""
Search endpoint - Full-text search across projects, specifications, questions.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User
from ..models.project import Project
from ..models.specification import Specification
from ..models.question import Question

router = APIRouter(prefix="/api/v1/search", tags=["search"])


class SearchResult(BaseModel):
    """A single search result item."""
    resource_type: str  # 'project', 'specification', 'question'
    id: str
    title: str  # name for projects, content[:100] for specs/questions
    preview: str  # Short preview of content
    category: Optional[str] = None
    project_id: Optional[str] = None
    relevance_score: float = 1.0


class SearchResponse(BaseModel):
    """Response model for search endpoint."""
    success: bool
    query: str
    results: List[SearchResult]
    total: int
    skip: int
    limit: int
    resource_counts: Dict[str, int]  # e.g., {"projects": 5, "specifications": 12, "questions": 3}


@router.get("", response_model=SearchResponse)
def search(
    query: str = Query(..., min_length=1, max_length=500, description="Search query"),
    resource_type: Optional[str] = Query(None, description="Filter by type: projects, specifications, questions"),
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> SearchResponse:
    """
    Full-text search across project data.

    Searches:
    - Project names and descriptions
    - Specification content and categories
    - Question text and categories

    Only returns data for projects owned by the current user.

    Args:
        query: Search text (required)
        resource_type: Optional filter (projects, specifications, questions)
        category: Optional category filter
        skip: Pagination offset
        limit: Items per page
        current_user: Authenticated user
        db: Database session

    Returns:
        SearchResponse with results, totals, and counts by type

    Example:
        GET /api/v1/search?query=FastAPI&resource_type=projects&skip=0&limit=20
        Authorization: Bearer <token>
    """
    results = []
    resource_counts = {"projects": 0, "specifications": 0, "questions": 0}

    # Search Projects (if no type filter or type='projects')
    if not resource_type or resource_type == "projects":
        projects_query = db.query(Project).where(
            Project.user_id == current_user.id,
            or_(
                Project.name.ilike(f"%{query}%"),
                Project.description.ilike(f"%{query}%") if Project.description else False
            )
        )
        total_projects = projects_query.count()
        resource_counts["projects"] = total_projects

        projects = projects_query.order_by(Project.created_at.desc()).all()
        for project in projects:
            results.append(SearchResult(
                resource_type="project",
                id=str(project.id),
                title=project.name,
                preview=project.description[:200] if project.description else "",
                category=project.current_phase,
                project_id=str(project.id),
                relevance_score=1.0
            ))

    # Search Specifications (if no type filter or type='specifications')
    if not resource_type or resource_type == "specifications":
        specs_query = db.query(Specification).join(Project).where(
            Project.user_id == current_user.id,
            or_(
                Specification.content.ilike(f"%{query}%"),
                Specification.category.ilike(f"%{query}%") if Specification.category else False
            )
        )

        # Optional: Filter by category if provided
        if category:
            specs_query = specs_query.where(Specification.category == category)

        total_specs = specs_query.count()
        resource_counts["specifications"] = total_specs

        specs = specs_query.order_by(Specification.created_at.desc()).all()
        for spec in specs:
            results.append(SearchResult(
                resource_type="specification",
                id=str(spec.id),
                title=f"[{spec.category}] {spec.content[:100]}",
                preview=spec.content[:200],
                category=spec.category,
                project_id=str(spec.project_id),
                relevance_score=1.0
            ))

    # Search Questions (if no type filter or type='questions')
    if not resource_type or resource_type == "questions":
        questions_query = db.query(Question).join(Project).where(
            Project.user_id == current_user.id,
            or_(
                Question.text.ilike(f"%{query}%"),
                Question.category.ilike(f"%{query}%") if Question.category else False
            )
        )

        # Optional: Filter by category if provided
        if category:
            questions_query = questions_query.where(Question.category == category)

        total_questions = questions_query.count()
        resource_counts["questions"] = total_questions

        questions = questions_query.order_by(Question.created_at.desc()).all()
        for question in questions:
            results.append(SearchResult(
                resource_type="question",
                id=str(question.id),
                title=f"[{question.category}] {question.text[:100]}",
                preview=question.text[:200],
                category=question.category,
                project_id=str(question.project_id),
                relevance_score=1.0
            ))

    # Sort results by recency (can add relevance scoring later)
    results.sort(key=lambda x: x.relevance_score, reverse=True)

    # Apply pagination to combined results
    total = len(results)
    paginated_results = results[skip:skip + limit]

    return SearchResponse(
        success=True,
        query=query,
        results=paginated_results,
        total=total,
        skip=skip,
        limit=limit,
        resource_counts=resource_counts
    )
