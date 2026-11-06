"""
Verify the deliberately hostile properties of cases 46 through 49.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    check_trap:
        Checks the applicable trap. Counts monotone cargo fields for 46, compares exact
        greedy/optimal values for 47, proves a long hop distance and cost inequality for
        48, and checks short-block repetition and near-miss prefixes for 49.
"""

from collections import Counter
from fractions import Fraction
from validator.reference import (
    cargo_value,
    greedy_cargo_value,
    hop_distances,
    route_costs,
    count_matches,
)


def check_trap(case, data, network, log, rule):
    """Verify the deliberately hostile property of cases 46 through 49."""
    adjacency = network["adjacency"]
    number = case["case_no"]
    if number == 46:
        crates = data["crates"]
        fields = []
        for name in ("value", "weight", "expiry", "serial"):
            fields.append([crate[name] for crate in crates])
        fields.append([Fraction(crate["value"], crate["weight"]) for crate in crates])
        monotone_count = 0
        for values in fields:
            if values == sorted(values) or values == sorted(values, reverse=True):
                monotone_count += 1
        rule(monotone_count >= 3, "V8", "Dock-order trap needs three monotone fields.")
    elif number == 47:
        optimum = cargo_value(data["crates"], case["capacity"])
        greedy = greedy_cargo_value(data["crates"], case["capacity"])
        rule(
            5 * greedy <= 3 * optimum,
            "V8",
            "Greedy cargo value exceeds 60% of optimum.",
        )
    elif number == 48:
        cheapest, fewest_costs = route_costs(data["locations"], adjacency)
        # A single pair 500 hops apart proves that the graph diameter is >= 500.
        # Search other sources only if source 0 does not already prove it.
        long_distance_found = False
        for source in range(len(adjacency)):
            if max(hop_distances(adjacency, source)) >= 500:
                long_distance_found = True
                break
        targets = [case["target_0"], case["target_1"], case["target_2"]]
        rule(
            long_distance_found
            and any(
                2 * fewest_costs[target] >= 3 * cheapest[target] for target in targets
            ),
            "V8",
            "Shortest-looks-cheapest trap failed.",
        )
    elif number == 49:
        repeated_block_found = False
        # Count complete, non-overlapping copies of a short block. Candidate
        # blocks come from every start position, including shifted repetitions.
        for block_length in range(1, 9):
            candidates = Counter(
                log[index : index + block_length]
                for index in range(len(log) - block_length + 1)
            )
            for block, frequency in candidates.items():
                if frequency * block_length < 0.9 * len(log):
                    continue
                covered_symbols = log.count(block) * block_length
                if covered_symbols >= 0.9 * len(log):
                    repeated_block_found = True
        near_misses = 0
        for pattern in data["radio_patterns"]:
            prefix = pattern["pattern"][:-1]
            possible_starts = len(log) - len(pattern["pattern"]) + 1
            prefix_matches = count_matches(log[: len(log) - 1], prefix)
            if prefix_matches >= possible_starts / 2:
                near_misses += 1
        rule(
            repeated_block_found and near_misses >= 4,
            "V8",
            "Near-miss repetition or prefix-match requirement failed.",
        )
