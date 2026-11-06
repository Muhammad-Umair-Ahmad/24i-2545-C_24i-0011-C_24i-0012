"""
Build and reject the two-times-five damaged workbook copies required by Iteration 1.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    write_broken_copy:
        Changes one cell while preserving the rest of a workbook. Copies the XLSX ZIP
        entries and edits the specified cell in one worksheet XML file.

    run_rejection_tests:
        Demonstrates rejection of ten damaged copies. Locates records for cases 00 and
        01, breaks weight, road reference, closure uniqueness, pattern count and tour
        length separately, and checks the expected failure group.
"""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree

SPREADSHEET_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def write_broken_copy(source, destination, sheet_number, address, value):
    target_name = f"xl/worksheets/sheet{sheet_number}.xml"
    with ZipFile(source) as original, ZipFile(destination, "w", ZIP_DEFLATED) as broken:
        for member in original.infolist():
            content = original.read(member.filename)
            if member.filename == target_name:
                root = ElementTree.fromstring(content)
                changed = False
                for cell in root.iter(f"{{{SPREADSHEET_NAMESPACE}}}c"):
                    if cell.attrib.get("r") == address:
                        cell.clear()
                        cell.set("r", address)
                        if isinstance(value, str):
                            cell.set("t", "inlineStr")
                            inline = ElementTree.SubElement(
                                cell, f"{{{SPREADSHEET_NAMESPACE}}}is"
                            )
                            text = ElementTree.SubElement(
                                inline, f"{{{SPREADSHEET_NAMESPACE}}}t"
                            )
                            text.text = value
                        else:
                            cell.set("t", "n")
                            number = ElementTree.SubElement(
                                cell, f"{{{SPREADSHEET_NAMESPACE}}}v"
                            )
                            number.text = str(value)
                        changed = True
                        break
                if not changed:
                    raise ValueError(f"Cannot find {target_name}!{address}")
                content = ElementTree.tostring(root)
            broken.writestr(member, content)


def run_rejection_tests(source, validate_function, error_class):
    """Save ten required broken copies and collect their observed rejections."""
    from openpyxl import load_workbook

    workbook = load_workbook(source, read_only=True)
    cases = list(workbook["cases"].values)[1:3]
    first_rows = {}
    for sheet_name in ("crates", "waves", "radio_patterns"):
        first_rows[sheet_name] = {}
        for row_number, row in enumerate(workbook[sheet_name].values, start=1):
            if row[0] not in first_rows[sheet_name]:
                first_rows[sheet_name][row[0]] = (row_number, row)
    workbook.close()
    lines = ["Required broken-copy checks:"]
    for case_row in cases:
        identifier, seed, case_number = case_row[:3]
        folder = Path(__file__).resolve().parent / "tests" / f"case_{case_number:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        crate_row, crate = first_rows["crates"][identifier]
        wave_row, wave = first_rows["waves"][identifier]
        pattern_row, pattern = first_rows["radio_patterns"][identifier]
        tests = [
            ("invalid_weight", 2, f"D{crate_row}", 0, "V2"),
            ("unknown_road", 5, f"C{wave_row}", 999999, "V3"),
            ("duplicate_closure", 5, f"C{wave_row + 1}", wave[2], "V4"),
            ("wrong_pattern_count", 7, f"D{pattern_row}", pattern[3] + 1, "V5"),
            ("wrong_tour_length", 1, f"K{case_number + 2}", case_row[10] + 1, "V6"),
        ]
        for name, sheet_number, address, value, expected_group in tests:
            destination = folder / f"{name}.xlsx"
            write_broken_copy(source, destination, sheet_number, address, value)
            try:
                validate_function(destination)
            except error_class as error:
                if not str(error).startswith(expected_group + ":"):
                    raise AssertionError(
                        f"{identifier}/{name}: wrong rejection: {error}"
                    ) from error
                lines.append(f"REJECTED case_{case_number:02d}/{name}.xlsx: {error}")
            else:
                raise AssertionError(f"{identifier}/{name}: broken copy was accepted.")
    lines.append("PASS: two cases, five broken copies each; all ten rejected.")
    return lines
