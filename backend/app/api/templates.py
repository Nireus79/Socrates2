"""
Templates endpoint - Project templates for quick project setup.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User
from ..models.project import Project
from ..models.specification import Specification

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


class TemplateCategory(BaseModel):
    """Template category details."""
    name: str
    description: str
    examples: List[str]


class Template(BaseModel):
    """A project template."""
    id: str
    name: str
    description: str
    use_case: str
    industry: Optional[str] = None
    categories: List[TemplateCategory]
    estimated_specs: int  # Number of specs this template includes
    difficulty: str  # 'beginner', 'intermediate', 'advanced'
    tags: List[str]


class TemplatesListResponse(BaseModel):
    """Response for list templates endpoint."""
    success: bool
    templates: List[Template]
    total: int
    skip: int
    limit: int


class TemplateDetailResponse(BaseModel):
    """Response for get template detail endpoint."""
    success: bool
    template: Template
    preview_specs: List[Dict[str, str]]  # Sample specifications this template includes


class ApplyTemplateResponse(BaseModel):
    """Response after applying template."""
    success: bool
    project_id: str
    specs_created: int
    message: str


# In-memory template database
AVAILABLE_TEMPLATES = [
    Template(
        id="template-web-app",
        name="Web Application",
        description="Template for building modern web applications",
        use_case="Full-stack web application development",
        industry="SaaS",
        categories=[
            TemplateCategory(
                name="Goals",
                description="Define what the application should accomplish",
                examples=["User authentication", "Real-time updates", "Mobile responsive"]
            ),
            TemplateCategory(
                name="Tech Stack",
                description="Frontend, backend, and infrastructure choices",
                examples=["Frontend framework", "API design pattern", "Database technology"]
            ),
            TemplateCategory(
                name="Security",
                description="Security requirements and best practices",
                examples=["Authentication method", "Data encryption", "Access control"]
            ),
            TemplateCategory(
                name="Performance",
                description="Performance and scalability requirements",
                examples=["Page load time", "Concurrent users", "Data volume"]
            ),
        ],
        estimated_specs=35,
        difficulty="intermediate",
        tags=["web", "saas", "full-stack", "popular"]
    ),
    Template(
        id="template-api",
        name="REST API",
        description="Template for building REST APIs",
        use_case="Microservice or backend API development",
        industry="Any",
        categories=[
            TemplateCategory(
                name="Goals",
                description="API objectives and use cases",
                examples=["Rate limiting", "Webhook support", "Versioning strategy"]
            ),
            TemplateCategory(
                name="Requirements",
                description="API functional requirements",
                examples=["Endpoints needed", "Request/response format", "Error handling"]
            ),
            TemplateCategory(
                name="Performance",
                description="API performance requirements",
                examples=["Latency requirements", "Throughput", "Caching strategy"]
            ),
        ],
        estimated_specs=25,
        difficulty="intermediate",
        tags=["api", "backend", "microservices"]
    ),
    Template(
        id="template-mobile",
        name="Mobile Application",
        description="Template for iOS/Android mobile applications",
        use_case="Native or cross-platform mobile app",
        industry="Consumer",
        categories=[
            TemplateCategory(
                name="Goals",
                description="Mobile app objectives",
                examples=["Offline functionality", "Push notifications", "Social integration"]
            ),
            TemplateCategory(
                name="Platform Requirements",
                description="Platform-specific considerations",
                examples=["iOS minimum version", "Android permissions", "Device compatibility"]
            ),
        ],
        estimated_specs=30,
        difficulty="advanced",
        tags=["mobile", "ios", "android", "cross-platform"]
    ),
]


@router.get("", response_model=TemplatesListResponse)
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    current_user: User = Depends(get_current_active_user)
) -> TemplatesListResponse:
    """
    List available project templates.

    Args:
        skip: Pagination offset
        limit: Items per page
        industry: Optional industry filter
        tags: Optional tag filter (comma-separated)
        current_user: Authenticated user

    Returns:
        List of available templates

    Example:
        GET /api/v1/templates?industry=SaaS&tags=web,popular
        Authorization: Bearer <token>
    """
    # Filter templates based on criteria
    filtered = AVAILABLE_TEMPLATES.copy()

    if industry:
        filtered = [t for t in filtered if t.industry == industry or t.industry == "Any"]

    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",")]
        filtered = [t for t in filtered if any(tag.lower() in tag_list for tag in t.tags)]

    total = len(filtered)
    paginated = filtered[skip:skip + limit]

    return TemplatesListResponse(
        success=True,
        templates=paginated,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{template_id}", response_model=TemplateDetailResponse)
def get_template(
    template_id: str,
    current_user: User = Depends(get_current_active_user)
) -> TemplateDetailResponse:
    """
    Get template details.

    Args:
        template_id: Template ID
        current_user: Authenticated user

    Returns:
        Detailed template information with preview specs

    Example:
        GET /api/v1/templates/template-web-app
        Authorization: Bearer <token>
    """
    template = next((t for t in AVAILABLE_TEMPLATES if t.id == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    # Generate preview specifications from template categories
    preview_specs = []
    for i, category in enumerate(template.categories):
        for j, example in enumerate(category.examples[:2]):  # Max 2 examples per category
            preview_specs.append({
                "category": category.name.lower().replace(" ", "_"),
                "content": example
            })

    return TemplateDetailResponse(
        success=True,
        template=template,
        preview_specs=preview_specs
    )


@router.post("/{template_id}/apply")
def apply_template(
    template_id: str,
    project_id: str = Query(..., description="Project ID to apply template to"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> ApplyTemplateResponse:
    """
    Apply a template to a project.

    Applies all template specifications to the project as starting points.

    Args:
        template_id: Template ID
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status and number of specs created

    Example:
        POST /api/v1/templates/template-web-app/apply?project_id=proj-123
        Authorization: Bearer <token>
    """
    # Verify project exists and user has access
    project = db.query(Project).where(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    if str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Get template
    template = next((t for t in AVAILABLE_TEMPLATES if t.id == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    # Apply template specifications
    specs_created = 0
    for category in template.categories:
        for example in category.examples:
            spec = Specification(
                project_id=project_id,
                category=category.name.lower().replace(" ", "_"),
                content=example,
                source="template",
                confidence=0.8,  # Template specs have good confidence
                is_current=True
            )
            db.add(spec)
            specs_created += 1

    db.commit()

    return ApplyTemplateResponse(
        success=True,
        project_id=str(project.id),
        specs_created=specs_created,
        message=f"Applied '{template.name}' template with {specs_created} specifications"
    )
