"""
Read Excel data and validate file structure and cell types before domain rules run.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    load_workbook_rows:
        Provides the safe reader entry point. Checks for merged cells, reads tables, and
        converts damaged archive, XML or workbook-format errors into V1 failures.

    check_no_merged_cells:
        Rejects merged cells. Opens worksheet XML inside the XLSX archive and searches
        for merge-cell elements because streaming Excel reading does not expose them.

    read_workbook_rows:
        Reads all required sheets. Opens the workbook in streaming mode, checks exact
        sheet names and order, reads each table, and always closes the file.

    read_sheet_rows:
        Reads one table into named dictionaries. Checks headers, complete rows, cell
        types and sorting, then pairs each heading with its value.

    check_cell_type:
        Checks the representation of a cell. Requires nonempty ASCII text in text
        columns and exact integers in numeric columns, rejecting formulas, Boolean
        values and inappropriate types.
"""

from zipfile import ZipFile, BadZipFile
from xml.etree import ElementTree

from generator.schema import SCHEMA
from validator.rules import require, TEXT_COLUMNS, ValidationError


def load_workbook_rows(path):
    """Return named records, or report a damaged Excel archive as a V1 error."""
    from openpyxl.utils.exceptions import InvalidFileException

    try:
        check_no_merged_cells(path)
        return read_workbook_rows(path)
    except (BadZipFile, ElementTree.ParseError, InvalidFileException) as error:
        raise ValidationError(f"V1: Cannot read workbook: {error}") from error


def check_no_merged_cells(path):
    """Inspect XML because openpyxl's streaming reader hides merged ranges."""
    with ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.startswith("xl/worksheets/") or not name.endswith(".xml"):
                continue
            root = ElementTree.fromstring(archive.read(name))
            for element in root.iter():
                require(
                    not element.tag.endswith("}mergeCell"),
                    "V1",
                    f"{name}: merged cells are forbidden.",
                )


def read_workbook_rows(path):
    """Open once, check the sheet contract, read each table, and always close."""
    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=True, data_only=False)
    try:
        require(
            workbook.sheetnames == list(SCHEMA),
            "V1",
            "Exactly the 20 required sheets, in order, are required.",
        )
        tables = {}
        for sheet_name, headings in SCHEMA.items():
            tables[sheet_name] = read_sheet_rows(workbook[sheet_name], headings)
        return tables
    finally:
        workbook.close()


def read_sheet_rows(sheet, headings):
    """Check headings, complete rows, typed cells and the required sort order."""
    rows = sheet.iter_rows()
    header = next(rows, ())
    require(
        [cell.value for cell in header] == headings,
        "V1",
        f"{sheet.title}: wrong column headings.",
    )
    records = []
    previous_key = None
    for row_number, cells in enumerate(rows, start=2):
        context = f"{sheet.title} row {row_number}"
        values = [cell.value for cell in cells]
        require(
            len(values) == len(headings) and all(value is not None for value in values),
            "V2",
            f"{context}: blank cell or wrong row width.",
        )
        for heading, cell in zip(headings, cells):
            check_cell_type(cell, heading, context)
        key = (values[0], values[1])
        require(
            previous_key is None or previous_key <= key,
            "V3",
            f"{sheet.title}: rows are not sorted.",
        )
        previous_key = key
        # Domain checks use names such as crate['weight'], not Excel column offsets.
        records.append(dict(zip(headings, values)))
    return records


def check_cell_type(cell, heading, context):
    """Reject formulas, floating-point numbers, blank text and non-ASCII text."""
    if heading in TEXT_COLUMNS:
        valid_text = (
            isinstance(cell.value, str)
            and cell.value.isascii()
            and cell.value != ""
            and cell.data_type in ("s", "inlineStr")
        )
        require(valid_text, "V2", f"{context}: {heading} must be plain ASCII text.")
    else:
        # bool is a subclass of int; exact type checking rejects Boolean cells too.
        require(
            type(cell.value) is int, "V2", f"{context}: {heading} must be an integer."
        )
