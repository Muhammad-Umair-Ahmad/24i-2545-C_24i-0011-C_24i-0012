"""
Generate locations, connected roads and disjoint road-closure waves.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    make_network:
        Coordinates one road network. Chooses its size, builds locations and endpoint
        pairs, assigns road fields, and selects closure waves before returning the three
        tables.

    make_locations:
        Creates depot, shelter, hospital and junction rows. Keeps location 0 as HQ,
        guarantees a shelter and hospital, and applies penalty or shelter-count scenario
        rules.

    count_shelters:
        Counts shelters. Reads each location type and increments a counter when it is S.

    make_road_endpoints:
        Creates connected undirected links. Starts with a chain or links each new node
        to an earlier node, adds deliberate detours where required, and inserts unique
        edges until the required density is reached.

    make_roads:
        Turns endpoint pairs into road rows. Sorts the pairs for stable IDs, draws
        travel minutes and cable costs, and applies the costly-direct-road examples.

    make_closure_waves:
        Creates disjoint closure rows. Samples distinct road IDs, enforces the corridor
        cut, and closes both HQ exits in the small corridor counterexample.
"""

import math
from generator.schema import case_id, tier_for, scenario_for
from generator.randomness import rng_for


def make_network(seed, case_number):
    """Return location rows, road rows, and road-closure rows for one case."""
    random_generator = rng_for(seed, case_number, "network")
    current_case_id = case_id(seed, case_number)
    tier = tier_for(case_number)
    scenario = scenario_for(case_number)
    is_regular_case = case_number <= 45

    if tier == "S":
        minimum_locations = 6
        maximum_locations = 12
    elif tier == "M":
        minimum_locations = 30
        maximum_locations = 150
    else:
        minimum_locations = 500
        maximum_locations = 2000
    location_count = random_generator.randint(minimum_locations, maximum_locations)
    if case_number == 48:
        location_count = 1500

    locations = make_locations(
        random_generator, current_case_id, location_count, scenario, is_regular_case
    )
    if case_number == 48:
        locations[1][3] = 0
        locations[2][3] = 0
    endpoints = make_road_endpoints(
        random_generator, location_count, scenario, case_number, is_regular_case
    )
    roads = make_roads(random_generator, current_case_id, endpoints, case_number)
    waves = make_closure_waves(
        random_generator, current_case_id, roads, scenario, case_number, is_regular_case
    )
    return locations, roads, waves


def make_locations(
    random_generator, current_case_id, location_count, scenario, is_regular_case
):
    """Choose location types and apply the scenario-specific minimums."""
    locations = []
    for location_id in range(location_count):
        if location_id == 0:
            location_type = "D"
            penalty = 0
        else:
            # S = shelter, H = hospital, J = junction; D is the starting depot.
            # The weights 3, 2, 5 make junctions the most likely type.
            location_type = random_generator.choices(["S", "H", "J"], [3, 2, 5])[0]
            penalty = random_generator.choice([0, 1, 2, 4, 6])
        locations.append([current_case_id, location_id, location_type, penalty])

    # Every case must have at least one shelter and one hospital.
    locations[1][2] = "S"
    locations[2][2] = "H"
    if is_regular_case and scenario == 1:
        required_count = math.ceil(location_count * 0.4)
        for location in locations[1 : required_count + 1]:
            location[3] = random_generator.choice([2, 4, 6])
    if is_regular_case and scenario == 3:
        required_shelters = math.ceil(location_count * 0.25)
        for location in locations[1 : required_shelters + 1]:
            location[2] = "S"
        locations[2][2] = "H"
        if count_shelters(locations) < required_shelters:
            for location in locations[3:]:
                if location[2] != "S":
                    location[2] = "S"
                if count_shelters(locations) >= required_shelters:
                    break

    return locations


def count_shelters(locations):
    """Count rows whose location type is S."""
    shelter_count = 0
    for location in locations:
        location_type = location[2]
        if location_type == "S":
            shelter_count += 1
    return shelter_count


