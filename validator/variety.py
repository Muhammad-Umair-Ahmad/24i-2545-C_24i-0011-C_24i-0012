"""
Track requirements that can only be checked across the complete collection of cases.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    VarietyChecks:
        Keeps counters and module fingerprints while validation visits cases. Its
        methods collect evidence and enforce dataset-wide V7 minimums.

    VarietyChecks.__init__:
        Starts an empty tracker. Creates sets of seen module fingerprints and zeroes
        cargo, route and safety-density counters.

    VarietyChecks.record:
        Records checked evidence from one case. Increments the small-case failure
        counters, assigns M/L safety density to its band, and checks module uniqueness.

    VarietyChecks.check_unique_modules:
        Detects repeated logical modules of size eight or more. Combines their tables
        and relevant case fields without case IDs, hashes the content, and compares it
        with fingerprints already seen.

    VarietyChecks.finish:
        Checks the final variety totals. Enforces five cargo failures, five route
        failures and the required safety-density band counts, then returns a readable
        summary.
"""

import hashlib
from collections import defaultdict
from generator.schema import SCHEMA
from validator.rules import require


class VarietyChecks:
    """Collect evidence across cases, then enforce the dataset-wide minimums."""

    def __init__(self):
        self.seen_modules = defaultdict(set)
        self.greedy_failures = 0
        self.route_failures = 0
        self.density_groups = [0, 0, 0]

    def record(self, case, data, cargo_greedy_failure, fewest_roads_failure, density):
        """Record checked facts; do not recompute or trust supplied claims here."""
        self.greedy_failures += cargo_greedy_failure
        self.route_failures += fewest_roads_failure
        if case["tier"] in ("M", "L"):
            if density < 3.5:
                self.density_groups[0] += 1
            elif density <= 4.8:
                self.density_groups[1] += 1
            else:
                self.density_groups[2] += 1
        self.check_unique_modules(case, data)

    def check_unique_modules(self, case, data):
        """Ignore case IDs when comparing complete logical modules."""
        # Compare complete logical modules, not IDs or individual planted rows.
        # For example, two valid assignments may match while their safety rules differ.
        module_definitions = {
            "crates": (len(data["crates"]), ["crates"], ["capacity"]),
            "network": (
                len(data["locations"]),
                ["locations", "roads", "waves"],
                ["target_0", "target_1", "target_2"],
            ),
            "radio": (
                sum(len(row["text"]) for row in data["radio_log"]),
                ["radio_log", "radio_patterns", "radio_reports"],
                ["edit_bound"],
            ),
            "windows": (len(data["windows"]), ["windows"], []),
            "incidents": (len(data["incidents"]), ["incidents"], []),
            "tour": (len(data["sites"]), ["sites", "tour"], ["tour_length"]),
            "pipeline": (
                max(len(data["pipeline_dims"]) - 1, len(data["drum_prices"])),
                ["pipeline_dims", "drum_prices"],
                [],
            ),
            "sensors": (
                case["sensor_nodes"],
                ["sensor_edges", "sensor_cover"],
                ["sensor_nodes", "sensor_k"],
            ),
            "safety": (
                case["safety_vars"],
                ["safety_rules", "safety_planted"],
                ["safety_vars"],
            ),
            "rations": (len(data["rations"]), ["rations"], ["rations_target"]),
        }
        for module_name, (size, sheet_names, case_fields) in module_definitions.items():
            if size < 8:
                continue
            content = []
            for sheet_name in sheet_names:
                for row in data[sheet_name]:
                    content.append(
                        tuple(row[field] for field in SCHEMA[sheet_name][1:])
                    )
            content.append(tuple(case[field] for field in case_fields))
            fingerprint = hashlib.sha256(repr(content).encode("ascii")).digest()
            require(
                fingerprint not in self.seen_modules[module_name],
                "V7",
                f'{module_name}: duplicate module data in {case["case_id"]}.',
            )
            self.seen_modules[module_name].add(fingerprint)

    def finish(self):
        """Enforce all cross-case totals and return a human-readable summary."""
        require(
            self.greedy_failures >= 5,
            "V7",
            "Need five S cases where cargo greedy is suboptimal.",
        )
        require(
            self.route_failures >= 5,
            "V7",
            "Need five S cases where fewest-road routes cost more.",
        )
        low, middle, high = self.density_groups
        require(
            low >= 5 and middle >= 8 and high >= 5,
            "V7",
            f"Insufficient safety density variety: {self.density_groups}.",
        )
        return (
            f"Variety: {self.greedy_failures} cargo failures, "
            f"{self.route_failures} route failures; safety density groups {self.density_groups}."
        )
