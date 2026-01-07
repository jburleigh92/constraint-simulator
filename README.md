# BoringAI Constraint Simulator

A deterministic governance tool for evaluating warehouse facility eligibility for the Empty Tote Return task.

## What This Tool Is

The Constraint Simulator is a **rule-based evaluation system** that assesses whether a warehouse facility meets the operational, safety, and infrastructure requirements for deploying Empty Tote Return automation. It provides one of three verdicts:

- **QUALIFIED**: Facility meets all requirements
- **DISQUALIFIED**: Facility violates one or more critical rules
- **UNKNOWN**: Required information is missing or invalid

The tool evaluates facilities against strict, deterministic constraints and provides detailed reports explaining the reasoning behind each verdict.

## What This Tool Is NOT

This is **NOT**:
- A robotics simulator
- A path planning or navigation tool
- A computer vision system
- An AI/ML prediction model
- A motion planning system
- A mapping or localization tool

It performs **constraint evaluation only** - no simulation of robot behavior, movement, or autonomy.

## Installation

No external dependencies required. The tool uses only Python standard library modules.

**Requirements**: Python 3.9 or higher

```bash
cd boringai_constraint_sim
```

## Usage

### Basic Usage

Evaluate a facility from a JSON file:

```bash
python -m app.cli examples/facility_eligible.json
```

### JSON Output Mode

For programmatic consumption:

```bash
python -m app.cli examples/facility_eligible.json --json
```

### Example Invocations

```bash
# Check the eligible facility example
python -m app.cli examples/facility_eligible.json

# Check the ineligible facility example
python -m app.cli examples/facility_ineligible.json

# Get JSON output for automation/scripting
python -m app.cli examples/facility_eligible.json --json
```

## Input Format

The tool accepts JSON files describing a facility snapshot. All required fields must be present with valid values.

### Required Fields

```json
{
  "facility_name": "string",
  "min_aisle_width_ft": 0.0,
  "has_separated_paths": true,
  "human_traffic_density": "low|medium|high",
  "has_closed_operating_window": true,
  "layout_stability": "stable|moderate_change|frequent_change",
  "chronic_destination_saturation": true,
  "tote_standardization": true,
  "safety_governance_maturity": "strong|average|weak"
}
```

### Optional Fields

- `notes`: String - Additional context about the facility

### Field Descriptions

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `facility_name` | string | any | Name of the warehouse facility |
| `min_aisle_width_ft` | float | > 0 | Minimum aisle width in feet |
| `has_separated_paths` | boolean | true/false | Whether human and automation paths are separated |
| `human_traffic_density` | enum | low, medium, high | Level of human foot traffic |
| `has_closed_operating_window` | boolean | true/false | Whether there's an off-hours deployment window |
| `layout_stability` | enum | stable, moderate_change, frequent_change | Frequency of facility layout changes |
| `chronic_destination_saturation` | boolean | true/false | Whether destinations are chronically saturated |
| `tote_standardization` | boolean | true/false | Whether tote containers are standardized |
| `safety_governance_maturity` | enum | strong, average, weak | Level of safety governance maturity |

## Output Format

### Human-Readable Report

Default output includes:
- Verdict (QUALIFIED, DISQUALIFIED, or UNKNOWN)
- List of disqualifiers (if any)
- List of caution flags (if any)
- Missing/invalid fields (if any)
- Evaluation notes with reasoning

Example:

```
======================================================================
CONSTRAINT SIMULATOR - EVALUATION REPORT
======================================================================

VERDICT: ✓ QUALIFIED

CAUTION FLAGS (2):
  • narrow_aisles
  • no_off_hours_window

EVALUATION NOTES:
  Facility 'Austin Distribution Center' is QUALIFIED for Empty Tote Return task.
  2 caution flag(s) identified:
    - narrow_aisles: Minimum aisle width below 8.0 feet
    - no_off_hours_window: No closed operating window available

======================================================================
```

### JSON Output

With `--json` flag:

```json
{
  "verdict": "QUALIFIED",
  "disqualifiers": [],
  "caution_flags": [
    "narrow_aisles",
    "no_off_hours_window"
  ],
  "missing_fields": [],
  "notes": [
    "Facility 'Austin Distribution Center' is QUALIFIED for Empty Tote Return task.",
    "2 caution flag(s) identified:",
    "  - narrow_aisles: Minimum aisle width below 8.0 feet",
    "  - no_off_hours_window: No closed operating window available"
  ]
}
```

## Exit Codes

The tool uses standard exit codes for easy integration with scripts and CI/CD:

| Exit Code | Meaning | Description |
|-----------|---------|-------------|
| 0 | QUALIFIED | Facility meets all requirements |
| 2 | DISQUALIFIED | Facility violates one or more rules |
| 3 | UNKNOWN | Required information missing or invalid |
| 1 | ERROR | Unexpected error occurred |

### Using Exit Codes in Scripts

```bash
python -m app.cli my_facility.json
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Facility is qualified!"
elif [ $EXIT_CODE -eq 2 ]; then
    echo "Facility is disqualified"
elif [ $EXIT_CODE -eq 3 ]; then
    echo "Cannot evaluate - missing data"
else
    echo "Error occurred"
fi
```

## Evaluation Rules

### Disqualifiers

If **any** of these conditions are true, the facility is **DISQUALIFIED**:

