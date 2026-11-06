"""
Check the six numerical story signatures for ordinary cases 0 through 45.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    check_scenario:
        Checks the selected scenario using already validated tables. Measures degree,
        category and shelter proportions, priorities, window overlap, symbol diversity,
        closure reachability or expiry/repetition as appropriate.
"""

from collections import Counter
from validator.reference import make_adjacency, hop_distances


def check_scenario(case, data, network, log, alarm_density, rule):
    """Check the signature after all contributing tables have passed validation."""
    tier = case["tier"]
    crates, locations, roads = data["crates"], data["locations"], data["roads"]
    windows = data["windows"]
    priorities = [alarm["priority"] for alarm in data["incidents"]]
    location_count = len(locations)
    adjacency, hops = network["adjacency"], network["hops"]
    waves, closed = network["waves"], network["closed"]
    targets = [case["target_0"], case["target_1"], case["target_2"]]
    scenario = case["scenario"]
    degree = 2 * len(roads) / location_count
    if scenario == 1:
        rule(
            2.2 <= degree <= 3.2
            and sum(row["penalty"] >= 2 for row in locations) / location_count >= 0.4
            and len(waves) >= 3
            and sum(row["cat"] in (0, 1) for row in crates) / len(crates) >= 0.55,
            "V7",
            "Delta Flood signature failed.",
        )
    elif scenario == 2:
        rule(
            2.0 <= degree <= 2.6
            and sum(row["cat"] in (2, 3) for row in crates) / len(crates) >= 0.45
            and sum(priorities) / len(priorities) >= 6.0,
            "V7",
            "Mountain Earthquake signature failed.",
        )
    elif scenario == 3:
        overlaps = 0
        for index, first_window in enumerate(windows):
            for second_window in windows[index + 1 :]:
                if (
                    first_window["start"] < second_window["finish"]
                    and second_window["start"] < first_window["finish"]
                ):
                    overlaps += 1
        rule(
            sum(row["type"] == "S" for row in locations) / location_count >= 0.25
            and len(waves) >= 3
            and 2 * overlaps / len(windows) >= 2
            and len(set(log)) >= 30,
            "V7",
            "Coastal Cyclone signature failed.",
        )
    elif scenario == 4:
        rule(
            degree >= 3.5
            and sum(row["cat"] == 4 for row in crates) / len(crates) >= 0.1
            and (tier not in ("M", "L") or alarm_density >= 1.5),
            "V7",
            "Urban Flash Flood signature failed.",
        )
    elif scenario == 5:
        after_closures = hop_distances(make_adjacency(locations, roads, closed))
        rule(
            degree <= 2.4
            and max(len(neighbors) for neighbors in adjacency) <= 4
            and max(hops) >= location_count // 4
            and len(waves) >= 3
            and any(after_closures[target] == -1 for target in targets),
            "V7",
            "Landslide Corridor signature failed.",
        )
    elif scenario == 6:
        rule(
            sum(row["cat"] in (1, 2) for row in crates) / len(crates) >= 0.55
            and sum(row["expiry"] <= 300 for row in crates) / len(crates) >= 0.5
            and max(Counter(log).values()) / len(log) >= 0.25,
            "V7",
            "Outbreak Camp signature failed.",
        )