def make_road_endpoints(
    random_generator, location_count, scenario, case_number, is_regular_case
):
    """Connect every location, then add enough edges for the scenario."""
    # Each pair stores the two location IDs joined by a road.
    # A set prevents duplicate roads. Put the smaller ID first in every pair.
    road_endpoints = set()
    if scenario == 5 or case_number == 48 or case_number < 5:
        # A chain looks like 0--1--2--3. Removing an edge breaks the route.
        for location_id in range(1, location_count):
            road_endpoints.add((location_id - 1, location_id))
    else:
        # Connect each new location to an earlier one. This guarantees that
        # every location has a route back to location 0.
        for location_id in range(1, location_count):
            earliest_neighbor = max(0, location_id - 6)
            earlier_location = random_generator.randrange(
                earliest_neighbor, location_id
            )
            road_endpoints.add((earlier_location, location_id))

    if case_number < 5:
        road_endpoints.add((0, 2))
    if case_number == 48:
        # A direct costly edge is shorter in hops than the cheap two-edge route.
        road_endpoints.add((0, 2))

    # Average degree means the average number of roads touching a location.
    # Each road touches two locations, so road count = degree * locations / 2.
    minimum_average_degree = 2.0
    if is_regular_case:
        if scenario == 1:
            minimum_average_degree = 2.2
        elif scenario == 2:
            minimum_average_degree = 2.0
        elif scenario == 4:
            minimum_average_degree = 3.5
        elif scenario == 5:
            minimum_average_degree = 2.0 * (location_count - 1) / location_count
        else:
            minimum_average_degree = 2.1
    required_road_count = math.ceil(minimum_average_degree * location_count / 2)
    required_road_count = max(location_count - 1, required_road_count)
    if (is_regular_case and scenario == 5) or case_number == 48:
        required_road_count = location_count - 1
    if case_number == 48:
        required_road_count = location_count

    while len(road_endpoints) < required_road_count:
        first_location = random_generator.randrange(location_count)
        second_location = random_generator.randrange(location_count)
        if first_location == second_location:
            continue
        if first_location > second_location:
            first_location, second_location = second_location, first_location
        road_endpoints.add((first_location, second_location))

    return road_endpoints


def make_roads(random_generator, current_case_id, road_endpoints, case_number):
    """Assign stable road IDs, travel minutes and cable costs."""
    # Sort before assigning road numbers so the output order is repeatable.
    roads = []
    for road_number, endpoints in enumerate(sorted(road_endpoints)):
        first_location, second_location = endpoints
        travel_minutes = random_generator.randint(1, 60)
        if case_number < 5 or case_number == 48:
            travel_minutes = 1
            if first_location == 0 and second_location == 1:
                travel_minutes = 60
        cable = random_generator.randint(1, 100)
        roads.append(
            [
                current_case_id,
                road_number,
                first_location,
                second_location,
                travel_minutes,
                cable,
            ]
        )

    return roads


def make_closure_waves(
    random_generator, current_case_id, roads, scenario, case_number, is_regular_case
):
    """Choose distinct roads and preserve the corridor disconnection guarantee."""
    if is_regular_case and scenario in (1, 3, 5):
        wave_count = 3
    else:
        wave_count = random_generator.randint(2, 5)
    selection_count = min(wave_count, len(roads))
    selected_roads = random_generator.sample(range(len(roads)), selection_count)
    if is_regular_case and scenario == 5:
        # Make the first closure cut off the depot from the rest of the chain.
        for road in roads:
            if road[2] == 0 and road[3] == 1:
                selected_roads[0] = road[1]
                break
        unique_roads = []
        for road_number in selected_roads:
            if road_number not in unique_roads:
                unique_roads.append(road_number)
        selected_roads = unique_roads
        while len(selected_roads) < wave_count:
            road_number = random_generator.randrange(len(roads))
            if road_number not in selected_roads:
                selected_roads.append(road_number)

    if case_number == 4:
        # This small corridor also contains the route-comparison detour 0--2.
        # Close both exits from HQ across the waves so the union still cuts it off.
        depot_exits = []
        for road in roads:
            if road[2] == 0:
                depot_exits.append(road[1])
        revised_selection = list(depot_exits)
        for road_number in selected_roads:
            if road_number not in revised_selection:
                revised_selection.append(road_number)
        selected_roads = revised_selection[:wave_count]

    waves = []
    for wave_number, road_number in enumerate(selected_roads, start=1):
        waves.append([current_case_id, wave_number, road_number])
    return waves
