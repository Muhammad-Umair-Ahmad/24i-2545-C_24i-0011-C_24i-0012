"""
Generate crate records and the deliberately difficult cargo examples.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    make_crates:
        Creates inventory for one case. Uses a repeatable random stream, chooses size
        and categories, samples unique serials, generates crate fields, applies expiry
        rules, and installs designated cargo counterexamples.

    choose_crate_count:
        Chooses the initial number of crates. Selects the tier range, draws a size, then
        applies the special case overrides before counterexample construction.

    choose_categories:
        Creates the required category mix. Fills scenario-specific minimum counts first,
        assigns remaining categories randomly, and shuffles the list.

    apply_cargo_counterexample:
        Makes ratio-based loading perform badly in designated cases. Retains eight or
        twelve rows and sets a light tempting crate, two valuable heavy crates, and low-
        value fillers while preserving the relevant category rules.
"""

import math
from generator.schema import case_id, tier_for, scenario_for
from generator.randomness import rng_for


def make_crates(seed, case_number):
    """Return crate rows, with columns in the order defined in schema.py."""
    random_generator = rng_for(seed, case_number, "crates")
    current_case_id = case_id(seed, case_number)
    tier = tier_for(case_number)
    scenario = scenario_for(case_number)
    is_regular_case = case_number <= 45

    crate_count = choose_crate_count(random_generator, tier, case_number)
    categories = choose_categories(
        random_generator, crate_count, scenario, is_regular_case
    )

    # sample chooses distinct serial numbers, so no two crates share one.
    serial_numbers = random_generator.sample(
        range(10_000_000, 100_000_000), crate_count
    )
    crates = []
    for crate_index in range(crate_count):
        weight = random_generator.randint(1, 20)
        value = random_generator.randint(10, 100)
        expiry = random_generator.randint(0, 999)
        serial_number = serial_numbers[crate_index]

        if is_regular_case and scenario == 6:
            if crate_index < math.ceil(crate_count * 0.5):
                expiry = random_generator.randint(0, 300)

        # Case 46 has deliberately repeated weights and values.
        if case_number == 46:
            weight = 10
            value = 20
            expiry = crate_index % 1000
            serial_number = 10_000_000 + crate_index

        crate_id = crate_index + 1
        category = categories[crate_index]
        crate_row = [
            current_case_id,
            crate_id,
            category,
            weight,
            value,
            expiry,
            serial_number,
        ]
        crates.append(crate_row)

    # Keep this second expiry pass to preserve the existing seeded dataset.
    # Column 5 is expiry: see the crates headings in schema.py.
    if is_regular_case and scenario == 6:
        for crate_index in range(math.ceil(crate_count / 2)):
            crates[crate_index][5] = random_generator.randint(0, 300)
    return apply_cargo_counterexample(crates, scenario, case_number)


def choose_crate_count(random_generator, tier, case_number):
    """Choose a legal tier size before applying explicit trap overrides."""
    if tier == "S":
        minimum_crates = 8
        maximum_crates = 20
    elif tier == "M":
        minimum_crates = 40
        maximum_crates = 200
    else:
        minimum_crates = 500
        maximum_crates = 1500

    crate_count = random_generator.randint(minimum_crates, maximum_crates)
    if case_number == 46:
        crate_count = 1500
    elif case_number == 47:
        crate_count = 20

    return crate_count


def choose_categories(random_generator, crate_count, scenario, is_regular_case):
    """Satisfy the scenario's minimum category mix before filling the rest."""
    # Some scenarios require a minimum proportion of particular categories.
    # ceil rounds up so a fractional crate never falls below the requirement.
    categories = []
    if is_regular_case and scenario == 1:
        required_count = math.ceil(crate_count * 0.55)
        for crate_index in range(required_count):
            categories.append(random_generator.choice([0, 1]))
    elif is_regular_case and scenario == 2:
        required_count = math.ceil(crate_count * 0.45)
        for crate_index in range(required_count):
            categories.append(random_generator.choice([2, 3]))
    elif is_regular_case and scenario == 4:
        required_count = math.ceil(crate_count * 0.10)
        for crate_index in range(required_count):
            categories.append(4)
    elif is_regular_case and scenario == 6:
        required_count = math.ceil(crate_count * 0.55)
        for crate_index in range(required_count):
            categories.append(random_generator.choice([1, 2]))

    # Fill the remaining categories freely, then mix their order.
    while len(categories) < crate_count:
        categories.append(random_generator.randrange(5))
    random_generator.shuffle(categories)

    return categories


def apply_cargo_counterexample(crates, scenario, case_number):
    """Replace weights and values only in the designated greedy counterexamples."""
    # These cases expose the limits of loading by value per kilogram.
    # The tempting 1 kg crate prevents loading both valuable 10 kg crates.
    if case_number < 5 or case_number == 47:
        trap_count = 8 if case_number < 5 else 12
        crates = crates[:trap_count]
        for crate_index, crate in enumerate(crates):
            crate[3] = 19
            crate[4] = 10
            if scenario == 1:
                crate[2] = crate_index % 2
            elif scenario == 2:
                crate[2] = 2 + crate_index % 2
            elif scenario == 4:
                crate[2] = 4
        crates[0][3] = 1
        crates[0][4] = 11
        for crate_index in (1, 2):
            crates[crate_index][3] = 10
            crates[crate_index][4] = 100
    return crates
