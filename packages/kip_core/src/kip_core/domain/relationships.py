from enum import StrEnum


class DocumentRelationshipType(StrEnum):
    SUPERSEDES = "supersedes"
    DUPLICATE_OF = "duplicate_of"
    RELATED_TO = "related_to"
    DERIVED_FROM = "derived_from"
    REFERENCES = "references"
    CONFLICTS_WITH = "conflicts_with"
