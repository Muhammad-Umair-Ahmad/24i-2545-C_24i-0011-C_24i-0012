"""
Compute the exhaustive small-case answers required by Iteration 1.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    cargo_optimum:
        Finds the highest crate value within capacity. Recursively explores leaving out
        or including each indivisible crate.

    cargo_optimum.search:
        Explores one cargo decision. Advances the crate index, tracks remaining
        capacity, and returns the better value from the legal branches.

    window_optima:
        Finds the most compatible windows and the highest compatible total value. Sorts
        windows by start and explores valid selections; touching windows are allowed.

    window_optima.search:
        Explores one window decision. Tries skipping the current window or taking it
        when its start is not before the previous finish, and tracks the two objectives
        separately.

    drum_optimum:
        Finds the maximum price obtainable from a whole drum. Tries every possible first
        piece and recursively prices the remaining length.

    drum_optimum.search:
        Prices a remaining drum length. Returns zero for no material, otherwise chooses
        the best first cut plus the best value of the remainder.

    tour_length:
        Measures a planted tour. Adds horizontal and vertical coordinate differences
        between consecutive sites, including the return to the starting site.

    tour_optimum:
        Finds the shortest closed tour. Fixes site 0 first, tries every permutation of
        the remaining sites, and keeps the smallest Manhattan length.

    cover_optimum:
        Finds the smallest sensor cover. Tries node subsets from smallest to largest and
        returns the first size that touches every edge.

    make_claims:
        Creates one claims row. Calls the six exhaustive reference calculations and
        places their answers in workbook column order.
"""

from itertools import combinations, permutations


def cargo_optimum(crates, capacity):
    """Try including and excluding every crate that can fit."""

    def search(index, remaining_capacity):
        if index == len(crates):
            return 0
        best_value = search(index + 1, remaining_capacity)
        weight = crates[index][3]
        value = crates[index][4]
        if weight <= remaining_capacity:
            included_value = value + search(index + 1, remaining_capacity - weight)
            best_value = max(best_value, included_value)
        return best_value

    return search(0, capacity)


def window_optima(windows):
    """Explore every compatible selection, allowing touching intervals."""
    ordered_windows = sorted(windows, key=lambda window: window[2])

    def search(index, previous_finish):
        if index == len(ordered_windows):
            return 0, 0
        best_count, best_value = search(index + 1, previous_finish)
        window = ordered_windows[index]
        start, finish, value = window[2:5]
        if start >= previous_finish:
            later_count, later_value = search(index + 1, finish)
            best_count = max(best_count, 1 + later_count)
            best_value = max(best_value, value + later_value)
        return best_count, best_value

    return search(0, 0)


def drum_optimum(prices):
    """Try every possible first cut and recursively try the remaining cuts."""

    def search(remaining_length):
        if remaining_length == 0:
            return 0
        best_price = 0
        for piece_length in range(1, remaining_length + 1):
            total_price = prices[piece_length - 1][2] + search(
                remaining_length - piece_length
            )
            best_price = max(best_price, total_price)
        return best_price

    return search(len(prices))


def tour_length(sites, order):
    """Measure the closed tour using Manhattan (horizontal + vertical) distance."""
    total_length = 0
    for step in range(len(order)):
        first_site = sites[order[step]]
        second_site = sites[order[(step + 1) % len(order)]]
        total_length += abs(first_site[2] - second_site[2])
        total_length += abs(first_site[3] - second_site[3])
    return total_length


def tour_optimum(sites):
    """Hold site 0 fixed and try every order of the other sites."""
    best_length = None
    for remaining_order in permutations(range(1, len(sites))):
        order = [0] + list(remaining_order)
        length = tour_length(sites, order)
        if best_length is None or length < best_length:
            best_length = length
    return best_length


def cover_optimum(node_count, edges):
    """Try node subsets from smallest to largest until every edge is touched."""
    for size in range(node_count + 1):
        for selection in combinations(range(node_count), size):
            selected_nodes = set(selection)
            covers_all_edges = True
            for edge in edges:
                if edge[1] not in selected_nodes and edge[2] not in selected_nodes:
                    covers_all_edges = False
                    break
            if covers_all_edges:
                return size


def make_claims(case_identifier, crates, capacity, data, sensor_nodes):
    window_count, window_value = window_optima(data["windows"])
    return [
        case_identifier,
        cargo_optimum(crates, capacity),
        window_count,
        window_value,
        drum_optimum(data["drum_prices"]),
        tour_optimum(data["sites"]),
        cover_optimum(sensor_nodes, data["sensor_edges"]),
    ]
