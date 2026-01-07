"""
Unit tests for the constraint evaluator.

Tests cover all key scenarios:
- QUALIFIED facilities
- DISQUALIFIED facilities (multiple disqualifier types)
- UNKNOWN verdicts (missing/invalid fields)
- Individual rule triggering
- Edge cases
"""

import unittest
from app.models import FacilitySnapshot, Verdict
from app.evaluator import ConstraintEvaluator
from app.rules import get_triggered_disqualifiers, get_triggered_caution_flags


class TestQualifiedFacility(unittest.TestCase):
    """Test cases for facilities that should be QUALIFIED."""

    def test_perfect_facility(self):
        """Test a facility that meets all requirements with no caution flags."""
        facility = FacilitySnapshot(
            facility_name="Perfect Warehouse",
            min_aisle_width_ft=12.0,
            has_separated_paths=True,
            human_traffic_density="low",
            has_closed_operating_window=True,
            layout_stability="stable",
            chronic_destination_saturation=False,
            tote_standardization=True,
            safety_governance_maturity="strong"
        )

        result = ConstraintEvaluator.evaluate(facility)

        self.assertEqual(result.verdict, Verdict.QUALIFIED)
        self.assertEqual(len(result.disqualifiers), 0)
        self.assertEqual(len(result.caution_flags), 0)

    def test_qualified_with_caution_flags(self):
        """Test a facility that qualifies but has caution flags."""
        facility = FacilitySnapshot(
            facility_name="Decent Warehouse",
            min_aisle_width_ft=7.5,  # Triggers narrow_aisles
            has_separated_paths=True,
            human_traffic_density="low",
            has_closed_operating_window=False,  # Triggers no_off_hours_window
            layout_stability="stable",
            chronic_destination_saturation=False,
            tote_standardization=True,
            safety_governance_maturity="average"  # Triggers average_safety_maturity
        )

        result = ConstraintEvaluator.evaluate(facility)

        self.assertEqual(result.verdict, Verdict.QUALIFIED)
        self.assertEqual(len(result.disqualifiers), 0)
        self.assertGreater(len(result.caution_flags), 0)
        self.assertIn("narrow_aisles", result.caution_flags)
        self.assertIn("no_off_hours_window", result.caution_flags)
        self.assertIn("average_safety_maturity", result.caution_flags)


