"""
Centralized subscription plan and feature configuration for Vyastha.

Prices are stored in MongoDB in the plans collection and can be seeded
from PLAN_DEFAULTS. This module acts as the single source of truth for
subscription features, limits, and default pricing.

Important:
- Never hard-code subscription prices in routers or frontend code.
- Prices are stored in INR (rupees).
- Convert rupees to paise only at the Razorpay/payment gateway boundary.
"""


from __future__ import annotations

from copy import deepcopy
from typing import Any


# ---------------------------------------------------------------------------
# FEATURE CONFIGURATION
# ---------------------------------------------------------------------------

# Feature keys used by FeatureAccessService.
# Add new subscription features here first, then map them to each plan.
FEATURE_KEYS: tuple[str, ...] = (
    "invoicing",
    "products",
    "inventory",
    "payment_tracking",
    "basic_analytics",
    "advanced_analytics",
    "advanced_inventory",
    "smart_features",
    "multi_user",
    "priority_support",
    "api_access",
)


# ---------------------------------------------------------------------------
# PLAN RANKING
# ---------------------------------------------------------------------------

# Used to determine whether a plan change is an upgrade or downgrade.
PLAN_RANK: dict[str, int] = {
    "free": 0,
    "basic": 1,
    "pro": 2,
    "business": 3,
}

FALLBACK_PLAN_SLUG = "free"


# ---------------------------------------------------------------------------
# DEFAULT SUBSCRIPTION PLANS
# ---------------------------------------------------------------------------

# All prices are in INR (rupees).
# Example:
#     ₹499/month -> 499
#     ₹4,990/year -> 4990
#
# Convert to paise ONLY before sending the amount to Razorpay.
PLAN_DEFAULTS: list[dict[str, Any]] = [
    {
        "slug": "free",
        "name": "Free",
        "description": "Get started with core billing for a single user.",
        "monthly_price": 0,
        "yearly_price": 0,
        "currency": "INR",
        "active": True,
        "highlight": False,

        "features": {
            "invoicing": True,
            "products": True,
            "inventory": True,
            "payment_tracking": True,
            "basic_analytics": True,
            "advanced_analytics": False,
            "advanced_inventory": False,
            "smart_features": False,
            "multi_user": False,
            "priority_support": False,
            "api_access": False,
        },

        "limits": {
            "invoices_per_month": 25,
            "products": 50,
            "inventory_items": 50,
            "users": 1,
        },

        "feature_list": [
            "Up to 25 invoices / month",
            "Up to 50 products",
            "Basic inventory tracking",
            "Payment tracking",
            "Basic dashboard analytics",
        ],
    },

    {
        "slug": "basic",
        "name": "Basic",
        "description": "Expanded limits for a growing small business.",
        "monthly_price": 499,
        "yearly_price": 4990,
        "currency": "INR",
        "active": True,
        "highlight": False,

        "features": {
            "invoicing": True,
            "products": True,
            "inventory": True,
            "payment_tracking": True,
            "basic_analytics": True,
            "advanced_analytics": False,
            "advanced_inventory": False,
            "smart_features": False,
            "multi_user": True,
            "priority_support": False,
            "api_access": False,
        },

        "limits": {
            "invoices_per_month": 500,
            "products": 1000,
            "inventory_items": 1000,
            "users": 3,
        },

        "feature_list": [
            "Up to 500 invoices / month",
            "Up to 1,000 products",
            "Up to 3 team members",
            "Payment tracking & reminders",
            "Email support",
        ],
    },

    {
        "slug": "pro",
        "name": "Pro",
        "description": "Advanced analytics and smart inventory for scaling teams.",
        "monthly_price": 1299,
        "yearly_price": 12990,
        "currency": "INR",
        "active": True,
        "highlight": True,

        "features": {
            "invoicing": True,
            "products": True,
            "inventory": True,
            "payment_tracking": True,
            "basic_analytics": True,
            "advanced_analytics": True,
            "advanced_inventory": True,
            "smart_features": True,
            "multi_user": True,
            "priority_support": False,
            "api_access": False,
        },

        "limits": {
            "invoices_per_month": 5000,
            "products": 10000,
            "inventory_items": 10000,
            "users": 10,
        },

        "feature_list": [
            "Up to 5,000 invoices / month",
            "Up to 10,000 products",
            "Up to 10 team members",
            "Advanced analytics & reports",
            "Advanced inventory (batches, low-stock alerts)",
            "Smart billing suggestions",
        ],
    },

    {
        "slug": "business",
        "name": "Business",
        "description": (
            "Everything in Pro plus unlimited scale and priority support."
        ),
        "monthly_price": 2999,
        "yearly_price": 29990,
        "currency": "INR",
        "active": True,
        "highlight": False,

        "features": {
            feature: True for feature in FEATURE_KEYS
        },

        "limits": {
            "invoices_per_month": -1,
            "products": -1,
            "inventory_items": -1,
            "users": -1,
        },

        "feature_list": [
            "Unlimited invoices & products",
            "Unlimited team members",
            "All Pro features",
            "API access",
            "Priority support",
            "Dedicated onboarding",
        ],
    },
]


