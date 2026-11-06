"""
Validate one case, with functions grouped by data module and coordinated by check_case.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    check_sizes_and_identifiers:
        Checks table sizes and required ID sequences. Applies independent tier limits,
        then compares identifiers with consecutive integer ranges before later checks
        follow references.

    check_inventory:
        Checks crate fields, serial uniqueness and capacity. Walks crate rows, adds
        weights and verifies that capacity lies between 10 and 70 percent of total
        weight.

    check_network:
        Checks locations, targets, roads and closures. Validates references and costs,
        builds adjacency lists, checks reachability from HQ, and verifies disjoint
        closure-wave sizes; returns checked graph facts.

    check_radio:
        Checks logs, patterns and reports. Joins ordered parts, validates the alphabet
        and lengths, independently recounts overlapping matches, and computes true edit
        distance to verify the supplied bound.

    check_windows:
        Checks rescue intervals and values. Validates times and duration limits, then
        counts finish/start coincidences to confirm at least two touching pairs.

    check_incidents:
        Checks alarm arrival order and urgency. Verifies tick and priority fields,
        calculates alarms per tick from the actual final tick, and checks required
        priority variety.

    check_tour:
        Checks coordinates and the planted tour. Verifies unique sites and a permutation
        starting at zero, recomputes closed Manhattan length, and compares L/X tours
        with the nearest-neighbor baseline.

    check_pipeline:
        Checks matrix dimensions and drum prices. Applies integer ranges and ensures
        that prices are not all proportional to piece length.

    check_sensors:
        Checks the planted sensor cover. Verifies node ranges, cover size, unique edges
        and that every edge touches a selected cover node.

    check_safety:
        Checks switch assignments and safety rules. Validates rule density and distinct
        switch references, then evaluates each clause under the planted assignment.

    check_rations:
        Checks ration values and planted flags. Recomputes the selected sum and compares
        it with the positive target.

    check_claims:
        Verifies small-case optima independently. Recomputes all six answers and detects
        whether ratio-based cargo loading and fewest-road routing lose on the case;
        rejects claims on non-S tiers.

    check_case:
        Runs the per-case checklist in dependency order. Checks sizes and references
        first, then each data module, claims, and either ordinary scenario rules or trap
        rules; returns facts needed for dataset-wide variety.
"""

from collections import Counter, defaultdict
from generator.schema import SCHEMA
from validator.rules import (
    check_size,
    consecutive,
    case_rule,
    ALPHABET,
    PATTERN_LENGTHS,
)
from validator.reference import (
    make_adjacency,
    hop_distances,
    count_matches,
    edit_distance,
    closed_tour_length,
    nearest_tour_length,
    cargo_value,
    greedy_cargo_value,
    window_values,
    drum_value,
    shortest_tour,
    smallest_cover,
    route_costs,
)
from validator.scenarios import check_scenario
from validator.traps import check_trap


def check_sizes_and_identifiers(case, data):
    """Check sizes first so later functions can safely access required rows."""
    number, tier = case["case_no"], case["tier"]
    label = case["case_id"]
    for name in (
        "crates",
        "locations",
        "windows",
        "incidents",
        "sites",
        "drum_prices",
        "rations",
    ):
        check_size(name, len(data[name]), tier, number)
    check_size("pipeline_dims", len(data["pipeline_dims"]) - 1, tier, number)
    check_size("sensor_nodes", case["sensor_nodes"], tier, number)
    check_size("safety_vars", case["safety_vars"], tier, number)
    for name, field, start in (
        ("crates", "crate_id", 1),
        ("locations", "loc_id", 0),
        ("roads", "road_no", 0),
        ("radio_log", "part", 1),
        ("radio_patterns", "pattern_no", 0),
        ("windows", "window_id", 1),
        ("incidents", "alarm_id", 1),
        ("sites", "site_no", 0),
        ("tour", "step", 0),
        ("pipeline_dims", "idx", 0),
        ("drum_prices", "length", 1),
        ("safety_rules", "rule_no", 1),
        ("safety_planted", "switch", 1),
        ("rations", "item", 0),
    ):
        consecutive(data[name], field, start, f"{label}/{name}")


