"""
Billing and subscription management API endpoints.

Handles:
- Checkout session creation
- Subscription management
- Invoice retrieval
- Billing portal access
- Webhook processing
"""
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db_specs
from ..core.security import get_current_active_user
from ..core.subscription_tiers import SubscriptionTier
from ..models.invoice import Invoice
from ..models.subscription import Subscription
from ..models.user import User
from ..services.stripe_service import StripeService
from ..services.trial_service import TrialService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


# ===== Request/Response Models =====

class CheckoutRequest(BaseModel):
    """Create checkout session request."""
    tier: SubscriptionTier
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    """Checkout session response."""
    session_id: str
    checkout_url: str


class SubscriptionResponse(BaseModel):
    """Subscription details response."""
    id: str
    status: str
    tier: str
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool


class InvoiceResponse(BaseModel):
    """Invoice details response."""
    id: str
    amount_paid: float
    amount_due: float
    status: str
    paid_at: Optional[str]
    hosted_invoice_url: Optional[str]


class TrialStatusResponse(BaseModel):
    """Trial status response."""
    has_trial: bool
    trial_ends_at: Optional[str]
    is_expired: bool
    is_in_grace_period: bool
    days_remaining: int


class UsageStatsResponse(BaseModel):
    """Usage statistics response."""
    tier: str
    projects_count: int
    max_projects: Optional[int]
    team_members_count: int
    max_team_members: Optional[int]
    storage_gb_used: float
    max_storage_gb: Optional[int]