# ---------------------------------------------------------------------------
# FAST PLAN LOOKUP
# ---------------------------------------------------------------------------

PLAN_DEFAULTS_BY_SLUG: dict[str, dict[str, Any]] = {
    plan["slug"]: plan
    for plan in PLAN_DEFAULTS
}


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def get_default_plan(slug: str) -> dict[str, Any]:
    """
    Return a copy of the default configuration for a plan.

    Raises:
        ValueError: If the requested plan does not exist.
    """
    normalized_slug = slug.strip().lower()

    plan = PLAN_DEFAULTS_BY_SLUG.get(normalized_slug)

    if plan is None:
        raise ValueError(f"Unknown subscription plan: {slug}")

    # Prevent accidental modification of the global defaults.
    return deepcopy(plan)


def get_plan_rank(slug: str) -> int:
    """
    Return the rank of a subscription plan.

    Unknown plans fall back to the Free plan rank.
    """
    normalized_slug = slug.strip().lower()
    return PLAN_RANK.get(normalized_slug, PLAN_RANK[FALLBACK_PLAN_SLUG])


def is_upgrade(current_plan: str, new_plan: str) -> bool:
    """
    Check whether changing plans represents an upgrade.
    """
    return get_plan_rank(new_plan) > get_plan_rank(current_plan)


def is_downgrade(current_plan: str, new_plan: str) -> bool:
    """
    Check whether changing plans represents a downgrade.
    """
    return get_plan_rank(new_plan) < get_plan_rank(current_plan)


def get_plan_price(
    slug: str,
    billing_cycle: str = "monthly",
) -> int:
    """
    Return the plan price in INR.

    Supported billing cycles:
        - monthly
        - yearly

    Raises:
        ValueError: If the plan or billing cycle is invalid.
    """
    plan = get_default_plan(slug)

    cycle = billing_cycle.strip().lower()

    if cycle == "monthly":
        return int(plan["monthly_price"])

    if cycle == "yearly":
        return int(plan["yearly_price"])

    raise ValueError(
        f"Invalid billing cycle: {billing_cycle}. "
        "Use 'monthly' or 'yearly'."
    )


def rupees_to_paise(amount_in_rupees: int | float) -> int:
    """
    Convert INR rupees to paise.

    Razorpay expects payment amounts in the smallest currency unit.
    Example:
        ₹499 -> 49900 paise
    """
    if amount_in_rupees < 0:
        raise ValueError("Amount cannot be negative.")

    return int(round(float(amount_in_rupees) * 100))


def get_feature_access(
    slug: str,
    feature_key: str,
) -> bool:
    """
    Check whether a plan has access to a specific feature.

    Unknown feature keys return False instead of accidentally granting access.
    """
    normalized_slug = slug.strip().lower()
    normalized_feature = feature_key.strip().lower()

    if normalized_feature not in FEATURE_KEYS:
        return False

    plan = PLAN_DEFAULTS_BY_SLUG.get(normalized_slug)

    if plan is None:
        plan = PLAN_DEFAULTS_BY_SLUG[FALLBACK_PLAN_SLUG]

    return bool(
        plan.get("features", {}).get(normalized_feature, False)
    )


def get_plan_limit(
    slug: str,
    limit_key: str,
) -> int:
    """
    Return a numeric limit for a plan.

    A value of -1 means unlimited.

    Raises:
        ValueError: If the plan or limit does not exist.
    """
    plan = get_default_plan(slug)

    limits = plan.get("limits", {})

    if limit_key not in limits:
        raise ValueError(
            f"Unknown limit '{limit_key}' for plan '{slug}'."
        )

    return int(limits[limit_key])


def is_unlimited_limit(
    slug: str,
    limit_key: str,
) -> bool:
    """
    Check whether a particular plan limit is unlimited.
    """
    return get_plan_limit(slug, limit_key) == -1