from enum import Enum


class PortfolioStatusEnum(str, Enum):
    """Lifecycle status of a portfolio"""
    DRAFT = "DRAFT"  # Portfolio being constructed
    PENDING_APPROVAL = "PENDING_APPROVAL"  # Awaiting regulatory/internal approval
    ACTIVE = "ACTIVE"  # Currently operating
    SUSPENDED = "SUSPENDED"  # Temporarily halted
    CLOSED_TO_NEW_INVESTORS = "CLOSED_TO_NEW_INVESTORS"  # No new subscriptions
    LIQUIDATING = "LIQUIDATING"  # In process of winding down
    TERMINATED = "TERMINATED"  # Fully closed
    FROZEN = "FROZEN"  # Trading halted due to regulatory action
    UNDER_REVIEW = "UNDER_REVIEW"  # Compliance or performance review
    RESTRUCTURING = "RESTRUCTURING"  # Undergoing structural changes
