"""
Generate rescue windows and the required alarm stream.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    make_windows:
        Creates rescue intervals. Starts with three windows that guarantee two touching
        pairs, then generates legal random intervals or an overlapping cyclone cluster.

    make_incidents:
        Creates ordered alarm arrivals. Distributes alarms across ticks at about 1.6
        alarms per tick, guarantees priority variety, and favors urgent priorities for
        earthquake cases.
"""

import math
from generator.randomness import size_for


def make_windows(random_generator, tier, scenario):
    # Preserve the deterministic window-generation contract.
    count = size_for(random_generator, tier, (8, 12), (50, 100), (1_000, 1_300))
    # The first three windows guarantee two touching pairs.
    windows = [
        [1, 0, 10, random_generator.randint(1, 100)],
        [2, 10, 20, random_generator.randint(1, 100)],
        [3, 20, 30, random_generator.randint(1, 100)],
    ]
    for window_id in range(4, count + 1):
        if scenario == 3:
            start = random_generator.randint(100, 120)
            finish = random_generator.randint(300, 500)
        else:
            start = random_generator.randint(0, 1435)
            duration = random_generator.randint(5, min(480, 1440 - start))
            finish = start + duration
        windows.append([window_id, start, finish, random_generator.randint(1, 100)])
    return windows


def make_incidents(random_generator, case_identifier, tier, scenario):
    """Release roughly 1.6 alarms per tick, retaining priority variety."""
    data = {}
    alarm_count = size_for(random_generator, tier, (10, 40), (200, 1000), (2000, 5000))
    # Select a final tick giving 1.5 to 1.8 alarms per tick.
    tick_count = math.ceil(alarm_count / 1.6)
    data["incidents"] = []
    required_priorities = [1, 6, 7, 8, 9, 10]
    for alarm_index in range(alarm_count):
        tick = alarm_index * tick_count // alarm_count
        if alarm_index < len(required_priorities):
            priority = required_priorities[alarm_index]
        elif scenario == 2:
            priority = random_generator.randint(7, 10)
        else:
            priority = random_generator.randint(1, 10)
        data["incidents"].append([case_identifier, alarm_index + 1, tick, priority])

    return data["incidents"]
