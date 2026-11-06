"""
Define the workbook contract: the 20 sheet names, column order and case identity helpers.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    tier_for:
        Chooses the size tier for a case. Rejects numbers outside 0 to 49 and applies
        the fixed S, M, L and X case-number boundaries.

    scenario_for:
        Chooses one of the six scenarios. Takes the case number remainder after division
        by six and adds one.

    case_id:
        Formats the workbook case identifier. Joins the seed, a hyphen and a case number
        padded to at least two digits, such as 11-03.
"""

# Each list contains the column headings, from left to right.
SCHEMA = {
    "cases": [
        "case_id",
        "group_seed",
        "case_no",
        "tier",
        "scenario",
        "capacity",
        "target_0",
        "target_1",
        "target_2",
        "edit_bound",
        "tour_length",
        "sensor_nodes",
        "sensor_k",
        "safety_vars",
        "rations_target",
    ],
    "crates": ["case_id", "crate_id", "cat", "weight", "value", "expiry", "serial"],
    "locations": ["case_id", "loc_id", "type", "penalty"],
    "roads": ["case_id", "road_no", "u", "v", "minutes", "cable"],
    "waves": ["case_id", "wave_no", "road_no"],
    "radio_log": ["case_id", "part", "text"],
    "radio_patterns": ["case_id", "pattern_no", "pattern", "count"],
    "radio_reports": ["case_id", "report_a", "report_b"],
    "windows": ["case_id", "window_id", "start", "finish", "value"],
    "incidents": ["case_id", "alarm_id", "tick", "priority"],
    "sites": ["case_id", "site_no", "x", "y"],
    "tour": ["case_id", "step", "site_no"],
    "pipeline_dims": ["case_id", "idx", "dim"],
    "drum_prices": ["case_id", "length", "price"],
    "sensor_edges": ["case_id", "u", "v"],
    "sensor_cover": ["case_id", "node"],
    "safety_rules": ["case_id", "rule_no", "lit_1", "lit_2", "lit_3"],
    "safety_planted": ["case_id", "switch", "value"],
    "rations": ["case_id", "item", "value", "planted"],
    "claims": [
        "case_id",
        "cargo_opt",
        "window_count_opt",
        "window_value_opt",
        "drum_opt",
        "tour_opt",
        "cover_min",
    ],
}


def tier_for(case_number):
    """Choose a size group (0 to 49)."""
    if case_number < 0 or case_number > 49:
        raise ValueError("case number must be in 0..49")
    if case_number < 20:
        return "S"
    if case_number < 40:
        return "M"
    if case_number < 46:
        return "L"
    return "X"


def scenario_for(case_number):
    """Repeat scenarios 1, 2, 3, 4, 5, 6 across the cases."""
    # The remainder is 0 to 5. Adding one gives us 1 to 6.
    return case_number % 6 + 1


def case_id(seed, case_number):
    """For example, seed 11 and case 3 become the text 11-03."""
    return f"{seed}-{case_number:02d}"