class TestDisqualifiedFacility(unittest.TestCase):
    """Test cases for facilities that should be DISQUALIFIED."""

    def test_high_traffic_no_separation(self):
        """Test disqualification due to high traffic without separated paths."""
        facility = FacilitySnapshot(
            facility_name="Busy Warehouse",
            min_aisle_width_ft=10.0,
            has_separated_paths=False,
            human_traffic_density="high",
            has_closed_operating_window=True,
            layout_stability="stable",
            chronic_destination_saturation=False,
            tote_standardization=True,
            safety_governance_maturity="strong"
        )

        result = ConstraintEvaluator.evaluate(facility)

        self.assertEqual(result.verdict, Verdict.DISQUALIFIED)
        self.assertIn("human_dense_shared_aisles", result.disqualifiers)

    def test_chronic_saturation(self):
        """Test disqualification due to chronic destination saturation."""
        facility = FacilitySnapshot(
            facility_name="Saturated Warehouse",
            min_aisle_width_ft=10.0,
            has_separated_paths=True,
            human_traffic_density="low",
            has_closed_operating_window=True,
            layout_stability="stable",
            chronic_destination_saturation=True,
            tote_standardization=True,
            safety_governance_maturity="strong"
        )

        result = ConstraintEvaluator.evaluate(facility)

        self.assertEqual(result.verdict, Verdict.DISQUALIFIED)
        self.assertIn("chronic_destination_saturation", result.disqualifiers)

    def test_unstable_layout(self):
        """Test disqualification due to frequent layout changes."""
        facility = FacilitySnapshot(
            facility_name="Unstable Warehouse",
            min_aisle_width_ft=10.0,
            has_separated_paths=True,
            human_traffic_density="low",
            has_closed_operating_window=True,
            layout_stability="frequent_change",
            chronic_destination_saturation=False,
            tote_standardization=True,
            safety_governance_maturity="strong"
        )

        result = ConstraintEvaluator.evaluate(facility)

        self.assertEqual(result.verdict, Verdict.DISQUALIFIED)
        self.assertIn("unstable_layout", result.disqualifiers)

    def test_poor_safety_governance(self):
        """Test disqualification due to weak safety governance."""
        facility = FacilitySnapshot(
            facility_name="Unsafe Warehouse",
            min_aisle_width_ft=10.0,
            has_separated_paths=True,
            human_traffic_density="low",
            has_closed_operating_window=True,
            layout_stability="stable",
            chronic_destination_saturation=False,
            tote_standardization=True,
            safety_governance_maturity="weak"
        )

        result = ConstraintEvaluator.evaluate(facility)

        self.assertEqual(result.verdict, Verdict.DISQUALIFIED)
        self.assertIn("poor_safety_governance", result.disqualifiers)

    def test_no_tote_standardization(self):
        """Test disqualification due to lack of tote standardization."""
        facility = FacilitySnapshot(
            facility_name="Non-Standard Warehouse",
            min_aisle_width_ft=10.0,
            has_separated_paths=True,
            human_traffic_density="low",
            has_closed_operating_window=True,
            layout_stability="stable",
            chronic_destination_saturation=False,
            tote_standardization=False,
            safety_governance_maturity="strong"
        )

        result = ConstraintEvaluator.evaluate(facility)

        self.assertEqual(result.verdict, Verdict.DISQUALIFIED)
        self.assertIn("unclear_tote_standards", result.disqualifiers)

    def test_multiple_disqualifiers(self):
        """Test facility with multiple disqualifying issues."""
        facility = FacilitySnapshot(
            facility_name="Problem Warehouse",
            min_aisle_width_ft=10.0,
            has_separated_paths=False,
            human_traffic_density="high",
            has_closed_operating_window=True,
            layout_stability="frequent_change",
            chronic_destination_saturation=True,
            tote_standardization=False,
            safety_governance_maturity="weak"
        )

        result = ConstraintEvaluator.evaluate(facility)

        self.assertEqual(result.verdict, Verdict.DISQUALIFIED)
        # Should have multiple disqualifiers
        self.assertGreaterEqual(len(result.disqualifiers), 2)


class TestUnknownVerdict(unittest.TestCase):
    """Test cases for UNKNOWN verdicts due to missing or invalid data."""

    def test_missing_required_field(self):
        """Test that missing required fields result in UNKNOWN verdict."""
        data = {
            "facility_name": "Incomplete Warehouse",
            "min_aisle_width_ft": 10.0,
            # Missing has_separated_paths
            "human_traffic_density": "low",
            "has_closed_operating_window": True,
            "layout_stability": "stable",
            "chronic_destination_saturation": False,
            "tote_standardization": True,
            "safety_governance_maturity": "strong"
        }

        result = ConstraintEvaluator.evaluate_from_dict(data)

        self.assertEqual(result.verdict, Verdict.UNKNOWN)
        self.assertGreater(len(result.missing_fields), 0)

    def test_invalid_enum_value(self):
        """Test that invalid enum values result in UNKNOWN verdict."""
        data = {
            "facility_name": "Bad Data Warehouse",
            "min_aisle_width_ft": 10.0,
            "has_separated_paths": True,
            "human_traffic_density": "very_high",  # Invalid value
            "has_closed_operating_window": True,
            "layout_stability": "stable",
            "chronic_destination_saturation": False,
            "tote_standardization": True,
            "safety_governance_maturity": "strong"
        }

        result = ConstraintEvaluator.evaluate_from_dict(data)

        self.assertEqual(result.verdict, Verdict.UNKNOWN)
        self.assertGreater(len(result.missing_fields), 0)

    def test_wrong_type(self):
        """Test that wrong field types result in UNKNOWN verdict."""
        data = {
            "facility_name": "Type Error Warehouse",
            "min_aisle_width_ft": "ten",  # Should be float
            "has_separated_paths": True,
            "human_traffic_density": "low",
            "has_closed_operating_window": True,
            "layout_stability": "stable",
            "chronic_destination_saturation": False,
            "tote_standardization": True,
            "safety_governance_maturity": "strong"
        }

        result = ConstraintEvaluator.evaluate_from_dict(data)

        self.assertEqual(result.verdict, Verdict.UNKNOWN)
        self.assertGreater(len(result.missing_fields), 0)


