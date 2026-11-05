"""
Generate optional G data and the other planted objects required in the workbook.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    nearest_tour:
        Builds a nearest-neighbor visit order. Starts at site 0, repeatedly chooses the
        closest unvisited site by Manhattan distance, and breaks ties by smaller site
        ID.

    make_sites_and_tour:
        Creates distinct relief-site coordinates and a valid tour. Samples grid points
        without replacement, builds a nearest-neighbor order, and measures the closed
        length.

    make_pipeline:
        Creates matrix-chain dimensions and drum prices for G. Draws legal dimensions
        and positive prices, then adjusts the first two prices to prevent proportional
        pricing.

    make_sensors:
        Creates a graph with a known cover. Chooses cover nodes first, connects other
        nodes to them, and links the cover nodes so every edge touches the cover.

    make_safety:
        Creates satisfiable three-literal rules. Chooses a Boolean assignment, selects
        rule density, and forces one literal of every generated rule to match the
        assignment.

    make_rations:
        Creates quantities with a known target selection. Draws positive values and
        selection flags, forces the first item to be selected, and sums selected values
        into the target.
"""

import math
from generator.claims import tour_length
from generator.randomness import size_for


def nearest_tour(sites):
    """Choose the nearest unvisited site; break ties by the smaller site ID."""
    remaining = set(range(1, len(sites)))
    order = [0]
    while remaining:
        current_site = sites[order[-1]]
        best_site = None
        best_distance = None
        for site_id in sorted(remaining):
            candidate = sites[site_id]
            distance = abs(current_site[2] - candidate[2]) + abs(
                current_site[3] - candidate[3]
            )
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_site = site_id
        order.append(best_site)
        remaining.remove(best_site)
    return order


def make_sites_and_tour(random_generator, case_identifier, tier):
    """Plant a nearest-neighbor tour through distinct grid sites."""
    data = {}
    site_count = size_for(random_generator, tier, (5, 7), (10, 16), (200, 500))
    coordinates = random_generator.sample(range(1000000), site_count)
    sites = []
    for site_number, coordinate in enumerate(coordinates):
        sites.append(
            [case_identifier, site_number, coordinate // 1000, coordinate % 1000]
        )
    data["sites"] = sites
    order = nearest_tour(sites)
    data["tour"] = []
    for step, site_number in enumerate(order):
        data["tour"].append([case_identifier, step, site_number])
    planted_tour_length = tour_length(sites, order)

    return data, planted_tour_length


def make_pipeline(random_generator, case_identifier, tier):
    """Generate matrix dimensions and non-proportional drum prices for G."""
    data = {}
    stages = size_for(random_generator, tier, (4, 8), (15, 60), (100, 300))
    data["pipeline_dims"] = []
    for index in range(stages + 1):
        data["pipeline_dims"].append(
            [case_identifier, index, random_generator.randint(2, 100)]
        )
    drum_length = size_for(random_generator, tier, (5, 10), (40, 200), (500, 2000))
    data["drum_prices"] = []
    for length in range(1, drum_length + 1):
        data["drum_prices"].append(
            [case_identifier, length, random_generator.randint(1, 500)]
        )
    # These two unequal price-per-unit values rule out proportional prices.
    data["drum_prices"][0][2] = random_generator.randint(2, 100)
    data["drum_prices"][1][2] = data["drum_prices"][0][2] + 1

    return data


def make_sensors(random_generator, case_identifier, tier):
    """Plant a cover, then create only edges touched by that cover."""
    data = {}
    sensor_nodes = size_for(random_generator, tier, (6, 10), (20, 40), (100, 400))
    cover_size = random_generator.randint(2, sensor_nodes // 2)
    cover_nodes = sorted(random_generator.sample(range(sensor_nodes), cover_size))
    edges = set()
    # Join every non-cover node to a cover node, and link the cover nodes.
    # The graph is connected and every edge touches the planted cover.
    for node in range(sensor_nodes):
        if node not in cover_nodes:
            cover_node = random_generator.choice(cover_nodes)
            edges.add(tuple(sorted((node, cover_node))))
    for index in range(1, cover_size):
        edges.add(tuple(sorted((cover_nodes[index - 1], cover_nodes[index]))))
    data["sensor_edges"] = []
    for first_node, second_node in sorted(edges):
        data["sensor_edges"].append([case_identifier, first_node, second_node])
    data["sensor_cover"] = []
    for node in cover_nodes:
        data["sensor_cover"].append([case_identifier, node])

    return data, sensor_nodes, cover_size


def make_safety(random_generator, case_identifier, tier, case_number):
    """Plant a Boolean assignment and generate clauses it satisfies."""
    data = {}
    switches = size_for(random_generator, tier, (6, 15), (20, 50), (20, 50))
    assignment = {}
    data["safety_planted"] = []
    for switch in range(1, switches + 1):
        assignment[switch] = random_generator.randint(0, 1)
        data["safety_planted"].append([case_identifier, switch, assignment[switch]])
    # The 26 M/L cases cycle through low, middle, and high rule densities.
    density = (3.0, 4.0, 5.5)[case_number % 3]
    rule_count = math.ceil(switches * density)
    data["safety_rules"] = []
    for rule_number in range(1, rule_count + 1):
        chosen_switches = random_generator.sample(range(1, switches + 1), 3)
        literals = []
        for switch in chosen_switches:
            sign = random_generator.choice([-1, 1])
            literals.append(sign * switch)
        # Force the first literal to be true under the planted assignment.
        first_switch = chosen_switches[0]
        if assignment[first_switch] == 1:
            literals[0] = first_switch
        else:
            literals[0] = -first_switch
        data["safety_rules"].append([case_identifier, rule_number] + literals)

    return data, switches


def make_rations(random_generator, case_identifier, tier):
    """Plant a nonempty selection and use its sum as the target."""
    data = {}
    ration_count = size_for(random_generator, tier, (8, 20), (24, 40), (50, 100))
    data["rations"] = []
    rations_target = 0
    for item in range(ration_count):
        value = random_generator.randint(1, 1000)
        planted = random_generator.randint(0, 1)
        if item == 0:
            planted = 1
        if planted == 1:
            rations_target += value
        data["rations"].append([case_identifier, item, value, planted])
    return data, rations_target
