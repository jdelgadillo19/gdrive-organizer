"""Stable fingerprints for recommendations and clusters across runs."""

from __future__ import annotations

from kip_core.organization.models import DocumentCluster, OrganizationRecommendation


def recommendation_fingerprint(rec: OrganizationRecommendation) -> str:
    """Stable key for comparing recommendations across runs (ignores ephemeral IDs)."""
    impacted = ",".join(sorted(rec.impacted_file_ids))
    return "|".join(
        [
            rec.recommendation_type.value,
            rec.proposed_destination_path or "",
            rec.proposed_name or "",
            impacted,
        ]
    )


def cluster_fingerprint(cluster: DocumentCluster) -> str:
    """Stable key for cluster membership comparison across runs."""
    members = ",".join(sorted(cluster.member_file_ids))
    keywords = ",".join(cluster.top_keywords[:4])
    return "|".join([cluster.label, cluster.operational_role.value, keywords, members])


def cluster_member_sets(clusters: list[DocumentCluster]) -> list[frozenset[str]]:
    return [frozenset(c.member_file_ids) for c in clusters]


def recommendation_fingerprint_set(
    recommendations: list[OrganizationRecommendation],
) -> set[str]:
    return {recommendation_fingerprint(r) for r in recommendations}
