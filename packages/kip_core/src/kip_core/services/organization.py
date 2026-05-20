"""Organizational analysis service boundary (no automatic mutations)."""

from kip_core.organization.models import (
    AnalysisPreferences,
    FolderSelection,
    OrganizationAnalysisResult,
    ScannedDriveItem,
)
from kip_core.organization.recommendation_engine import run_organizational_analysis


class OrganizationService:
    """
    Facade for the organization engine within the modular monolith.

    Drive sync / scan workers supply ScannedDriveItem inventories; this service
    returns structured recommendations only.
    """

    def analyze_folder(
        self,
        selection: FolderSelection,
        items: list[ScannedDriveItem],
        preferences: AnalysisPreferences | None = None,
    ) -> OrganizationAnalysisResult:
        return run_organizational_analysis(selection, items, preferences)
