from enum import StrEnum


class AuthorityLevel(StrEnum):
    CANONICAL = "canonical"
    APPROVED = "approved"
    DRAFT = "draft"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class LifecycleStatus(StrEnum):
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


AUTHORITY_WEIGHTS: dict[AuthorityLevel, float] = {
    AuthorityLevel.CANONICAL: 1.0,
    AuthorityLevel.APPROVED: 0.8,
    AuthorityLevel.DRAFT: 0.5,
    AuthorityLevel.DEPRECATED: 0.2,
    AuthorityLevel.ARCHIVED: 0.1,
}


def authority_weight(level: AuthorityLevel) -> float:
    return AUTHORITY_WEIGHTS[level]


def is_retrieval_eligible(
    authority_level: AuthorityLevel,
    lifecycle_status: LifecycleStatus,
) -> bool:
    """Archived lifecycle excludes documents from standard retrieval."""
    if lifecycle_status == LifecycleStatus.ARCHIVED:
        return False
    if authority_level == AuthorityLevel.ARCHIVED:
        return False
    return True
