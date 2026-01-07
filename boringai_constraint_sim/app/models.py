"""
Data models for facility snapshots and evaluation results.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class HumanTrafficDensity(str, Enum):
    """Enumeration of valid human traffic density levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LayoutStability(str, Enum):
    """Enumeration of valid layout stability levels."""
    STABLE = "stable"
    MODERATE_CHANGE = "moderate_change"
    FREQUENT_CHANGE = "frequent_change"


class SafetyGovernanceMaturity(str, Enum):
    """Enumeration of valid safety governance maturity levels."""
    STRONG = "strong"
    AVERAGE = "average"
    WEAK = "weak"


class Verdict(str, Enum):
    """Evaluation verdict for facility eligibility."""
    QUALIFIED = "QUALIFIED"
    DISQUALIFIED = "DISQUALIFIED"
    UNKNOWN = "UNKNOWN"


@dataclass
class FacilitySnapshot:
    """
    Snapshot of a warehouse facility's characteristics for constraint evaluation.

    Required fields must be present and valid for a conclusive evaluation.
    Missing or invalid required fields will result in an UNKNOWN verdict.
    """
    # Required fields
    facility_name: str
    min_aisle_width_ft: float
    has_separated_paths: bool
    human_traffic_density: str
    has_closed_operating_window: bool
    layout_stability: str
    chronic_destination_saturation: bool
    tote_standardization: bool
    safety_governance_maturity: str

    # Optional fields
    notes: Optional[str] = None


@dataclass
class EvaluationResult:
    """
    Result of evaluating a facility snapshot against eligibility constraints.

    Attributes:
        verdict: Final determination (QUALIFIED, DISQUALIFIED, or UNKNOWN)
        disqualifiers: List of disqualifying rule violations
        caution_flags: List of caution flags (warnings that don't disqualify)
        missing_fields: List of required fields that were missing or invalid
        notes: Additional context and reasoning for the verdict
    """
    verdict: Verdict
    disqualifiers: List[str] = field(default_factory=list)
    caution_flags: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert the evaluation result to a dictionary suitable for JSON serialization."""
        return {
            "verdict": self.verdict.value,
            "disqualifiers": self.disqualifiers,
            "caution_flags": self.caution_flags,
            "missing_fields": self.missing_fields,
            "notes": self.notes
        }
