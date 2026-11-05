"""
Build individual complete cases and combine them into workbook tables.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    find_targets:
        Finds delivery destinations. Walks through location rows and collects shelter
        and hospital IDs in their existing order.

    choose_capacity:
        Chooses truck capacity. Adds crate weights and takes 40 percent, except for the
        explicitly constructed cargo counterexamples, which use 20 kg.

    generate_case:
        Builds one complete case. Generates inventory and roads, ensures three targets,
        adds all other tables, assembles the case row, and computes exhaustive claims
        only for tier S.

    generate_dataset:
        Builds the full 50-case dataset. Repeats generate_case for numbers 0 through 49,
        appends rows to their matching sheet, and sorts each table by case ID and its
        second column.
"""

from generator.schema import SCHEMA, case_id, tier_for, scenario_for
from generator.inventory import make_crates
from generator.network import make_network
from generator.randomness import rng_for
from generator.additional_data import make_additional_data
from generator.claims import make_claims


def find_targets(locations):
    """Return shelter and hospital IDs in location order."""
    targets = []
    for location in locations:
        location_id = location[1]
        location_type = location[2]
        if location_type in ("S", "H"):
            targets.append(location_id)
    return targets


def choose_capacity(crates, case_number):
    """Use 40% of total weight, except for the explicit cargo counterexamples."""
    total_weight = 0
    for crate in crates:
        total_weight += crate[3]
    if case_number < 5 or case_number == 47:
        return 20
    return max(1, total_weight * 40 // 100)


def generate_case(seed, case_number):
    """Create one complete case. All random choices remain in a fixed order."""
    identifier = case_id(seed, case_number)
    tier = tier_for(case_number)
    scenario = scenario_for(case_number)

    # 1. Generate inventory and the road network using separate random streams.
    crates = make_crates(seed, case_number)
    locations, roads, waves = make_network(seed, case_number)
    capacity = choose_capacity(crates, case_number)

    # 2. Ensure three non-HQ targets exist before collecting the location rows.
    targets = find_targets(locations)
    if len(targets) < 3:
        locations[3][2] = "S"
        targets = find_targets(locations)

    # 3. Generate the remaining tables in their documented random-draw order.
    random_generator = rng_for(seed, case_number, "additional-data")
    data, fields = make_additional_data(
        case_number, identifier, tier, scenario, random_generator
    )
    data["crates"] = crates
    data["locations"] = locations
    data["roads"] = roads
    data["waves"] = waves

    # 4. Assemble the case row explicitly in the shared workbook column order.
    data["cases"] = [
        [
            identifier,
            seed,
            case_number,
            tier,
            scenario,
            capacity,
            targets[0],
            targets[1],
            targets[2],
            fields["edit_bound"],
            fields["tour_length"],
            fields["sensor_nodes"],
            fields["sensor_k"],
            fields["safety_vars"],
            fields["rations_target"],
        ]
    ]

    # 5. Claims belong only to small cases and use exhaustive reference searches.
    data["claims"] = []
    if tier == "S":
        claim = make_claims(identifier, crates, capacity, data, fields["sensor_nodes"])
        data["claims"].append(claim)
    return data


def generate_dataset(seed):
    """Collect all 50 cases into the 20 required workbook tables."""
    tables = {}
    for sheet_name in SCHEMA:
        tables[sheet_name] = []
    for case_number in range(50):
        case_data = generate_case(seed, case_number)
        for sheet_name, rows in case_data.items():
            tables[sheet_name].extend(rows)
    for rows in tables.values():
        rows.sort(key=lambda row: (row[0], row[1]))
    return tables
