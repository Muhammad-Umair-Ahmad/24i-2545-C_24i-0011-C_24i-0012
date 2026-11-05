"""
Write generated tables to the requested Excel file.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    write_workbook:
        Saves the workbook safely. Creates sheets in schema order, writes headings and
        typed cells, saves beside the destination to a temporary file, replaces the
        destination after success, and removes the temporary file.
"""

from pathlib import Path
from tempfile import NamedTemporaryFile

from generator.schema import SCHEMA


def write_workbook(tables, output):
    """Write plain typed cells and replace the destination only after saving."""
    # Keep the Excel dependency at the file boundary; generation itself is pure Python.
    from openpyxl import Workbook
    from openpyxl.cell import WriteOnlyCell

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook(write_only=True)
    for sheet_name, headings in SCHEMA.items():
        sheet = workbook.create_sheet(title=sheet_name)
        sheet.freeze_panes = "B2"
        sheet.append(headings)
        for row in tables[sheet_name]:
            cells = []
            for value in row:
                cell = WriteOnlyCell(sheet, value=value)
                # Numeric-looking radio text must remain text in Excel.
                if isinstance(value, str):
                    cell.data_type = "s"
                cells.append(cell)
            sheet.append(cells)

    # A failed save must not destroy a previously valid dataset.
    with NamedTemporaryFile(
        suffix=".xlsx", dir=output.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        workbook.save(temporary_path)
        temporary_path.replace(output)
    finally:
        temporary_path.unlink(missing_ok=True)
