"""
Facility constraint evaluator.

This module orchestrates the evaluation of facility snapshots
against eligibility rules, producing deterministic verdicts.
"""

import json
from typing import Dict, Any, List
from app.models import (
    FacilitySnapshot,
    EvaluationResult,
    Verdict,
    HumanTrafficDensity,
    LayoutStability,
    SafetyGovernanceMaturity
)
from app.rules import (
    get_triggered_disqualifiers,
    get_triggered_caution_flags,
    get_rule_description
)


class ConstraintEvaluator:
    """
    Evaluates warehouse facilities against eligibility constraints.

    This is a deterministic, rule-based evaluator that produces one of three verdicts:
    - QUALIFIED: Facility meets all requirements
    - DISQUALIFIED: Facility violates one or more disqualifying rules
    - UNKNOWN: Required information is missing or invalid
    """

    REQUIRED_FIELDS = {
        "facility_name": str,
        "min_aisle_width_ft": (int, float),
        "has_separated_paths": bool,
        "human_traffic_density": str,
        "has_closed_operating_window": bool,
        "layout_stability": str,
        "chronic_destination_saturation": bool,
        "tote_standardization": bool,
        "safety_governance_maturity": str,
    }

    @staticmethod
    def load_facility_from_json(file_path: str) -> Dict[str, Any]:
        """
        Load facility data from a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Dictionary containing facility data

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        with open(file_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def validate_and_parse(data: Dict[str, Any]) -> tuple[FacilitySnapshot | None, List[str]]:
        """
        Validate facility data and parse into a FacilitySnapshot.

        Args:
            data: Dictionary containing facility data

        Returns:
            Tuple of (FacilitySnapshot or None, list of validation errors)
        """
        missing_fields = []
        invalid_fields = []

        # Check required fields exist and have correct types
        for field_name, expected_type in ConstraintEvaluator.REQUIRED_FIELDS.items():
            if field_name not in data:
                missing_fields.append(f"{field_name} (missing)")
            else:
                value = data[field_name]
                if not isinstance(value, expected_type):
                    invalid_fields.append(
                        f"{field_name} (expected {expected_type}, got {type(value).__name__})"
                    )

        # Validate enum values
        if "human_traffic_density" in data:
            valid_densities = {e.value for e in HumanTrafficDensity}
            if data["human_traffic_density"] not in valid_densities:
                invalid_fields.append(
                    f"human_traffic_density (invalid value '{data['human_traffic_density']}', "
                    f"expected one of {valid_densities})"
                )

        if "layout_stability" in data:
            valid_stabilities = {e.value for e in LayoutStability}
            if data["layout_stability"] not in valid_stabilities:
                invalid_fields.append(
                    f"layout_stability (invalid value '{data['layout_stability']}', "
                    f"expected one of {valid_stabilities})"
                )

        if "safety_governance_maturity" in data:
            valid_maturities = {e.value for e in SafetyGovernanceMaturity}
            if data["safety_governance_maturity"] not in valid_maturities:
                invalid_fields.append(
                    f"safety_governance_maturity (invalid value '{data['safety_governance_maturity']}', "
                    f"expected one of {valid_maturities})"
                )

        # If there are validation errors, return None and the error list
        all_errors = missing_fields + invalid_fields
        if all_errors:
            return None, all_errors

        # Parse into FacilitySnapshot
        try:
            facility = FacilitySnapshot(
                facility_name=data["facility_name"],
                min_aisle_width_ft=float(data["min_aisle_width_ft"]),
                has_separated_paths=data["has_separated_paths"],
                human_traffic_density=data["human_traffic_density"],
                has_closed_operating_window=data["has_closed_operating_window"],
                layout_stability=data["layout_stability"],
                chronic_destination_saturation=data["chronic_destination_saturation"],
                tote_standardization=data["tote_standardization"],
                safety_governance_maturity=data["safety_governance_maturity"],
                notes=data.get("notes")
            )
            return facility, []
        except Exception as e:
            return None, [f"Parsing error: {str(e)}"]

    @staticmethod
    def evaluate(facility: FacilitySnapshot) -> EvaluationResult:
        """
        Evaluate a facility snapshot against all eligibility rules.

        Evaluation logic:
        1. Check for disqualifiers - if any trigger, verdict is DISQUALIFIED
        2. Check for caution flags - these are included in the report
        3. If no disqualifiers, verdict is QUALIFIED

        Args:
            facility: The facility snapshot to evaluate

        Returns:
            EvaluationResult with verdict and detailed findings
        """
        # Evaluate disqualifiers
        disqualifiers = get_triggered_disqualifiers(facility)

        # Evaluate caution flags
        caution_flags = get_triggered_caution_flags(facility)

        # Determine verdict
        if disqualifiers:
            verdict = Verdict.DISQUALIFIED
            notes = [
                f"Facility '{facility.facility_name}' is DISQUALIFIED due to {len(disqualifiers)} "
                f"rule violation(s)."
            ]
            for disq in disqualifiers:
                notes.append(f"  - {disq}: {get_rule_description(disq)}")
        else:
            verdict = Verdict.QUALIFIED
            notes = [
                f"Facility '{facility.facility_name}' is QUALIFIED for Empty Tote Return task."
            ]

        # Add caution flag information
        if caution_flags:
            notes.append(f"{len(caution_flags)} caution flag(s) identified:")
            for flag in caution_flags:
                notes.append(f"  - {flag}: {get_rule_description(flag)}")

        return EvaluationResult(
            verdict=verdict,
            disqualifiers=disqualifiers,
            caution_flags=caution_flags,
            notes=notes
        )

    @staticmethod
    def evaluate_from_dict(data: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate facility data from a dictionary.

        This method validates the input data and returns an UNKNOWN verdict
        if validation fails.

        Args:
            data: Dictionary containing facility data

        Returns:
            EvaluationResult with verdict and detailed findings
        """
        facility, validation_errors = ConstraintEvaluator.validate_and_parse(data)

        if validation_errors:
            # Return UNKNOWN verdict with validation errors
            notes = ["Cannot evaluate: required information is missing or invalid."]
            notes.extend(validation_errors)
            return EvaluationResult(
                verdict=Verdict.UNKNOWN,
                missing_fields=validation_errors,
                notes=notes
            )

        # Perform evaluation
        return ConstraintEvaluator.evaluate(facility)

    @staticmethod
    def evaluate_from_file(file_path: str) -> EvaluationResult:
        """
        Load and evaluate a facility from a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            EvaluationResult with verdict and detailed findings

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        data = ConstraintEvaluator.load_facility_from_json(file_path)
        return ConstraintEvaluator.evaluate_from_dict(data)