class TestCautionFlags(unittest.TestCase):
    """Test individual caution flag rules."""

    def test_narrow_aisles_flag(self):
        """Test that narrow aisles trigger the caution flag."""
        facility = FacilitySnapshot(
            facility_name="Narrow Warehouse",
            min_aisle_width_ft=6.0,
            has_separated_paths=True,
            human_traffic_density="low",
            has_closed_operating_window=True,
            layout_stability="stable",
            chronic_destination_saturation=False,
            tote_standardization=True,
            safety_governance_maturity="strong"
        )

        caution_flags = get_triggered_caution_flags(facility)
        self.assertIn("narrow_aisles", caution_flags)

    def test_mixed_traffic_no_separation_flag(self):
        """Test that medium traffic without separation triggers caution."""
        facility = FacilitySnapshot(
            facility_name="Mixed Traffic Warehouse",
            min_aisle_width_ft=10.0,
            has_separated_paths=False,
            human_traffic_density="medium",
            has_closed_operating_window=True,
            layout_stability="stable",
            chronic_destination_saturation=False,
            tote_standardization=True,
            safety_governance_maturity="strong"
        )

        caution_flags = get_triggered_caution_flags(facility)
        self.assertIn("mixed_traffic_no_separation", caution_flags)

    def test_layout_drift_risk_flag(self):
        """Test that moderate layout changes trigger caution."""
        facility = FacilitySnapshot(
            facility_name="Changing Warehouse",
            min_aisle_width_ft=10.0,
            has_separated_paths=True,
            human_traffic_density="low",
            has_closed_operating_window=True,
            layout_stability="moderate_change",
            chronic_destination_saturation=False,
            tote_standardization=True,
            safety_governance_maturity="strong"
        )

        caution_flags = get_triggered_caution_flags(facility)
        self.assertIn("layout_drift_risk", caution_flags)


class TestRuleLogic(unittest.TestCase):
    """Test specific rule logic and edge cases."""

    def test_high_traffic_with_separation_no_disqualifier(self):
        """Test that high traffic WITH separated paths does not disqualify."""
        facility = FacilitySnapshot(
            facility_name="Safe High Traffic Warehouse",
            min_aisle_width_ft=10.0,
            has_separated_paths=True,  # This should prevent disqualification
            human_traffic_density="high",
            has_closed_operating_window=True,
            layout_stability="stable",
            chronic_destination_saturation=False,
            tote_standardization=True,
            safety_governance_maturity="strong"
        )

        disqualifiers = get_triggered_disqualifiers(facility)
        self.assertNotIn("human_dense_shared_aisles", disqualifiers)

        result = ConstraintEvaluator.evaluate(facility)
        self.assertEqual(result.verdict, Verdict.QUALIFIED)

    def test_medium_traffic_with_separation_no_caution(self):
        """Test that medium traffic WITH separated paths has no mixed traffic flag."""
        facility = FacilitySnapshot(
            facility_name="Safe Medium Traffic Warehouse",
            min_aisle_width_ft=10.0,
            has_separated_paths=True,  # This should prevent caution flag
            human_traffic_density="medium",
            has_closed_operating_window=True,
            layout_stability="stable",
            chronic_destination_saturation=False,
            tote_standardization=True,
            safety_governance_maturity="strong"
        )

        caution_flags = get_triggered_caution_flags(facility)
        self.assertNotIn("mixed_traffic_no_separation", caution_flags)


if __name__ == "__main__":
    unittest.main()
