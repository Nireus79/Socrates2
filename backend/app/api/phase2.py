"""
Phase 2 Advanced Features API Endpoints.

Handles:
- Subscription tier information and management
- Usage reporting and quota checks
- Rate limiting status and monitoring
- Validator endpoints for form validation
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.database import get_db_auth, get_db_specs
from ..core.rate_limiting import get_rate_limiter
from ..core.security import get_current_active_user
from ..core.subscription_tiers import TIER_LIMITS, SubscriptionTier
from ..core.usage_limits import UsageLimitError, UsageLimiter
from ..core.validators import (
    validate_email,
    validate_password,
    validate_project_name,
    validate_team_name,
    validate_username,
)
from ..models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/phase2", tags=["phase2"])

# ===== Request/Response Models =====


class SubscriptionTierInfo(BaseModel):
    """Subscription tier information response."""

    tier: str = Field(..., description="Tier name (FREE, PRO, TEAM, ENTERPRISE)")
    max_projects: Optional[int] = Field(..., description="Maximum projects allowed")
    max_team_members: Optional[int] = Field(..., description="Maximum team members allowed")
    api_requests_per_day: Optional[int] = Field(..., description="API requests per day limit")
    storage_gb: Optional[int] = Field(..., description="Storage in GB")
    price_usd: Optional[float] = Field(..., description="Monthly price in USD")
    features: list[str] = Field(..., description="List of available features")


class SubscriptionLimitsResponse(BaseModel):
    """User subscription limits response."""

    current_tier: str = Field(..., description="Current subscription tier")
    max_projects: Optional[int]
    max_team_members: Optional[int]
    api_requests_per_day: Optional[int]
    storage_gb: Optional[int]


class UsageMetric(BaseModel):
    """Single usage metric."""

    name: str = Field(..., description="Metric name")
    current: int = Field(..., description="Current usage")
    limit: Optional[int] = Field(..., description="Limit for this metric")
    percentage: float = Field(..., description="Percentage of limit used (0-100)")


class UsageSummaryResponse(BaseModel):
    """User usage summary response."""

    tier: str = Field(..., description="Current subscription tier")
    metrics: list[UsageMetric] = Field(..., description="List of usage metrics")
    storage_used_gb: float = Field(..., description="Storage used in GB")
    api_requests_today: int = Field(..., description="API requests made today")
    projects_created: int = Field(..., description="Projects created by user")
    team_members: int = Field(..., description="Team members for user's team")


class RateLimitStatusResponse(BaseModel):
    """Rate limit status response."""

    limit: int = Field(..., description="Requests per day limit")
    remaining: int = Field(..., description="Remaining requests today")
    reset_at: str = Field(..., description="ISO timestamp when counter resets")
    current_requests: int = Field(..., description="Requests made today")
    percentage_used: float = Field(..., description="Percentage of limit used")


class ValidatorRequest(BaseModel):
    """Validator request."""

    value: str = Field(..., description="Value to validate")


class ValidatorResponse(BaseModel):
    """Validator response."""

    valid: bool = Field(..., description="Is the value valid")
    message: str = Field(..., description="Validation message (empty if valid)")


class BulkValidatorResponse(BaseModel):
    """Bulk validator response."""

    email: Optional[bool] = Field(None, description="Is email valid")
    password: Optional[bool] = Field(None, description="Is password valid")
    username: Optional[bool] = Field(None, description="Is username valid")
    project_name: Optional[bool] = Field(None, description="Is project name valid")
    team_name: Optional[bool] = Field(None, description="Is team name valid")


# ===== Subscription Endpoints =====


@router.get("/subscriptions/tiers", response_model=list[SubscriptionTierInfo])
def get_subscription_tiers():
    """
    Get all available subscription tiers.

    Returns:
        List of subscription tier information

    Example response:
        [
            {
                "tier": "FREE",
                "max_projects": 3,
                "max_team_members": 1,
                "api_requests_per_day": 1000,
                "storage_gb": 1,
                "price_usd": 0,
                "features": ["Basic question generation", "Conflict detection", "Learning analytics"]
            },
            ...
        ]
    """
    try:
        tiers_info = []
        for tier in SubscriptionTier:
            tier_limits = TIER_LIMITS.get(tier, {})
            tiers_info.append(
                SubscriptionTierInfo(
                    tier=tier.name,
                    max_projects=tier_limits.get("max_projects"),
                    max_team_members=tier_limits.get("max_team_members"),
                    api_requests_per_day=tier_limits.get("api_requests_per_day"),
                    storage_gb=tier_limits.get("storage_gb"),
                    price_usd=tier_limits.get("price_usd"),
                    features=tier_limits.get("features", []),
                )
            )
        return tiers_info
    except Exception as e:
        logger.error(f"Error fetching subscription tiers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription tiers",
        )


@router.get(
    "/subscriptions/my-tier",
    response_model=SubscriptionLimitsResponse,
    dependencies=[Depends(get_current_active_user)],
)
def get_my_subscription_tier(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current user's subscription tier and limits.

    Returns:
        Current subscription tier information

    Example response:
        {
            "current_tier": "PRO",
            "max_projects": 25,
            "max_team_members": 10,
            "api_requests_per_day": 100000,
            "storage_gb": 100
        }
    """
    try:
        # Get user's subscription tier (default to FREE)
        user_tier = getattr(current_user, "subscription_tier", SubscriptionTier.FREE)
        if isinstance(user_tier, str):
            try:
                user_tier = SubscriptionTier[user_tier]
            except KeyError:
                user_tier = SubscriptionTier.FREE

        tier_limits = TIER_LIMITS.get(user_tier, {})

        return SubscriptionLimitsResponse(
            current_tier=user_tier.name,
            max_projects=tier_limits.get("max_projects"),
            max_team_members=tier_limits.get("max_team_members"),
            api_requests_per_day=tier_limits.get("api_requests_per_day"),
            storage_gb=tier_limits.get("storage_gb"),
        )
    except Exception as e:
        logger.error(f"Error fetching subscription tier for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription tier",
        )


