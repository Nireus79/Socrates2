"""
Subscription tier definitions and limits.

Defines pricing and feature limits for each subscription tier.
"""
from enum import Enum
from typing import Dict, Optional


class SubscriptionTier(str, Enum):
    """Available subscription tiers."""
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


# Tier limits and pricing
TIER_LIMITS: Dict[SubscriptionTier, Dict] = {
    SubscriptionTier.FREE: {
        "max_projects": 3,
        "max_specifications": 50,
        "max_team_members": 1,
        "api_requests_per_day": 1000,
        "storage_gb": 1,
        "price_usd": 0,
        "billing_interval": None,  # No billing for free
        "features": [
            "Basic project management",
            "Question-based spec extraction",
            "Limited API access",
        ],
    },
    SubscriptionTier.PRO: {
        "max_projects": 25,
        "max_specifications": None,  # Unlimited
        "max_team_members": 5,
        "api_requests_per_day": 100000,
        "storage_gb": 100,
        "price_usd": 29,
        "billing_interval": "month",
        "stripe_price_id": "price_pro_monthly",  # Set from environment
        "features": [
            "25 concurrent projects",
            "Unlimited specifications",
            "Team collaboration (5 members)",
            "Advanced search",
            "Priority support",
            "API access",
        ],
    },
    SubscriptionTier.TEAM: {
        "max_projects": None,  # Unlimited
        "max_specifications": None,  # Unlimited
        "max_team_members": 50,
        "api_requests_per_day": None,  # Unlimited
        "storage_gb": 1000,
        "price_usd": 99,
        "billing_interval": "month",
        "stripe_price_id": "price_team_monthly",  # Set from environment
        "features": [
            "Unlimited projects",
            "Unlimited specifications",
            "Team collaboration (50 members)",
            "Advanced analytics",
            "Priority support",
            "Custom integrations",
            "SSO/SAML",
        ],
    },
    SubscriptionTier.ENTERPRISE: {
        "max_projects": None,  # Unlimited
        "max_specifications": None,  # Unlimited
        "max_team_members": None,  # Unlimited
        "api_requests_per_day": None,  # Unlimited
        "storage_gb": None,  # Custom
        "price_usd": "custom",
        "billing_interval": "month",
        "stripe_price_id": None,  # Custom pricing
        "features": [
            "Everything in Team",
            "Unlimited everything",
            "Dedicated support",
            "SLA guarantee",
            "On-premise deployment",
            "Custom training",
        ],
    },
}


def get_tier_limit(tier: SubscriptionTier, limit_name: str) -> Optional[int | str]:
    """
    Get a specific limit for a tier.

    Args:
        tier: Subscription tier
        limit_name: Name of the limit (max_projects, max_team_members, etc.)

    Returns:
        The limit value, or None if tier doesn't exist or limit not found
    """
    if tier not in TIER_LIMITS:
        return None
    return TIER_LIMITS[tier].get(limit_name)


def get_tier_info(tier: SubscriptionTier) -> Optional[Dict]:
    """
    Get all info for a tier.

    Args:
        tier: Subscription tier

    Returns:
        Dictionary with all tier information, or None if tier doesn't exist
    """
    return TIER_LIMITS.get(tier)


def can_create_project(tier: SubscriptionTier, current_count: int) -> bool:
    """
    Check if user can create another project.

    Args:
        tier: User's subscription tier
        current_count: Current number of projects

    Returns:
        True if limit not reached, False otherwise
    """
    limit = get_tier_limit(tier, "max_projects")
    if limit is None:
        return True  # Unlimited
    return current_count < limit


def can_add_team_member(tier: SubscriptionTier, current_count: int) -> bool:
    """
    Check if user can add another team member.

    Args:
        tier: User's subscription tier
        current_count: Current number of team members

    Returns:
        True if limit not reached, False otherwise
    """
    limit = get_tier_limit(tier, "max_team_members")
    if limit is None:
        return True  # Unlimited
    return current_count < limit


def get_api_rate_limit(tier: SubscriptionTier) -> Optional[int]:
    """
    Get API request limit per day for tier.

    Args:
        tier: Subscription tier

    Returns:
        Number of requests per day, or None if unlimited
    """
    return get_tier_limit(tier, "api_requests_per_day")
