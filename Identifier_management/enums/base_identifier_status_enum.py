from enum import Enum


class BaseIdentifierStatusEnum(Enum, str):
    """Base identifier statuses"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    SUPERSEDED = "SUPERSEDED"
    ERROR = "ERROR"
