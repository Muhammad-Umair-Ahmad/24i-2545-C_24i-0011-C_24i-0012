"""
Assemble the remaining Iteration 1 tables after inventory and roads.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    make_additional_data:
        Creates radio, rescue windows, alarms, tours, pipeline, sensors, safety and
        rations. Calls each domain generator in a fixed order, merges their tables, and
        returns named fields needed by the cases sheet.
"""

from generator.radio import make_radio_rows
from generator.scheduling import make_windows, make_incidents
from generator.planning import (
    make_sites_and_tour,
    make_pipeline,
    make_sensors,
    make_safety,
    make_rations,
)


def make_additional_data(
    case_number, case_identifier, tier, scenario, random_generator
):
    """Return generated tables and named fields for the cases sheet."""
    data, edit_bound = make_radio_rows(
        random_generator, case_identifier, tier, scenario, case_number
    )
    data["windows"] = []
    for window in make_windows(random_generator, tier, scenario):
        data["windows"].append([case_identifier] + window)
    data["incidents"] = make_incidents(
        random_generator, case_identifier, tier, scenario
    )
    tour_data, tour_length = make_sites_and_tour(
        random_generator, case_identifier, tier
    )
    data.update(tour_data)
    data.update(make_pipeline(random_generator, case_identifier, tier))
    sensor_data, sensor_nodes, sensor_k = make_sensors(
        random_generator, case_identifier, tier
    )
    data.update(sensor_data)
    safety_data, safety_vars = make_safety(
        random_generator, case_identifier, tier, case_number
    )
    data.update(safety_data)
    ration_data, rations_target = make_rations(random_generator, case_identifier, tier)
    data.update(ration_data)
    case_fields = {
        "edit_bound": edit_bound,
        "tour_length": tour_length,
        "sensor_nodes": sensor_nodes,
        "sensor_k": sensor_k,
        "safety_vars": safety_vars,
        "rations_target": rations_target,
    }
    return data, case_fields
