"""
Run workbook generation from the terminal.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    main:
        Reads the seed and output filename. Calls the in-memory dataset builder, passes
        its tables to the Excel writer, and prints a short completion message.
"""

import argparse
import sys
from pathlib import Path

# Keep the submission directory free of generated Python cache folders.
sys.dont_write_bytecode = True

# Allow direct execution from the project root.
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator.builder import generate_dataset
from generator.workbook import write_workbook


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--output", type=Path, default=Path("cases.xlsx"))
    arguments = parser.parse_args()
    tables = generate_dataset(arguments.seed)
    write_workbook(tables, arguments.output)
    print(f"Created {arguments.output}: 50 cases, 20 sheets.")


if __name__ == "__main__":
    main()
