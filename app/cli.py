"""
Command-line interface for the Constraint Simulator.

Provides both human-readable and JSON output modes for facility evaluation.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import NoReturn
from app.evaluator import ConstraintEvaluator
from app.models import Verdict, EvaluationResult


def print_human_readable_report(result: EvaluationResult) -> None:
    """
    Print a human-readable evaluation report to stdout.

    Args:
        result: The evaluation result to display
    """
    print("=" * 70)
    print("CONSTRAINT SIMULATOR - EVALUATION REPORT")
    print("=" * 70)
    print()

    # Verdict
    verdict_display = result.verdict.value
    if result.verdict == Verdict.QUALIFIED:
        verdict_symbol = "✓"
    elif result.verdict == Verdict.DISQUALIFIED:
        verdict_symbol = "✗"
    else:
        verdict_symbol = "?"

    print(f"VERDICT: {verdict_symbol} {verdict_display}")
    print()

    # Disqualifiers
    if result.disqualifiers:
        print(f"DISQUALIFIERS ({len(result.disqualifiers)}):")
        for disq in result.disqualifiers:
            print(f"  • {disq}")
        print()

    # Caution flags
    if result.caution_flags:
        print(f"CAUTION FLAGS ({len(result.caution_flags)}):")
        for flag in result.caution_flags:
            print(f"  • {flag}")
        print()

    # Missing fields
    if result.missing_fields:
        print(f"MISSING/INVALID FIELDS ({len(result.missing_fields)}):")
        for field in result.missing_fields:
            print(f"  • {field}")
        print()

    # Notes
    if result.notes:
        print("EVALUATION NOTES:")
        for note in result.notes:
            print(f"  {note}")
        print()

    print("=" * 70)


def print_json_report(result: EvaluationResult) -> None:
    """
    Print a JSON-formatted evaluation report to stdout.

    Args:
        result: The evaluation result to display
    """
    print(json.dumps(result.to_dict(), indent=2))


def get_exit_code(verdict: Verdict) -> int:
    """
    Map verdict to appropriate exit code.

    Args:
        verdict: The evaluation verdict

    Returns:
        Exit code (0=QUALIFIED, 2=DISQUALIFIED, 3=UNKNOWN)
    """
    if verdict == Verdict.QUALIFIED:
        return 0
    elif verdict == Verdict.DISQUALIFIED:
        return 2
    elif verdict == Verdict.UNKNOWN:
        return 3
    return 1  # Should never reach here


def main() -> NoReturn:
    """
    Main entry point for the CLI.

    Exit codes:
        0: QUALIFIED
        1: Unexpected error
        2: DISQUALIFIED
        3: UNKNOWN
    """
    parser = argparse.ArgumentParser(
        description="Evaluate warehouse facility eligibility for Empty Tote Return task",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s examples/facility_eligible.json
  %(prog)s examples/facility_ineligible.json --json
  %(prog)s my_facility.json

Exit codes:
  0 - QUALIFIED: Facility meets all requirements
  2 - DISQUALIFIED: Facility violates one or more rules
  3 - UNKNOWN: Required information missing or invalid
  1 - Unexpected error occurred
        """
    )

    parser.add_argument(
        "facility_file",
        type=str,
        help="Path to facility snapshot JSON file"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format instead of human-readable format"
    )

    args = parser.parse_args()

    try:
        # Validate file exists
        facility_path = Path(args.facility_file)
        if not facility_path.exists():
            print(f"Error: File not found: {args.facility_file}", file=sys.stderr)
            sys.exit(1)

        # Evaluate facility
        result = ConstraintEvaluator.evaluate_from_file(str(facility_path))

        # Output report
        if args.json:
            print_json_report(result)
        else:
            print_human_readable_report(result)

        # Exit with appropriate code
        sys.exit(get_exit_code(result.verdict))

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
