from kip_core.domain.governance import (
    AuthorityLevel,
    LifecycleStatus,
    is_retrieval_eligible,
)


def test_archived_lifecycle_not_eligible() -> None:
    assert not is_retrieval_eligible(AuthorityLevel.APPROVED, LifecycleStatus.ARCHIVED)


def test_archived_authority_not_eligible() -> None:
    assert not is_retrieval_eligible(AuthorityLevel.ARCHIVED, LifecycleStatus.ACTIVE)


def test_canonical_active_is_eligible() -> None:
    assert is_retrieval_eligible(AuthorityLevel.CANONICAL, LifecycleStatus.ACTIVE)