# ===== Usage Endpoints =====


@router.get(
    "/usage/summary",
    response_model=UsageSummaryResponse,
    dependencies=[Depends(get_current_active_user)],
)
def get_usage_summary(
    current_user: User = Depends(get_current_active_user),
    db_specs: Session = Depends(get_db_specs),
    db_auth: Session = Depends(get_db_auth),
):
    """
    Get current user's usage summary and quota status.

    Returns:
        Usage metrics and current consumption

    Example response:
        {
            "tier": "PRO",
            "metrics": [
                {"name": "Projects", "current": 5, "limit": 25, "percentage": 20.0},
                {"name": "API Requests", "current": 45000, "limit": 100000, "percentage": 45.0}
            ],
            "storage_used_gb": 12.5,
            "api_requests_today": 450,
            "projects_created": 5,
            "team_members": 3
        }
    """
    try:
        # Get user's tier
        user_tier = getattr(current_user, "subscription_tier", SubscriptionTier.FREE)
        if isinstance(user_tier, str):
            try:
                user_tier = SubscriptionTier[user_tier]
            except KeyError:
                user_tier = SubscriptionTier.FREE

        tier_limits = TIER_LIMITS.get(user_tier, {})

        # Build metrics
        metrics = []

        # Projects metric
        from ..models.project import Project

        projects_count = db_specs.query(Project).filter(Project.owner_id == current_user.id).count()
        max_projects = tier_limits.get("max_projects")
        project_pct = (projects_count / max_projects * 100) if max_projects else 0
        metrics.append(
            UsageMetric(
                name="Projects",
                current=projects_count,
                limit=max_projects,
                percentage=min(project_pct, 100),
            )
        )

        # API requests metric
        api_limit = tier_limits.get("api_requests_per_day")
        api_pct = 45.0  # Placeholder
        metrics.append(
            UsageMetric(
                name="API Requests Today",
                current=450,  # Placeholder
                limit=api_limit,
                percentage=api_pct,
            )
        )

        # Team members metric
        from ..models.team_member import TeamMember

        team_members_count = db_specs.query(TeamMember).filter(TeamMember.user_id == current_user.id).count()
        max_team_members = tier_limits.get("max_team_members")
        team_pct = (team_members_count / max_team_members * 100) if max_team_members else 0
        metrics.append(
            UsageMetric(
                name="Team Members",
                current=team_members_count,
                limit=max_team_members,
                percentage=min(team_pct, 100),
            )
        )

        return UsageSummaryResponse(
            tier=user_tier.name,
            metrics=metrics,
            storage_used_gb=12.5,  # Placeholder
            api_requests_today=450,  # Placeholder
            projects_created=projects_count,
            team_members=team_members_count,
        )
    except Exception as e:
        logger.error(f"Error fetching usage summary for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch usage summary",
        )


# ===== Rate Limit Endpoints =====


