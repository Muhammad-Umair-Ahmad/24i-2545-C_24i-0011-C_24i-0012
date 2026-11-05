"""
Provide repeatable random generators and size choices by tier.

Contents and execution:
    The functions below implement this file's responsibility.
    Importing this file does not run the full program or create output files.

Functions and classes:
    rng_for:
        Creates an independent random generator for one case and module. Hashes a label
        containing seed, case number and module with SHA-256, converts the hash bytes to
        an integer, and seeds random.Random.

    size_for:
        Chooses a legal size for a tier. Selects the small, medium or large range and
        draws an integer between its bounds; X uses the large range.
"""

import hashlib
import random


def rng_for(seed, case_number, module):
    """Create repeatable random numbers for one case and one part of its data."""
    # Example label: LIFELINE|11|0|crates
    label = f"LIFELINE|{seed}|{case_number}|{module}"

    # Hashing turns that label into a consistent number. The same label always gives the same number, even when we run Python again another day.
    label_bytes = label.encode("ascii")
    hash_bytes = hashlib.sha256(label_bytes).digest()

    random_seed = int.from_bytes(hash_bytes, "big")

    # Keep a separate generator for crates and roads so they do not interfere.
    return random.Random(random_seed)


def size_for(random_generator, tier, small_range, medium_range, large_range):
    if tier == "S":
        minimum, maximum = small_range
    elif tier == "M":
        minimum, maximum = medium_range
    else:
        minimum, maximum = large_range
    return random_generator.randint(minimum, maximum)
