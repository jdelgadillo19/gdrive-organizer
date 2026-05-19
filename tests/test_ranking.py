from kip_core.domain.governance import AuthorityLevel
from kip_core.domain.ranking import RankingSignals, rank_candidates


def test_canonical_outranks_draft_despite_lower_semantic() -> None:
    candidates = [
        (
            "doc-draft",
            None,
            RankingSignals(
                semantic_score=0.88,
                authority_level=AuthorityLevel.DRAFT,
                freshness_score=1.0,
            ),
        ),
        (
            "doc-canonical",
            None,
            RankingSignals(
                semantic_score=0.85,
                authority_level=AuthorityLevel.CANONICAL,
                freshness_score=0.9,
            ),
        ),
    ]
    ranked = rank_candidates(candidates)
    assert ranked[0].document_id == "doc-canonical"


def test_explanation_includes_weighted_components() -> None:
    signals = RankingSignals(
        semantic_score=0.8,
        authority_level=AuthorityLevel.APPROVED,
        freshness_score=0.9,
    )
    ranked = rank_candidates([("doc-1", "chunk-1", signals)])
    assert "semantic" in ranked[0].explanation
    assert "authority" in ranked[0].explanation