| Rule ID | Condition | Reason |
|---------|-----------|--------|
| `human_dense_shared_aisles` | `human_traffic_density == "high"` AND `has_separated_paths == false` | High human traffic without path separation creates safety risk |
| `chronic_destination_saturation` | `chronic_destination_saturation == true` | Chronic saturation prevents reliable automation |
| `unstable_layout` | `layout_stability == "frequent_change"` | Frequent layout changes make automation infeasible |
| `poor_safety_governance` | `safety_governance_maturity == "weak"` | Weak safety governance is incompatible with automation |
| `unclear_tote_standards` | `tote_standardization == false` | Non-standardized totes prevent reliable handling |

### Caution Flags

These conditions raise **warnings** but do not disqualify a facility:

| Flag ID | Condition | Warning |
|---------|-----------|---------|
| `narrow_aisles` | `min_aisle_width_ft < 8.0` | Narrow aisles may limit maneuverability |
| `mixed_traffic_no_separation` | `human_traffic_density == "medium"` AND `has_separated_paths == false` | Mixed traffic requires additional safety measures |
| `layout_drift_risk` | `layout_stability == "moderate_change"` | Moderate layout changes require monitoring |
| `no_off_hours_window` | `has_closed_operating_window == false` | Lack of off-hours window complicates deployment |
| `average_safety_maturity` | `safety_governance_maturity == "average"` | Average safety maturity may need enhancement |

### Evaluation Logic

1. **Validation**: Check that all required fields are present with valid types and values
   - If validation fails → **UNKNOWN**
2. **Disqualifier Check**: Evaluate all disqualifier rules
   - If any disqualifier triggers → **DISQUALIFIED**
3. **Caution Flag Check**: Evaluate all caution flag rules
   - Caution flags are reported but do not affect verdict
4. **Final Verdict**: If no disqualifiers and validation passes → **QUALIFIED**

## Running Tests

The tool includes comprehensive unit tests using Python's built-in `unittest` module.

Run all tests:

```bash
python -m unittest discover tests
```

Run tests with verbose output:

```bash
python -m unittest discover tests -v
```

Run a specific test class:

```bash
python -m unittest tests.test_evaluator.TestQualifiedFacility
```

### Test Coverage

Tests cover:
- ✅ QUALIFIED facilities (perfect and with caution flags)
- ✅ DISQUALIFIED facilities (each disqualifier type)
- ✅ UNKNOWN verdicts (missing fields, invalid types, invalid enums)
- ✅ Individual rule triggering logic
- ✅ Edge cases (e.g., high traffic WITH separation)

## Project Structure

```
boringai_constraint_sim/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── models.py            # Data models (FacilitySnapshot, EvaluationResult)
│   ├── rules.py             # Rule definitions (disqualifiers, caution flags)
│   ├── evaluator.py         # Constraint evaluation logic
│   └── cli.py               # Command-line interface
├── examples/
│   ├── facility_eligible.json    # Example QUALIFIED facility
│   └── facility_ineligible.json  # Example DISQUALIFIED facility
├── tests/
│   └── test_evaluator.py    # Comprehensive unit tests
├── README.md                # This file
└── requirements.txt         # Python dependencies (none)
```

## Development Guidelines

### Design Principles

1. **Deterministic**: Same input always produces same output
2. **Rule-Based**: No ML, AI, or randomness
3. **Transparent**: Every verdict includes clear reasoning
4. **Type-Safe**: Full type hints throughout
5. **Testable**: Comprehensive unit test coverage
6. **Simple**: No unnecessary abstractions or complexity

### Adding New Rules

To add a new disqualifier rule:

1. Add a `Rule` instance to `DISQUALIFIER_RULES` in `app/rules.py`
2. Add test cases in `tests/test_evaluator.py`
3. Update this README's rule documentation

To add a new caution flag:

1. Add a `Rule` instance to `CAUTION_FLAG_RULES` in `app/rules.py`
2. Add test cases in `tests/test_evaluator.py`
3. Update this README's rule documentation

### Code Style

- Use type hints for all function signatures
- Write clear docstrings for all public functions and classes
- Keep functions focused and single-purpose
- Handle errors gracefully with actionable messages
- Prefer simplicity over cleverness

## Frequently Asked Questions

**Q: Why is my facility showing UNKNOWN?**
A: Check that all required fields are present in your JSON file and have valid values. The error message will list specific missing or invalid fields.

**Q: Can a facility with caution flags still be QUALIFIED?**
A: Yes! Caution flags are warnings that indicate potential concerns but do not disqualify a facility. They should be reviewed and addressed, but they don't prevent qualification.

**Q: What's the difference between this and a robotics simulator?**
A: This tool only evaluates **eligibility constraints**. It does not simulate robot motion, path planning, navigation, or any physical behavior. It's a governance/decision tool, not a simulation tool.

**Q: Can I use this tool in automated workflows?**
A: Yes! Use the `--json` flag for machine-readable output and check the exit code to determine the verdict programmatically.

**Q: Is the evaluation deterministic?**
A: Yes, absolutely. The same input will always produce the same output. There is no randomness, ML, or AI involved - only rule-based logic.

## License

This is a demonstration project for constraint-based facility evaluation.

## Support

For issues or questions, refer to the rule definitions in this README and the comprehensive test suite in `tests/test_evaluator.py`.
