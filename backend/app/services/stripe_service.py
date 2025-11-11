"""
Stripe integration service.

Handles all Stripe API interactions:
- Customer creation
- Subscription management
- Checkout sessions
- Webhook processing
"""
import logging
from typing import Any, Dict, Optional
from uuid import UUID

import stripe

from ..core.config import settings

logger = logging.getLogger(__name__)

# Configure Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Handle Stripe integration and payment processing."""

    @staticmethod
    def create_customer(user_id: UUID, email: str, name: str, metadata: Optional[Dict] = None) -> str:
        """
        Create a Stripe customer.

        Args:
            user_id: User's ID in our system
            email: User's email
            name: User's full name
            metadata: Optional custom metadata

        Returns:
            Stripe customer ID

        Raises:
            stripe.error.StripeError: If Stripe API call fails
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "user_id": str(user_id),
                    **(metadata or {})
                }
            )
            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise

    @staticmethod
    def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a checkout session for subscription.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancellation
            metadata: Optional custom metadata

        Returns:
            Stripe session ID

        Raises:
            stripe.error.StripeError: If Stripe API call fails
        """
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                payment_method_types=["card"],
                metadata=metadata or {}
            )
            logger.info(f"Created checkout session {session.id}")
            return session.id

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise

    @staticmethod
    def get_checkout_session(session_id: str) -> Dict[str, Any]:
        """
        Get checkout session details.

        Args:
            session_id: Stripe session ID

        Returns:
            Session details dictionary
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                "id": session.id,
                "payment_status": session.payment_status,
                "subscription_id": session.subscription,
                "customer_id": session.customer,
                "status": session.status,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            raise

    @staticmethod
    def get_portal_session(customer_id: str, return_url: str) -> str:
        """
        Create a billing portal session.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal

        Returns:
            Portal URL

        Raises:
            stripe.error.StripeError: If Stripe API call fails
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            logger.info(f"Created billing portal session for customer {customer_id}")
            return session.url

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create billing portal session: {e}")
            raise

    @staticmethod
    def get_subscription(subscription_id: str) -> Dict[str, Any]:
        """
        Get subscription details.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Subscription details dictionary
        """
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": sub.id,
                "customer_id": sub.customer,
                "status": sub.status,
                "items": [
                    {
                        "price_id": item.price.id,
                        "amount": item.price.unit_amount,
                        "currency": item.price.currency,
                    }
                    for item in sub.items.data
                ],
                "current_period_start": sub.current_period_start,
                "current_period_end": sub.current_period_end,
                "cancel_at_period_end": sub.cancel_at_period_end,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription {subscription_id}: {e}")
            raise

    @staticmethod
    def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> Dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of billing period. If False, cancel immediately.

        Returns:
            Updated subscription details

        Raises:
            stripe.error.StripeError: If Stripe API call fails
        """
        try:
            if at_period_end:
                sub = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                sub = stripe.Subscription.delete(subscription_id)

            logger.info(f"Canceled subscription {subscription_id} (at_period_end={at_period_end})")

            return {
                "id": sub.id,
                "status": sub.status,
                "cancel_at_period_end": sub.cancel_at_period_end,
                "canceled_at": sub.canceled_at,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {e}")
            raise

    @staticmethod
    def verify_webhook_signature(body: bytes, signature: str) -> bool:
        """
        Verify webhook signature from Stripe.

        Args:
            body: Raw request body
            signature: Signature from Stripe-Signature header

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            stripe.Webhook.construct_event(
                body,
                signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
            return True
        except (ValueError, stripe.error.SignatureVerificationError):
            logger.warning("Invalid webhook signature")
            return False

    @staticmethod
    def get_customer_invoices(customer_id: str, limit: int = 10) -> list[Dict[str, Any]]:
        """
        Get invoices for a customer.

        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to return

        Returns:
            List of invoice dictionaries
        """
        try:
            invoices = stripe.Invoice.list(customer=customer_id, limit=limit)
            return [
                {
                    "id": invoice.id,
                    "amount_paid": invoice.amount_paid,
                    "amount_due": invoice.amount_due,
                    "status": invoice.status,
                    "currency": invoice.currency,
                    "date": invoice.date,
                    "paid": invoice.paid,
                    "hosted_invoice_url": invoice.hosted_invoice_url,
                    "pdf": invoice.invoice_pdf,
                }
                for invoice in invoices.data
            ]
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve invoices for customer {customer_id}: {e}")
            raise