# ===== Endpoints =====

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
) -> CheckoutResponse:
    """
    Create a Stripe checkout session for subscription upgrade.

    Args:
        request: Checkout request with tier and return URLs
        current_user: Authenticated user

    Returns:
        CheckoutResponse with session ID and checkout URL

    Raises:
        HTTPException: If subscription creation fails
    """
    try:
        # Check if user already has active subscription
        # (In production, fetch from database)

        # Get or create Stripe customer
        stripe_customer_id = current_user.stripe_customer_id
        if not stripe_customer_id:
            stripe_customer_id = StripeService.create_customer(
                user_id=current_user.id,
                email=current_user.email,
                name=current_user.name or "User"
            )
            # Update user with Stripe customer ID
            # (This would be saved to database in production)

        # Get Stripe price ID for tier
        # In production, fetch from config based on tier
        price_id_map = {
            SubscriptionTier.PRO: "price_pro_monthly",
            SubscriptionTier.TEAM: "price_team_monthly",
            SubscriptionTier.ENTERPRISE: "price_enterprise_monthly",
        }

        price_id = price_id_map.get(request.tier)
        if not price_id:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {request.tier}")

        # Create checkout session
        session_id = StripeService.create_checkout_session(
            customer_id=stripe_customer_id,
            price_id=price_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={"tier": request.tier, "user_id": str(current_user.id)}
        )

        # Get session details to get checkout URL
        session_details = StripeService.get_checkout_session(session_id)

        logger.info(f"Created checkout session {session_id} for user {current_user.id}")

        return CheckoutResponse(
            session_id=session_id,
            checkout_url=f"https://checkout.stripe.com/pay/{session_id}"
        )

    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> SubscriptionResponse:
    """
    Get current subscription details.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        SubscriptionResponse with current subscription info

    Raises:
        HTTPException: If no subscription found
    """
    try:
        # Fetch subscription from database
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(["active", "past_due"])
        ).first()

        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="No active subscription found. User is on free tier."
            )

        return SubscriptionResponse(
            id=str(subscription.id),
            status=subscription.status,
            tier=subscription.tier,
            current_period_start=subscription.current_period_start.isoformat(),
            current_period_end=subscription.current_period_end.isoformat(),
            cancel_at_period_end=subscription.cancel_at_period_end
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscription")


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> Dict[str, Any]:
    """
    Cancel current subscription (at end of billing period).

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Dictionary with cancellation status

    Raises:
        HTTPException: If no subscription or cancellation fails
    """
    try:
        # Fetch subscription from database
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.status == "active"
        ).first()

        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")

        # Cancel subscription at end of period
        StripeService.cancel_subscription(
            subscription.stripe_subscription_id,
            at_period_end=True
        )

        # Update database
        subscription.cancel_at_period_end = True
        db.commit()

        logger.info(f"Canceled subscription {subscription.id} for user {current_user.id}")

        return {
            "status": "success",
            "message": "Subscription will be canceled at the end of the billing period",
            "cancel_at": subscription.current_period_end.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.get("/invoices", response_model=list[InvoiceResponse])
async def get_invoices(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> list[InvoiceResponse]:
    """
    Get user's invoices.

    Args:
        limit: Maximum number of invoices to return
        current_user: Authenticated user
        db: Database session

    Returns:
        List of invoices

    Raises:
        HTTPException: If invoice retrieval fails
    """
    try:
        # Fetch invoices from database
        invoices = db.query(Invoice).filter(
            Invoice.user_id == current_user.id
        ).order_by(Invoice.invoice_date.desc()).limit(limit).all()

        return [
            InvoiceResponse(
                id=str(invoice.id),
                amount_paid=float(invoice.amount_paid),
                amount_due=float(invoice.amount_due),
                status=invoice.status,
                paid_at=invoice.paid_at.isoformat() if invoice.paid_at else None,
                hosted_invoice_url=invoice.hosted_invoice_url
            )
            for invoice in invoices
        ]

    except Exception as e:
        logger.error(f"Failed to fetch invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invoices")


@router.get("/portal")
async def get_billing_portal_url(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, str]:
    """
    Get Stripe billing portal URL for managing subscription.

    Args:
        current_user: Authenticated user

    Returns:
        Dictionary with portal URL

    Raises:
        HTTPException: If user has no Stripe customer or portal creation fails
    """
    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(
                status_code=400,
                detail="User has no Stripe customer ID"
            )

        portal_url = StripeService.get_portal_session(
            customer_id=current_user.stripe_customer_id,
            return_url="https://app.socrates.com/settings/billing"  # TODO: Make configurable
        )

        logger.info(f"Created billing portal session for user {current_user.id}")

        return {"portal_url": portal_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create billing portal session: {e}")
        raise HTTPException(status_code=500, detail="Failed to access billing portal")


@router.get("/trial", response_model=TrialStatusResponse)
async def get_trial_status(
    current_user: User = Depends(get_current_active_user),
) -> TrialStatusResponse:
    """
    Get trial status for current user.

    Args:
        current_user: Authenticated user

    Returns:
        TrialStatusResponse with trial information
    """
    status = TrialService.get_trial_status(current_user)
    return TrialStatusResponse(**status)


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_specs)
) -> UsageStatsResponse:
    """
    Get usage statistics for current user.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        UsageStatsResponse with usage information

    Raises:
        HTTPException: If unable to fetch stats
    """
    try:
        from ..models.project import Project

        # Get project count
        project_count = db.query(Project).filter(
            Project.user_id == current_user.id
        ).count()

        # Get tier info
        tier = current_user.subscription_tier or "free"
        from ..core.subscription_tiers import TIER_LIMITS, SubscriptionTier
        tier_info = TIER_LIMITS.get(SubscriptionTier(tier), {})

        return UsageStatsResponse(
            tier=tier,
            projects_count=project_count,
            max_projects=tier_info.get("max_projects"),
            team_members_count=1,  # TODO: Count actual team members
            max_team_members=tier_info.get("max_team_members"),
            storage_gb_used=0.0,  # TODO: Calculate actual storage used
            max_storage_gb=tier_info.get("storage_gb")
        )

    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get usage statistics")


@router.post("/webhooks")
async def handle_stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
    """
    Handle Stripe webhook events.

    Processes:
    - payment_intent.succeeded
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded

    Args:
        request: HTTP request with webhook body
        background_tasks: Background task queue

    Returns:
        Dictionary with webhook received status

    Raises:
        HTTPException: If webhook signature invalid
    """
    try:
        # Get webhook signature
        signature = request.headers.get("stripe-signature")
        if not signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")

        # Get raw body
        body = await request.body()

        # Verify signature
        if not StripeService.verify_webhook_signature(body, signature):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

        # Parse event
        event = json.loads(body)
        event_type = event.get("type")

        logger.info(f"Received Stripe webhook: {event_type}")

        # Process webhook asynchronously
        background_tasks.add_task(
            _process_stripe_webhook,
            event
        )

        return {"received": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def _process_stripe_webhook(event: Dict[str, Any]) -> None:
    """
    Process Stripe webhook event in background.

    Args:
        event: Stripe event dictionary
    """

    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    try:
        if event_type == "customer.subscription.updated":
            await _handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(data)
        elif event_type == "invoice.payment_succeeded":
            await _handle_invoice_payment_succeeded(data)
        else:
            logger.debug(f"Unhandled webhook event: {event_type}")

    except Exception as e:
        logger.error(f"Error processing webhook {event_type}: {e}", exc_info=True)


async def _handle_subscription_updated(data: Dict[str, Any]) -> None:
    """Handle subscription updated event."""
    logger.info(f"Subscription updated: {data.get('id')}")
    # TODO: Update subscription in database


async def _handle_subscription_deleted(data: Dict[str, Any]) -> None:
    """Handle subscription deleted event."""
    logger.info(f"Subscription deleted: {data.get('id')}")
    # TODO: Mark subscription as canceled in database


async def _handle_invoice_payment_succeeded(data: Dict[str, Any]) -> None:
    """Handle invoice payment succeeded event."""
    logger.info(f"Invoice payment succeeded: {data.get('id')}")
    # TODO: Record invoice in database