def check_inventory(case, data, rule):
    """Verify every crate and the capacity as a fraction of total weight."""
    crates = data["crates"]
    serials = set()
    total_weight = 0
    for crate in crates:
        rule(
            0 <= crate["cat"] <= 4
            and 1 <= crate["weight"] <= 20
            and 10 <= crate["value"] <= 100
            and 0 <= crate["expiry"] <= 999
            and 10000000 <= crate["serial"] <= 99999999,
            "V2",
            "Invalid crate field.",
        )
        serials.add(crate["serial"])
        total_weight += crate["weight"]
    rule(len(serials) == len(crates), "V3", "Crate serials must be distinct.")
    rule(
        case["capacity"] >= 1
        and total_weight <= 10 * case["capacity"] <= 7 * total_weight,
        "V2",
        "Capacity must be 10% to 70% of total weight.",
    )


def check_network(case, data, rule):
    """Return the checked graph facts needed by scenarios, claims and traps."""
    locations, roads = data["locations"], data["roads"]
    location_count = len(locations)
    for location in locations:
        rule(
            location["type"] in ("D", "S", "H", "J")
            and location["penalty"] in (0, 1, 2, 4, 6),
            "V2",
            "Invalid location.",
        )
    rule(
        locations[0]["type"] == "D" and locations[0]["penalty"] == 0,
        "V3",
        "Location 0 must be HQ with no penalty.",
    )
    rule(
        any(row["type"] == "S" for row in locations)
        and any(row["type"] == "H" for row in locations),
        "V3",
        "Need a shelter and a hospital.",
    )
    targets = [case["target_0"], case["target_1"], case["target_2"]]
    rule(len(set(targets)) == 3, "V3", "Targets must be distinct.")
    for target in targets:
        rule(
            0 < target < location_count and locations[target]["type"] in ("S", "H"),
            "V3",
            "Invalid target.",
        )
    rule(
        location_count - 1 <= len(roads) <= 3 * location_count,
        "V2",
        "Road count outside allowed range.",
    )
    endpoints = set()
    for road in roads:
        rule(
            0 <= road["u"] < road["v"] < location_count
            and 1 <= road["minutes"] <= 60
            and 1 <= road["cable"] <= 100,
            "V2",
            "Invalid road.",
        )
        endpoints.add((road["u"], road["v"]))
    rule(len(endpoints) == len(roads), "V3", "Duplicate road endpoints.")
    adjacency = make_adjacency(locations, roads)
    hops = hop_distances(adjacency)
    rule(-1 not in hops, "V4", "Network is disconnected before closures.")
    waves = defaultdict(list)
    closed = set()
    for wave in data["waves"]:
        road_number = wave["road_no"]
        rule(0 <= road_number < len(roads), "V3", "Closure references an unknown road.")
        rule(road_number not in closed, "V4", "Closure waves must be disjoint.")
        closed.add(road_number)
        waves[wave["wave_no"]].append(road_number)
    rule(
        2 <= len(waves) <= 5 and sorted(waves) == list(range(1, len(waves) + 1)),
        "V2",
        "Need 2 to 5 consecutive waves starting at 1.",
    )
    for wave_roads in waves.values():
        rule(
            1 <= len(wave_roads) <= max(1, len(roads) // 4),
            "V4",
            "Closure-wave size outside allowed range.",
        )

    return {"adjacency": adjacency, "hops": hops, "waves": waves, "closed": closed}


def check_radio(case, data, rule):
    """Return the joined log only after verifying every radio field."""
    tier, number = case["tier"], case["case_no"]
    log = "".join(row["text"] for row in data["radio_log"])
    check_size("radio_log", len(log), tier, number)
    for part in data["radio_log"]:
        rule(
            1 <= len(part["text"]) <= 10000 and set(part["text"]) <= ALPHABET,
            "V5",
            "Invalid radio-log part.",
        )
    patterns = data["radio_patterns"]
    rule(len(patterns) == 6, "V5", "Need exactly six patterns.")
    counts = []
    for pattern, expected_length in zip(patterns, PATTERN_LENGTHS):
        text = pattern["pattern"]
        rule(
            len(text) == expected_length and set(text) <= ALPHABET,
            "V5",
            "Invalid pattern length or alphabet.",
        )
        actual_count = count_matches(log, text)
        rule(
            actual_count == pattern["count"],
            "V5",
            f'Wrong count for pattern {pattern["pattern_no"]}.',
        )
        counts.append(actual_count)
    rule(
        sum(count > 0 for count in counts) >= 2 and 0 in counts,
        "V5",
        "Need two occurring patterns and one absent pattern.",
    )
    rule(len(data["radio_reports"]) == 1, "V3", "Need one pair of radio reports.")
    reports = data["radio_reports"][0]
    first, second = reports["report_a"], reports["report_b"]
    for report in (first, second):
        check_size("radio_reports", len(report), tier, number)
        rule(set(report) <= ALPHABET, "V2", "Invalid radio-report alphabet.")
    rule(
        edit_distance(first, second) <= case["edit_bound"] <= len(first) + len(second),
        "V5",
        "Invalid edit-distance bound.",
    )

    return log


def check_windows(case, data, rule):
    """Validate times, durations, values and at least two touching pairs."""
    windows = data["windows"]
    for window in windows:
        rule(
            0 <= window["start"] < window["finish"] <= 1440
            and 5 <= window["finish"] - window["start"] <= 480
            and 1 <= window["value"] <= 100,
            "V2",
            "Invalid rescue window.",
        )
    starts = Counter(window["start"] for window in windows)
    finishes = Counter(window["finish"] for window in windows)
    touching_pairs = sum(count * starts[finish] for finish, count in finishes.items())
    rule(touching_pairs >= 2, "V2", "Need at least two touching window pairs.")


def check_incidents(case, data, rule):
    """Validate arrival ordering, urgency variety and actual alarms per tick."""
    tier = case["tier"]
    incidents = data["incidents"]
    ticks = [alarm["tick"] for alarm in incidents]
    priorities = [alarm["priority"] for alarm in incidents]
    rule(
        ticks[0] == 0
        and ticks == sorted(ticks)
        and all(1 <= priority <= 10 for priority in priorities),
        "V2",
        "Invalid alarm ticks or priorities.",
    )
    alarm_density = len(incidents) / (ticks[-1] + 1)
    if tier in ("M", "L"):
        rule(
            1.2 <= alarm_density <= 1.8
            and len(set(priorities)) >= 6
            and 1 in priorities,
            "V2",
            "Invalid alarm density or priority variety.",
        )

    return alarm_density


def check_tour(case, data, rule):
    """Validate unique sites, a complete permutation and its closed length."""
    tier = case["tier"]
    sites = data["sites"]
    coordinates = set()
    for site in sites:
        rule(
            0 <= site["x"] <= 999 and 0 <= site["y"] <= 999,
            "V2",
            "Site coordinates outside range.",
        )
        coordinates.add((site["x"], site["y"]))
    rule(len(coordinates) == len(sites), "V3", "Duplicate sites.")
    tour = [step["site_no"] for step in data["tour"]]
    rule(
        len(tour) == len(sites)
        and sorted(tour) == list(range(len(sites)))
        and tour[0] == 0,
        "V6",
        "Tour must be a permutation starting at 0.",
    )
    rule(
        closed_tour_length(sites, tour) == case["tour_length"],
        "V6",
        "Wrong closed Manhattan tour length.",
    )
    if tier in ("L", "X"):
        rule(
            case["tour_length"] <= nearest_tour_length(sites),
            "V6",
            "Tour is longer than nearest-neighbor baseline (ties: lowest site ID).",
        )


def check_pipeline(case, data, rule):
    """Validate matrix dimensions and legal, non-proportional drum prices."""
    rule(
        all(2 <= row["dim"] <= 100 for row in data["pipeline_dims"]),
        "V2",
        "Invalid pipeline dimension.",
    )
    prices = data["drum_prices"]
    rule(all(1 <= row["price"] <= 500 for row in prices), "V2", "Invalid drum price.")
    rule(
        any(row["price"] != row["length"] * prices[0]["price"] for row in prices),
        "V2",
        "Drum prices must not all be proportional.",
    )


def check_sensors(case, data, rule):
    """Ensure the planted cover touches every legal sensor edge."""
    sensor_nodes = case["sensor_nodes"]
    cover = [row["node"] for row in data["sensor_cover"]]
    rule(
        len(cover) == len(set(cover)) == case["sensor_k"]
        and 2 <= case["sensor_k"] <= sensor_nodes // 2,
        "V6",
        "Invalid planted cover size.",
    )
    rule(all(0 <= node < sensor_nodes for node in cover), "V3", "Unknown cover node.")
    sensor_pairs = set()
    for edge in data["sensor_edges"]:
        rule(0 <= edge["u"] < edge["v"] < sensor_nodes, "V3", "Invalid sensor edge.")
        rule(
            edge["u"] in cover or edge["v"] in cover,
            "V6",
            "Planted cover misses an edge.",
        )
        sensor_pairs.add((edge["u"], edge["v"]))
    rule(
        len(sensor_pairs) == len(data["sensor_edges"])
        and len(sensor_pairs) >= sensor_nodes - 1,
        "V2",
        "Duplicate or too few sensor edges.",
    )


def check_safety(case, data, rule):
    """Check rule references and the planted Boolean assignment."""
    tier = case["tier"]
    switches = case["safety_vars"]
    assignment_rows = data["safety_planted"]
    rule(
        len(assignment_rows) == switches
        and all(row["value"] in (0, 1) for row in assignment_rows),
        "V6",
        "Invalid planted assignment.",
    )
    assignment = {row["switch"]: row["value"] for row in assignment_rows}
    density = len(data["safety_rules"]) / switches
    rule(2.0 <= density <= 6.0, "V2", "Safety rules/switch outside range.")
    if tier in ("M", "L"):
        rule(density >= 2.5, "V7", "M/L safety density must be at least 2.5.")
    for clause in data["safety_rules"]:
        literals = [clause["lit_1"], clause["lit_2"], clause["lit_3"]]
        rule(
            len({abs(literal) for literal in literals}) == 3
            and all(1 <= abs(literal) <= switches for literal in literals),
            "V3",
            "Safety literals must use three distinct existing switches.",
        )
        satisfied = False
        for literal in literals:
            if assignment[abs(literal)] == int(literal > 0):
                satisfied = True
        rule(satisfied, "V6", "Planted assignment violates a rule.")
    return density


def check_rations(case, data, rule):
    """Recompute the nonempty planted ration sum."""
    rations_sum = 0
    for ration in data["rations"]:
        rule(
            1 <= ration["value"] <= 1000 and ration["planted"] in (0, 1),
            "V2",
            "Invalid ration field.",
        )
        if ration["planted"] == 1:
            rations_sum += ration["value"]
    rule(
        rations_sum == case["rations_target"] and rations_sum > 0,
        "V6",
        "Wrong planted ration sum.",
    )


def check_claims(case, data, network, rule):
    """Return whether cargo greedy and fewest-road routing lose on this S case."""
    tier = case["tier"]
    crates, locations = data["crates"], data["locations"]
    windows, prices, sites = data["windows"], data["drum_prices"], data["sites"]
    sensor_nodes = case["sensor_nodes"]
    adjacency = network["adjacency"]
    targets = [case["target_0"], case["target_1"], case["target_2"]]
    greedy_failure = False
    route_failure = False
    if tier == "S":
        cheapest, fewest_costs = route_costs(locations, adjacency)
        rule(len(data["claims"]) == 1, "V5", "Each S case needs one claim row.")
        optimum = cargo_value(crates, case["capacity"])
        count_optimum, value_optimum = window_values(windows)
        expected = [
            optimum,
            count_optimum,
            value_optimum,
            drum_value(prices),
            shortest_tour(sites),
            smallest_cover(sensor_nodes, data["sensor_edges"]),
        ]
        actual = [data["claims"][0][field] for field in SCHEMA["claims"][1:]]
        rule(
            actual == expected,
            "V5",
            f"Wrong optimum claims: expected {expected}, found {actual}.",
        )
        greedy_failure = greedy_cargo_value(crates, case["capacity"]) < optimum
        route_failure = any(
            fewest_costs[target] > cheapest[target] for target in targets
        )
    else:
        rule(not data["claims"], "V5", "Claims must be present only for tier S.")

    return greedy_failure, route_failure


def check_case(case, data):
    """Validate structure before references, then check derived facts and stories."""
    rule = case_rule(case["case_id"])
    check_sizes_and_identifiers(case, data)
    check_inventory(case, data, rule)
    network = check_network(case, data, rule)
    log = check_radio(case, data, rule)
    check_windows(case, data, rule)
    alarm_density = check_incidents(case, data, rule)
    check_tour(case, data, rule)
    check_pipeline(case, data, rule)
    check_sensors(case, data, rule)
    safety_density = check_safety(case, data, rule)
    check_rations(case, data, rule)
    greedy_failure, route_failure = check_claims(case, data, network, rule)
    if case["case_no"] <= 45:
        check_scenario(case, data, network, log, alarm_density, rule)
    else:
        check_trap(case, data, network, log, rule)
    return greedy_failure, route_failure, safety_density