@router.get(
    "/rate-limit/status",
    response_model=RateLimitStatusResponse,
    dependencies=[Depends(get_current_active_user)],
)
def get_rate_limit_status(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current rate limit status for authenticated user.

    Returns:
        Rate limit information and remaining quota

    Example response:
        {
            "limit": 100000,
            "remaining": 85000,
            "reset_at": "2025-11-14T09:15:00Z",
            "current_requests": 15000,
            "percentage_used": 15.0
        }
    """
    try:
        # Get user's tier
        user_tier = getattr(current_user, "subscription_tier", SubscriptionTier.FREE)
        if isinstance(user_tier, str):
            try:
                user_tier = SubscriptionTier[user_tier]
            except KeyError:
                user_tier = SubscriptionTier.FREE

        tier_limits = TIER_LIMITS.get(user_tier, {})
        daily_limit = tier_limits.get("api_requests_per_day", 1000)

        # Get rate limiter
        limiter = get_rate_limiter()
        remaining = limiter.get_remaining(current_user.id, daily_limit)
        current_requests = daily_limit - remaining if remaining is not None else 0

        from datetime import datetime, timedelta, timezone

        reset_at = datetime.now(timezone.utc) + timedelta(days=1)

        return RateLimitStatusResponse(
            limit=daily_limit,
            remaining=remaining or 0,
            reset_at=reset_at.isoformat(),
            current_requests=current_requests,
            percentage_used=(current_requests / daily_limit * 100) if daily_limit else 0,
        )
    except Exception as e:
        logger.error(f"Error fetching rate limit status for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch rate limit status",
        )


# ===== Validator Endpoints =====


@router.post("/validators/email", response_model=ValidatorResponse)
def validate_email_endpoint(request: ValidatorRequest):
    """
    Validate email format.

    Args:
        request: Validator request with email value

    Returns:
        Validation result

    Example response:
        {
            "valid": true,
            "message": ""
        }
    """
    valid = validate_email(request.value)
    return ValidatorResponse(
        valid=valid,
        message="" if valid else "Invalid email format",
    )


@router.post("/validators/password", response_model=ValidatorResponse)
def validate_password_endpoint(request: ValidatorRequest):
    """
    Validate password strength.

    Args:
        request: Validator request with password value

    Returns:
        Validation result

    Example response:
        {
            "valid": true,
            "message": ""
        }
    """
    valid, message = validate_password(request.value)
    return ValidatorResponse(valid=valid, message=message)


@router.post("/validators/username", response_model=ValidatorResponse)
def validate_username_endpoint(request: ValidatorRequest):
    """
    Validate username format.

    Args:
        request: Validator request with username value

    Returns:
        Validation result

    Example response:
        {
            "valid": true,
            "message": ""
        }
    """
    valid, message = validate_username(request.value)
    return ValidatorResponse(valid=valid, message=message)


@router.post("/validators/project-name", response_model=ValidatorResponse)
def validate_project_name_endpoint(request: ValidatorRequest):
    """
    Validate project name format.

    Args:
        request: Validator request with project name value

    Returns:
        Validation result

    Example response:
        {
            "valid": true,
            "message": ""
        }
    """
    valid, message = validate_project_name(request.value)
    return ValidatorResponse(valid=valid, message=message)


@router.post("/validators/team-name", response_model=ValidatorResponse)
def validate_team_name_endpoint(request: ValidatorRequest):
    """
    Validate team name format.

    Args:
        request: Validator request with team name value

    Returns:
        Validation result

    Example response:
        {
            "valid": true,
            "message": ""
        }
    """
    valid, message = validate_team_name(request.value)
    return ValidatorResponse(valid=valid, message=message)


@router.post("/validators/bulk", response_model=BulkValidatorResponse)
def bulk_validate(
    email: Optional[str] = None,
    password: Optional[str] = None,
    username: Optional[str] = None,
    project_name: Optional[str] = None,
    team_name: Optional[str] = None,
):
    """
    Validate multiple fields at once.

    Args:
        email: Optional email to validate
        password: Optional password to validate
        username: Optional username to validate
        project_name: Optional project name to validate
        team_name: Optional team name to validate

    Returns:
        Validation results for all provided fields

    Example response:
        {
            "email": true,
            "password": false,
            "username": true,
            "project_name": true,
            "team_name": null
        }
    """
    result = {}

    if email is not None:
        result["email"] = validate_email(email)

    if password is not None:
        valid, _ = validate_password(password)
        result["password"] = valid

    if username is not None:
        valid, _ = validate_username(username)
        result["username"] = valid

    if project_name is not None:
        valid, _ = validate_project_name(project_name)
        result["project_name"] = valid

    if team_name is not None:
        valid, _ = validate_team_name(team_name)
        result["team_name"] = valid

    return BulkValidatorResponse(**result)
