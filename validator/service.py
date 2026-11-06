"""
Coordinate workbook-level validation without handling terminal arguments or writing files.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    group_records_by_case:
        Organizes named records under their case IDs. Verifies exactly 50 identities and
        one seed, creates each case table group, and rejects references to unknown
        cases.

    check_case_identity:
        Verifies ID, tier and scenario independently. Recomputes the expected values
        from the group seed and case number and compares them with the saved fields.

    validate:
        Checks the entire saved workbook. Reads records, groups cases, verifies each
        identity and case, accumulates variety evidence, and returns report lines or
        raises the first validation failure.
"""

from generator.schema import SCHEMA
from validator.rules import require
from validator.workbook import load_workbook_rows
from validator.checks import check_case
from validator.variety import VarietyChecks


def group_records_by_case(tables):
    """Check the case set, then attach each sheet row to its owning case."""
    cases = tables["cases"]
    require(len(cases) == 50, "V1", "Need exactly 50 cases.")
    numbers = sorted(case["case_no"] for case in cases)
    require(numbers == list(range(50)), "V1", "Case numbers must be exactly 0..49.")
    identifiers = {case["case_id"] for case in cases}
    seeds = {case["group_seed"] for case in cases}
    require(
        len(identifiers) == 50 and len(seeds) == 1,
        "V1",
        "Need distinct case IDs and one group seed.",
    )
    grouped = {}
    for identifier in identifiers:
        grouped[identifier] = {name: [] for name in SCHEMA}
    for sheet_name, records in tables.items():
        for row in records:
            identifier = row["case_id"]
            require(
                identifier in identifiers,
                "V3",
                f"{sheet_name}: unknown case reference.",
            )
            grouped[identifier][sheet_name].append(row)
    return grouped


def check_case_identity(case):
    """Recompute tier, scenario and ID independently of generator helpers."""
    number = case["case_no"]
    if number < 20:
        expected_tier = "S"
    elif number < 40:
        expected_tier = "M"
    elif number < 46:
        expected_tier = "L"
    else:
        expected_tier = "X"
    expected_identifier = f'{case["group_seed"]}-{number:02d}'
    require(
        case["case_id"] == expected_identifier
        and case["tier"] == expected_tier
        and case["scenario"] == number % 6 + 1,
        "V1",
        f"Case {number}: wrong identity, tier, or scenario.",
    )


def validate(path):
    """Return report lines, or raise ValidationError at the first broken rule."""
    tables = load_workbook_rows(path)
    by_case = group_records_by_case(tables)
    variety = VarietyChecks()
    details = []
    for case in tables["cases"]:
        check_case_identity(case)
        data = by_case[case["case_id"]]
        cargo_greedy_failure, fewest_roads_failure, safety_density = check_case(
            case, data
        )
        variety.record(
            case, data, cargo_greedy_failure, fewest_roads_failure, safety_density
        )
        message = f'PASS {case["case_id"]}: V1-V7'
        if case["case_no"] >= 46:
            message += "; V8 trap checked"
        details.append(message)
    details.append(variety.finish())
    return details
