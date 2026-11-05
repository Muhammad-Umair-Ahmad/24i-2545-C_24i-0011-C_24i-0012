"""
Generate radio logs, overlapping phrase counts and related reports.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    overlapping_count:
        Counts every occurrence of a phrase. Uses string find repeatedly and advances
        only one position after a match so overlaps are included.

    random_text:
        Creates a string of a requested length. Repeatedly chooses a character from the
        supplied alphabet and joins the characters.

    make_radio:
        Creates the joined log, six patterns and two reports. Applies scenario symbol
        rules and the near-miss trap, then makes three report replacements to establish
        an edit upper bound.

    make_radio_rows:
        Converts radio content into workbook tables. Splits the log into parts of at
        most 10000 characters, counts the six patterns, and stores the paired reports.
"""

import math
from generator.randomness import size_for

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
PATTERN_LENGTHS = (2, 4, 8, 12, 20, 40)


def overlapping_count(text, pattern):
    """Move forward by one after a match so overlapping matches count too."""
    count = 0
    position = text.find(pattern)
    while position != -1:
        count += 1
        position = text.find(pattern, position + 1)
    return count


def random_text(random_generator, alphabet, length):
    characters = []
    for position in range(length):
        characters.append(random_generator.choice(alphabet))
    return "".join(characters)


def make_radio(random_generator, tier, scenario, case_number):
    length = size_for(
        random_generator, tier, (200, 500), (2000, 10000), (20000, 100000)
    )
    # Exclude Z from ordinary logs so a pattern containing Z is certainly absent.
    log_alphabet = ALPHABET.replace("Z", "")
    log = random_text(random_generator, log_alphabet, length)
    if case_number <= 45 and scenario == 3:
        log = log_alphabet + log[len(log_alphabet) :]
    if case_number <= 45 and scenario == 6:
        repeated_length = math.ceil(length * 0.30)
        log = "A" * repeated_length + log[repeated_length:]

    patterns = [log[:2], log[3:7], log[8:16], log[20:32], log[40:60], "Z" * 40]
    if case_number == 49:
        log = "A" * random_generator.randint(50000, 100000)
        patterns = ["AA", "AAAA"]
        for pattern_length in PATTERN_LENGTHS[2:]:
            patterns.append("A" * (pattern_length - 1) + "B")

    reports_length = size_for(random_generator, tier, (10, 30), (30, 150), (200, 1000))
    report_a = random_text(random_generator, ALPHABET, reports_length)
    report_b_characters = list(report_a)
    # Three replacements give a proven edit-distance upper bound of three.
    changed_positions = random_generator.sample(range(reports_length), 3)
    for position in changed_positions:
        old_symbol = report_b_characters[position]
        alternatives = ALPHABET.replace(old_symbol, "")
        report_b_characters[position] = random_generator.choice(alternatives)
    report_b = "".join(report_b_characters)
    return log, patterns, report_a, report_b, 3


def make_radio_rows(random_generator, case_identifier, tier, scenario, case_number):
    """Split logs into Excel-safe text parts and store the six phrase counts."""
    data = {}
    log, patterns, report_a, report_b, edit_bound = make_radio(
        random_generator, tier, scenario, case_number
    )
    data["radio_log"] = []
    for offset in range(0, len(log), 10000):
        part = offset // 10000 + 1
        data["radio_log"].append([case_identifier, part, log[offset : offset + 10000]])
    data["radio_patterns"] = []
    for pattern_number, pattern in enumerate(patterns):
        data["radio_patterns"].append(
            [case_identifier, pattern_number, pattern, overlapping_count(log, pattern)]
        )
    data["radio_reports"] = [[case_identifier, report_a, report_b]]
    return data, edit_bound
