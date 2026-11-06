"""
Independently calculate answers needed to verify saved data; no generator algorithms are imported.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    count_matches:
        Counts overlapping phrase matches using KMP. Builds a prefix table and reuses
        partial matches while scanning the log.

    edit_distance:
        Computes minimum insertions, deletions and replacements. Builds one dynamic-
        programming row at a time from the previous row.

    cargo_value:
        Finds the exact indivisible cargo optimum. Updates a capacity table backwards
        for each crate so a crate cannot be reused.

    greedy_cargo_value:
        Measures the ratio-based loading baseline. Orders crates by exact value/weight
        fractions with ID tie breaking, taking those that still fit.

    window_values:
        Finds maximum compatible window count and value. Sorts by finish, finds
        compatible earlier windows with binary search, and fills two dynamic-programming
        tables.

    drum_value:
        Finds the best price for a complete drum. Fills a table of smaller lengths and
        compares every possible first piece.

    distance:
        Measures Manhattan distance between two sites. Adds the absolute horizontal and
        vertical coordinate differences.

    closed_tour_length:
        Measures a supplied visit order. Adds distances for consecutive sites and the
        final return to the first site.

    nearest_tour_length:
        Measures the nearest-neighbor baseline. Starts at zero, chooses the closest
        unvisited site with ID tie breaking, then closes the tour.

    shortest_tour:
        Finds the exact shortest closed tour on small cases. Uses a Held-Karp table
        indexed by visited subset and last site, then adds the return to zero.

    smallest_cover:
        Finds the minimum sensor cover. Enumerates subsets in increasing size and checks
        whether each edge has a selected endpoint.

    make_adjacency:
        Builds graph neighbor lists. Adds each unblocked road in both directions and
        omits road IDs in the blocked set.

    hop_distances:
        Finds the fewest roads from a source. Uses a breadth-first queue and records a
        node distance when first reached.

    route_costs:
        Computes cheapest costs and cheapest costs among fewest-road routes. Uses a
        priority queue for weighted paths, then relaxes edges that advance exactly one
        breadth-first level; every step includes the destination penalty.
"""

import heapq
from bisect import bisect_right
from collections import deque
from itertools import combinations
from fractions import Fraction


def count_matches(text, pattern):
    """Count overlapping occurrences with a prefix table (KMP)."""
    prefix_lengths = [0] * len(pattern)
    matched = 0
    for index in range(1, len(pattern)):
        while matched > 0 and pattern[index] != pattern[matched]:
            matched = prefix_lengths[matched - 1]
        if pattern[index] == pattern[matched]:
            matched += 1
        prefix_lengths[index] = matched
    count = 0
    matched = 0
    for symbol in text:
        while matched > 0 and symbol != pattern[matched]:
            matched = prefix_lengths[matched - 1]
        if symbol == pattern[matched]:
            matched += 1
        if matched == len(pattern):
            count += 1
            matched = prefix_lengths[matched - 1]
    return count


def edit_distance(first, second):
    """Compute the true minimum number of insertions, deletions, replacements."""
    previous_row = list(range(len(second) + 1))
    for first_index, first_symbol in enumerate(first, start=1):
        current_row = [first_index]
        for second_index, second_symbol in enumerate(second, start=1):
            replacement_cost = 0 if first_symbol == second_symbol else 1
            current_row.append(
                min(
                    previous_row[second_index] + 1,
                    current_row[second_index - 1] + 1,
                    previous_row[second_index - 1] + replacement_cost,
                )
            )
        previous_row = current_row
    return previous_row[-1]


def cargo_value(crates, capacity):
    best_values = [0] * (capacity + 1)
    for crate in crates:
        weight, value = crate["weight"], crate["value"]
        for available_weight in range(capacity, weight - 1, -1):
            best_values[available_weight] = max(
                best_values[available_weight],
                value + best_values[available_weight - weight],
            )
    return best_values[capacity]


def greedy_cargo_value(crates, capacity):
    ordered = sorted(
        crates,
        key=lambda crate: (
            -Fraction(crate["value"], crate["weight"]),
            crate["crate_id"],
        ),
    )
    total_value = 0
    for crate in ordered:
        if crate["weight"] <= capacity:
            capacity -= crate["weight"]
            total_value += crate["value"]
    return total_value


