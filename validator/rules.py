"""
Store independent requirement limits and helpers that raise understandable validation failures.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    ValidationError:
        Represents a failed workbook requirement. Inherits ValueError and carries the
        requirement group and explanatory message.

    require:
        Enforces one condition. Raises ValidationError with its V1-V8 group when the
        condition is false.

    consecutive:
        Checks an identifier sequence. Extracts the named field and compares it with the
        exact consecutive range starting at the required number.

    check_size:
        Checks one item count against its tier range. Selects S/M/L limits, applies
        explicit trap-size overrides, and rejects an out-of-range count.

    case_rule:
        Creates a case-specific rule checker. Returns a nested function that adds the
        case ID before forwarding a condition to require.

    case_rule.rule:
        Reports a condition for its owning case. Prefixes the message with the captured
        case identifier and delegates failure handling to require.
"""

ALPHABET = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
PATTERN_LENGTHS = (2, 4, 8, 12, 20, 40)
# X inherits L, except for the four explicitly overridden trap sizes.
SIZE_RANGES = {
    "crates": ((8, 20), (40, 200), (500, 1500)),
    "locations": ((6, 12), (30, 150), (500, 2000)),
    "radio_log": ((200, 500), (2000, 10000), (20000, 100000)),
    "radio_reports": ((10, 30), (30, 150), (200, 1000)),
    "windows": ((8, 20), (50, 300), (1000, 3000)),
    "incidents": ((10, 40), (200, 1000), (2000, 5000)),
    "sites": ((5, 9), (10, 16), (200, 500)),
    "pipeline_dims": ((4, 8), (15, 60), (100, 300)),
    "drum_prices": ((5, 14), (40, 200), (500, 2000)),
    "sensor_nodes": ((6, 14), (20, 40), (100, 400)),
    "safety_vars": ((6, 15), (20, 50), (20, 50)),
    "rations": ((8, 20), (24, 40), (50, 100)),
}
TEXT_COLUMNS = {"case_id", "tier", "type", "text", "pattern", "report_a", "report_b"}


class ValidationError(ValueError):
    """A workbook rule failed; the message starts with its V1-V8 group."""


def require(condition, group, message):
    if not condition:
        raise ValidationError(f"{group}: {message}")


def consecutive(rows, field, start, context):
    actual = []
    for row in rows:
        actual.append(row[field])
    expected = list(range(start, start + len(rows)))
    require(
        actual == expected,
        "V3",
        f"{context}: {field} must be consecutive from {start}.",
    )


def check_size(name, size, tier, case_number):
    tier_index = 0 if tier == "S" else 1 if tier == "M" else 2
    minimum, maximum = SIZE_RANGES[name][tier_index]
    if name == "crates" and case_number == 46:
        minimum, maximum = 1500, 3000
    elif name == "crates" and case_number == 47:
        minimum, maximum = 12, 60
    elif name == "locations" and case_number == 48:
        minimum, maximum = 1500, 3000
    elif name == "radio_log" and case_number == 49:
        minimum, maximum = 50000, 100000
    require(
        minimum <= size <= maximum,
        "V2",
        f"Case {case_number}: {name} size {size} outside {minimum}..{maximum}.",
    )


def case_rule(case_identifier):
    """Attach the case ID to every failure raised by its domain checks."""

    def rule(condition, group, message):
        require(condition, group, f"{case_identifier}: {message}")

    return rule
