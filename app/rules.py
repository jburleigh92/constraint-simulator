"""
Rule definitions for facility constraint evaluation.

This module defines the disqualifying rules and caution flags
used to determine facility eligibility for the Empty Tote Return task.
"""

from typing import List, Callable
from app.models import FacilitySnapshot


class Rule:
    """
    Represents a single evaluation rule.

    Attributes:
        name: Unique identifier for the rule
        description: Human-readable explanation of the rule
        check: Function that returns True if the rule is triggered
    """

    def __init__(
        self,
        name: str,
        description: str,
        check: Callable[[FacilitySnapshot], bool]
    ):
        self.name = name
        self.description = description
        self.check = check

    def evaluate(self, facility: FacilitySnapshot) -> bool:
        """Evaluate the rule against a facility snapshot."""
        return self.check(facility)


# DISQUALIFIER RULES
# If any of these rules trigger, the facility is DISQUALIFIED

DISQUALIFIER_RULES: List[Rule] = [
    Rule(
        name="human_dense_shared_aisles",
        description="High human traffic density without separated paths",
        check=lambda f: f.human_traffic_density == "high" and not f.has_separated_paths
    ),
    Rule(
        name="chronic_destination_saturation",
        description="Chronic destination saturation detected",
        check=lambda f: f.chronic_destination_saturation
    ),
    Rule(
        name="unstable_layout",
        description="Facility layout changes frequently",
        check=lambda f: f.layout_stability == "frequent_change"
    ),
    Rule(
        name="poor_safety_governance",
        description="Weak safety governance maturity",
        check=lambda f: f.safety_governance_maturity == "weak"
    ),
    Rule(
        name="unclear_tote_standards",
        description="Tote standardization not established",
        check=lambda f: not f.tote_standardization
    ),
]


# CAUTION FLAG RULES
# These rules raise warnings but do not disqualify a facility on their own

CAUTION_FLAG_RULES: List[Rule] = [
    Rule(
        name="narrow_aisles",
        description="Minimum aisle width below 8.0 feet",
        check=lambda f: f.min_aisle_width_ft < 8.0
    ),
    Rule(
        name="mixed_traffic_no_separation",
        description="Medium human traffic without separated paths",
        check=lambda f: f.human_traffic_density == "medium" and not f.has_separated_paths
    ),
    Rule(
        name="layout_drift_risk",
        description="Moderate layout change frequency",
        check=lambda f: f.layout_stability == "moderate_change"
    ),
    Rule(
        name="no_off_hours_window",
        description="No closed operating window available",
        check=lambda f: not f.has_closed_operating_window
    ),
    Rule(
        name="average_safety_maturity",
        description="Average safety governance maturity",
        check=lambda f: f.safety_governance_maturity == "average"
    ),
]


def get_triggered_disqualifiers(facility: FacilitySnapshot) -> List[str]:
    """
    Evaluate all disqualifier rules and return a list of triggered rule names.

    Args:
        facility: The facility snapshot to evaluate

    Returns:
        List of disqualifier rule names that were triggered
    """
    triggered = []
    for rule in DISQUALIFIER_RULES:
        if rule.evaluate(facility):
            triggered.append(rule.name)
    return triggered


def get_triggered_caution_flags(facility: FacilitySnapshot) -> List[str]:
    """
    Evaluate all caution flag rules and return a list of triggered rule names.

    Args:
        facility: The facility snapshot to evaluate

    Returns:
        List of caution flag rule names that were triggered
    """
    triggered = []
    for rule in CAUTION_FLAG_RULES:
        if rule.evaluate(facility):
            triggered.append(rule.name)
    return triggered


def get_rule_description(rule_name: str) -> str:
    """
    Get the human-readable description for a rule name.

    Args:
        rule_name: The name of the rule

    Returns:
        Description of the rule, or the rule name if not found
    """
    all_rules = DISQUALIFIER_RULES + CAUTION_FLAG_RULES
    for rule in all_rules:
        if rule.name == rule_name:
            return rule.description
    return rule_name