def window_values(windows):
    ordered = sorted(windows, key=lambda window: window["finish"])
    finishes = []
    counts = [0]
    values = [0]
    for index, window in enumerate(ordered):
        earlier_count = bisect_right(finishes, window["start"])
        counts.append(max(counts[-1], 1 + counts[earlier_count]))
        values.append(max(values[-1], window["value"] + values[earlier_count]))
        finishes.append(window["finish"])
    return counts[-1], values[-1]


def drum_value(prices):
    best_values = [0] * (len(prices) + 1)
    for total_length in range(1, len(prices) + 1):
        for piece_length in range(1, total_length + 1):
            value = (
                prices[piece_length - 1]["price"]
                + best_values[total_length - piece_length]
            )
            best_values[total_length] = max(best_values[total_length], value)
    return best_values[-1]


def distance(first, second):
    return abs(first["x"] - second["x"]) + abs(first["y"] - second["y"])


def closed_tour_length(sites, order):
    total = 0
    for step in range(len(order)):
        total += distance(sites[order[step]], sites[order[(step + 1) % len(order)]])
    return total


def nearest_tour_length(sites):
    remaining = set(range(1, len(sites)))
    order = [0]
    while remaining:
        current = order[-1]
        next_site = min(
            remaining, key=lambda node: (distance(sites[current], sites[node]), node)
        )
        order.append(next_site)
        remaining.remove(next_site)
    return closed_tour_length(sites, order)


def shortest_tour(sites):
    """Held-Karp table: (visited subset, final site) -> shortest open path."""
    node_count = len(sites)
    paths = {(1, 0): 0}
    for mask in range(1, 1 << node_count, 2):
        for last in range(node_count):
            if (mask, last) not in paths:
                continue
            for next_site in range(1, node_count):
                if mask & (1 << next_site):
                    continue
                key = (mask | (1 << next_site), next_site)
                candidate = paths[(mask, last)] + distance(
                    sites[last], sites[next_site]
                )
                paths[key] = min(paths.get(key, float("inf")), candidate)
    full_mask = (1 << node_count) - 1
    return min(
        paths[(full_mask, last)] + distance(sites[last], sites[0])
        for last in range(1, node_count)
    )


def smallest_cover(node_count, edges):
    for size in range(node_count + 1):
        for nodes in combinations(range(node_count), size):
            selection = set(nodes)
            if all(edge["u"] in selection or edge["v"] in selection for edge in edges):
                return size


def make_adjacency(locations, roads, blocked=None):
    adjacency = [[] for location in locations]
    if blocked is None:
        blocked = set()
    for road in roads:
        if road["road_no"] not in blocked:
            adjacency[road["u"]].append((road["v"], road["minutes"]))
            adjacency[road["v"]].append((road["u"], road["minutes"]))
    return adjacency


def hop_distances(adjacency, source=0):
    distances = [-1] * len(adjacency)
    distances[source] = 0
    pending = deque([source])
    while pending:
        current = pending.popleft()
        for neighbor, minutes in adjacency[current]:
            if distances[neighbor] == -1:
                distances[neighbor] = distances[current] + 1
                pending.append(neighbor)
    return distances


def route_costs(locations, adjacency):
    """Return cheapest costs and the minimum costs among fewest-road routes."""
    hops = hop_distances(adjacency)
    cheapest = [float("inf")] * len(locations)
    cheapest[0] = 0
    pending = [(0, 0)]
    while pending:
        cost, node = heapq.heappop(pending)
        if cost != cheapest[node]:
            continue
        for neighbor, minutes in adjacency[node]:
            candidate = cost + minutes + locations[neighbor]["penalty"]
            if candidate < cheapest[neighbor]:
                cheapest[neighbor] = candidate
                heapq.heappush(pending, (candidate, neighbor))
    fewest_road_costs = [float("inf")] * len(locations)
    fewest_road_costs[0] = 0
    for node in sorted(range(len(locations)), key=lambda node: hops[node]):
        for neighbor, minutes in adjacency[node]:
            if hops[neighbor] == hops[node] + 1:
                candidate = (
                    fewest_road_costs[node] + minutes + locations[neighbor]["penalty"]
                )
                fewest_road_costs[neighbor] = min(
                    fewest_road_costs[neighbor], candidate
                )
    return cheapest, fewest_road_costs
