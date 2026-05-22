"""LaunchBuild1 canon topic definitions and cross-reference pairs."""

from __future__ import annotations

from dataclasses import dataclass

from kip_core.canon.models import CanonTopicId


@dataclass(frozen=True)
class CanonTopicDefinition:
    topic_id: CanonTopicId
    title: str
    description: str
    path_keywords: frozenset[str]
    name_keywords: frozenset[str]
    content_keywords: frozenset[str]


CANON_TOPICS: tuple[CanonTopicDefinition, ...] = (
    CanonTopicDefinition(
        topic_id=CanonTopicId.ROLE_DESCRIPTIONS,
        title="Role descriptions",
        description=(
            "Leadership and Members, Music and Tech, Prep and Perform — "
            "official role expectations by team."
        ),
        path_keywords=frozenset(
            {"role", "roles", "leadership", "platform team", "music team", "tech team", "stage team"}
        ),
        name_keywords=frozenset(
            {"role", "roles", "leadership", "position guide", "dress code", "worship leader tasks"}
        ),
        content_keywords=frozenset(
            {"responsibilit", "role", "leader", "member", "team", "expect", "duties"}
        ),
    ),
    CanonTopicDefinition(
        topic_id=CanonTopicId.MASTER_SUNDAY_SERVICE_PLAN,
        title="Master Sunday Service Plan",
        description="Authoritative outline for Sunday / weekend service flow and order.",
        path_keywords=frozenset({"service order", "weekend", "sunday", "tech checklist"}),
        name_keywords=frozenset(
            {"service order", "sunday", "weekend", "flow timeline", "operations checklist"}
        ),
        content_keywords=frozenset(
            {"sunday", "service", "order", "weekend", "worship", "run sheet", "timeline"}
        ),
    ),
    CanonTopicDefinition(
        topic_id=CanonTopicId.WEEKLY_PREP_PLAN,
        title="Weekly Prep Plan",
        description="Weekly preparation, flow timelines, and operational prep checklists.",
        path_keywords=frozenset({"weekly", "prep", "flow", "timeline", "checklist", "planning"}),
        name_keywords=frozenset(
            {"weekly", "flow timeline", "prep", "checklist", "planning", "meeting notes"}
        ),
        content_keywords=frozenset(
            {"weekly", "prep", "rehearsal", "timeline", "before service", "planning"}
        ),
    ),
    CanonTopicDefinition(
        topic_id=CanonTopicId.NEW_VOLUNTEER_ONBOARDING,
        title="New Volunteer Onboarding",
        description="Onboarding paths for new volunteers across production, music, and tech.",
        path_keywords=frozenset({"onboarding", "volunteer", "audition", "new volunteer"}),
        name_keywords=frozenset({"onboarding", "audition", "volunteer", "training seminar"}),
        content_keywords=frozenset(
            {"onboard", "volunteer", "new member", "audition", "orientation", "training"}
        ),
    ),
)


@dataclass(frozen=True)
class CrossReferencePair:
    """Documents that should be reconciled when both exist."""

    label: str
    path_a_contains: str
    path_b_contains: str
    kind: str = "same_topic_reconcile"


CROSS_REFERENCE_PAIRS: tuple[CrossReferencePair, ...] = (
    CrossReferencePair(
        label="Weekly flow timeline variants",
        path_a_contains="Weekly Flow Timeline.docx",
        path_b_contains="Weekly Flow Timeline(1)",
    ),
    CrossReferencePair(
        label="Sunday service order vs weekly flow",
        path_a_contains="Service Order Outline",
        path_b_contains="Weekly Flow Timeline",
    ),
    CrossReferencePair(
        label="Platform role descriptions vs leadership roles",
        path_a_contains="Role Descriptions",
        path_b_contains="Leadership Roles",
    ),
    CrossReferencePair(
        label="Worship leader tasks vs weekly flow",
        path_a_contains="Worship Leader Tasks",
        path_b_contains="Weekly Flow Timeline",
    ),
    CrossReferencePair(
        label="Vision and values (doc vs deck)",
        path_a_contains="Vision & Values.docx",
        path_b_contains="Vision & Values.pptx",
    ),
)
