"""
Run Iteration 1 validation and its required submission evidence from the terminal.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    main:
        Reads input, report and broken-copy options. Rejects an input/report path
        collision, runs validation and optional rejection tests, catches failures,
        writes the requested report, prints the final result and returns an exit status.
"""

import argparse
import sys
from pathlib import Path
from zipfile import BadZipFile
from xml.etree import ElementTree

# Keep the submission directory free of generated Python cache folders.
sys.dont_write_bytecode = True

# Allow direct execution from the project root.
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validator.rules import ValidationError
from validator.service import validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("cases.xlsx"))
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("validation_report.txt"),
        help="Iteration 1 validation report destination",
    )
    parser.add_argument(
        "--test-bad-data",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate and check the required broken copies (enabled by default)",
    )
    arguments = parser.parse_args()
    if (
        arguments.report is not None
        and arguments.input.resolve() == arguments.report.resolve()
    ):
        parser.error(
            "--report must differ from --input; the workbook must not be overwritten"
        )
    lines = [f"Workbook: {arguments.input}", "Checks: V1-V8 from Project Phase 1."]
    try:
        lines.extend(validate(arguments.input))
        if arguments.test_bad_data:
            from validator.test_rejections import run_rejection_tests

            lines.extend(
                run_rejection_tests(arguments.input, validate, ValidationError)
            )
        lines.append("PASS: all 50 saved cases satisfy all implemented V1-V8 checks.")
        status = 0
    except (
        ValidationError,
        BadZipFile,
        ElementTree.ParseError,
        AssertionError,
        OSError,
        ValueError,
        KeyError,
        IndexError,
        TypeError,
    ) as error:
        lines.append(f"FAIL: {error}")
        status = 1
    if arguments.report is not None:
        try:
            arguments.report.parent.mkdir(parents=True, exist_ok=True)
            arguments.report.write_text("\n".join(lines) + "\n")
        except OSError as error:
            print(f"Cannot save validation report: {error}", file=sys.stderr)
            return 1
    print(lines[-1])
    return status


if __name__ == "__main__":
    sys.exit(main())
