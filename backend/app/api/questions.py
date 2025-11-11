"""
Questions API endpoints.

Provides:
- Create questions
- List questions for project
- Get question details
- Update question
- Answer question
- Delete question

Uses repository pattern for efficient data access.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.database import get_db_auth, get_db_specs
from ..core.security import get_current_active_user
from ..models.user import User
from ..repositories import RepositoryService

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])


# Dependency for repository service
def get_repository_service(
    auth_session: Session = Depends(get_db_auth),
    specs_session: Session = Depends(get_db_specs)
) -> RepositoryService:
    """Get repository service with both database sessions."""
    return RepositoryService(auth_session, specs_session)


# Request/Response Models
class CreateQuestionRequest(BaseModel):
    """Request model for creating a question."""
    project_id: str = Field(..., description="Project UUID")
    text: str = Field(..., min_length=5, max_length=5000, description="Question text")
    category: Optional[str] = Field(default="functional", description="Question category")
    priority: Optional[str] = Field(default="medium", pattern="^(low|medium|high|critical)$")
    session_id: Optional[str] = Field(None, description="Session UUID if question is from a session")


class UpdateQuestionRequest(BaseModel):
    """Request model for updating a question."""
    text: Optional[str] = Field(None, min_length=5, max_length=5000)
    category: Optional[str] = Field(None)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    status: Optional[str] = Field(None, pattern="^(pending|answered|skipped|resolved)$")


class AnswerQuestionRequest(BaseModel):
    """Request model for answering a question."""
    answer: str = Field(..., min_length=5, max_length=10000, description="Answer text")


class QuestionResponse(BaseModel):
    """Response model for question data."""
    id: str
    project_id: str
    session_id: Optional[str]
    text: str
    category: Optional[str]
    priority: str
    status: str
    answer: Optional[str]
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class QuestionListResponse(BaseModel):
    """Response for question list."""
    questions: list[QuestionResponse]
    total: int
    skip: int
    limit: int


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    request: CreateQuestionRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> QuestionResponse:
    """
    Create a new question.

    Args:
        request: Question details (text, category, priority, project_id)
        current_user: Authenticated user
        service: Repository service

    Returns:
        QuestionResponse with created question details

    Example:
        POST /api/v1/questions
        Authorization: Bearer <token>
        {
            "project_id": "550e8400-e29b-41d4-a716-446655440000",
            "text": "What are the main requirements?",
            "category": "functional",
            "priority": "high"
        }

        Response 201:
        {
            "id": "550e8400-e29b-41d4-a716-446655440050",
            "project_id": "550e8400-e29b-41d4-a716-446655440000",
            "text": "What are the main requirements?",
            "category": "functional",
            "priority": "high",
            "status": "pending",
            "created_at": "2025-11-11T12:00:00"
        }
    """
    try:
        # Parse project UUID
        project_uuid = UUID(request.project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {request.project_id}"
        )

    try:
        # Verify project exists and user owns it
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {request.project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: you don't have access to this project"
            )

        # Create question
        question = service.questions.create_question(
            project_id=project_uuid,
            text=request.text,
            category=request.category or "functional",
            priority=request.priority or "medium"
        )

        # Commit transaction
        service.commit_all()

        return QuestionResponse(
            id=str(question.id),
            project_id=str(question.project_id),
            session_id=str(question.session_id) if question.session_id else None,
            text=question.text,
            category=question.category,
            priority=question.priority,
            status=question.status,
            answer=question.answer,
            created_at=question.created_at.isoformat(),
            updated_at=question.updated_at.isoformat() if question.updated_at else None
        )

    except HTTPException:
        service.rollback_all()
        raise
    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create question"
        ) from e


@router.get("/project/{project_id}", response_model=QuestionListResponse)
def list_project_questions(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> QuestionListResponse:
    """
    List all questions for a project.

    Args:
        project_id: Project UUID
        skip: Number of questions to skip (pagination)
        limit: Maximum number of questions to return
        current_user: Authenticated user
        service: Repository service

    Returns:
        QuestionListResponse with questions list

    Example:
        GET /api/v1/questions/project/550e8400-e29b-41d4-a716-446655440000?skip=0&limit=10
        Authorization: Bearer <token>

        Response:
        {
            "questions": [...],
            "total": 5,
            "skip": 0,
            "limit": 10
        }
    """
    try:
        # Parse project UUID
        project_uuid = UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project ID format: {project_id}"
        )

    try:
        # Verify project exists and user owns it
        project = service.projects.get_by_id(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        if str(project.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )

        # Get questions
        questions = service.questions.get_project_questions(
            project_id=project_uuid,
            skip=skip,
            limit=limit
        )

        # Get total count
        total = service.questions.count_by_field("project_id", project_uuid)

        return QuestionListResponse(
            questions=[
                QuestionResponse(
                    id=str(q.id),
                    project_id=str(q.project_id),
                    session_id=str(q.session_id) if q.session_id else None,
                    text=q.text,
                    category=q.category,
                    priority=q.priority,
                    status=q.status,
                    answer=q.answer,
                    created_at=q.created_at.isoformat(),
                    updated_at=q.updated_at.isoformat() if q.updated_at else None
                )
                for q in questions
            ],
            total=total,
            skip=skip,
            limit=limit
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list questions"
        ) from e


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(
    question_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> QuestionResponse:
    """
    Get question details.

    Args:
        question_id: Question UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        QuestionResponse with question details

    Example:
        GET /api/v1/questions/550e8400-e29b-41d4-a716-446655440050
        Authorization: Bearer <token>

        Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440050",
            ...
        }
    """
    try:
        # Parse UUID
        question_uuid = UUID(question_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid question ID format: {question_id}"
        )

    # Get question
    question = service.questions.get_by_id(question_uuid)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question not found: {question_id}"
        )

    # Verify permissions
    project = service.projects.get_by_id(question.project_id)
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    return QuestionResponse(
        id=str(question.id),
        project_id=str(question.project_id),
        session_id=str(question.session_id) if question.session_id else None,
        text=question.text,
        category=question.category,
        priority=question.priority,
        status=question.status,
        answer=question.answer,
        created_at=question.created_at.isoformat(),
        updated_at=question.updated_at.isoformat() if question.updated_at else None
    )


@router.put("/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: str,
    request: UpdateQuestionRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> QuestionResponse:
    """
    Update question details.

    Args:
        question_id: Question UUID
        request: Fields to update (text, category, priority, status)
        current_user: Authenticated user
        service: Repository service

    Returns:
        QuestionResponse with updated question

    Example:
        PUT /api/v1/questions/550e8400-e29b-41d4-a716-446655440050
        Authorization: Bearer <token>
        {
            "text": "Updated question text",
            "priority": "critical"
        }

        Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440050",
            ...
        }
    """
    try:
        # Parse UUID
        question_uuid = UUID(question_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid question ID format: {question_id}"
        )

    # Get question
    question = service.questions.get_by_id(question_uuid)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question not found: {question_id}"
        )

    # Verify permissions
    project = service.projects.get_by_id(question.project_id)
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    try:
        # Update fields if provided
        if request.text is not None:
            question = service.questions.update(question_uuid, text=request.text)
        if request.category is not None:
            question = service.questions.update(question_uuid, category=request.category)
        if request.priority is not None:
            question = service.questions.update_question_priority(question_uuid, request.priority)
        if request.status is not None:
            question = service.questions.update(question_uuid, status=request.status)

        # Commit transaction
        service.commit_all()

        return QuestionResponse(
            id=str(question.id),
            project_id=str(question.project_id),
            session_id=str(question.session_id) if question.session_id else None,
            text=question.text,
            category=question.category,
            priority=question.priority,
            status=question.status,
            answer=question.answer,
            created_at=question.created_at.isoformat(),
            updated_at=question.updated_at.isoformat() if question.updated_at else None
        )

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update question"
        ) from e


@router.post("/{question_id}/answer", response_model=QuestionResponse)
def answer_question(
    question_id: str,
    request: AnswerQuestionRequest,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> QuestionResponse:
    """
    Answer a question.

    Args:
        question_id: Question UUID
        request: Answer text
        current_user: Authenticated user
        service: Repository service

    Returns:
        QuestionResponse with answered question

    Example:
        POST /api/v1/questions/550e8400-e29b-41d4-a716-446655440050/answer
        Authorization: Bearer <token>
        {
            "answer": "The main requirements are: 1) User authentication 2) API endpoints 3) Database storage"
        }

        Response:
        {
            "id": "550e8400-e29b-41d4-a716-446655440050",
            "status": "answered",
            "answer": "The main requirements are...",
            ...
        }
    """
    try:
        # Parse UUID
        question_uuid = UUID(question_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid question ID format: {question_id}"
        )

    # Get question
    question = service.questions.get_by_id(question_uuid)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question not found: {question_id}"
        )

    # Verify permissions
    project = service.projects.get_by_id(question.project_id)
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    try:
        # Answer question
        question = service.questions.answer_question(question_uuid, request.answer)
        service.commit_all()

        return QuestionResponse(
            id=str(question.id),
            project_id=str(question.project_id),
            session_id=str(question.session_id) if question.session_id else None,
            text=question.text,
            category=question.category,
            priority=question.priority,
            status=question.status,
            answer=question.answer,
            created_at=question.created_at.isoformat(),
            updated_at=question.updated_at.isoformat() if question.updated_at else None
        )

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to answer question"
        ) from e


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: str,
    current_user: User = Depends(get_current_active_user),
    service: RepositoryService = Depends(get_repository_service)
) -> None:
    """
    Delete a question.

    Args:
        question_id: Question UUID
        current_user: Authenticated user
        service: Repository service

    Returns:
        No content (204 response)

    Example:
        DELETE /api/v1/questions/550e8400-e29b-41d4-a716-446655440050
        Authorization: Bearer <token>

        Response 204: No Content
    """
    try:
        # Parse UUID
        question_uuid = UUID(question_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid question ID format: {question_id}"
        )

    # Get question
    question = service.questions.get_by_id(question_uuid)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question not found: {question_id}"
        )

    # Verify permissions
    project = service.projects.get_by_id(question.project_id)
    if str(project.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    try:
        # Delete question
        service.questions.delete(question_uuid)
        service.commit_all()

    except Exception as e:
        service.rollback_all()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete question"
        ) from e
