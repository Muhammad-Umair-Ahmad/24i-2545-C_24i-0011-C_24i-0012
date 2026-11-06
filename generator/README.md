# Generator

Writes `cases.xlsx` (50 cases, 20 sheets) from the group seed.

## Reproduce

From the project root:

```bash
pip install -r requirements.txt
python -m generator.main --seed 11 --output cases.xlsx
```

On Windows use `python`. On Linux or macOS use `python3`.

Group seed: 11. The same seed always produces the same workbook.

## Files

- `main.py`: reads arguments and starts the build
- `builder.py`: assembles each case
- `workbook.py`: writes the Excel file
- `schema.py`: defines the required sheets and column order
- `claims.py`: computes exhaustive tier-S answers for the `claims` sheet
- `inventory.py`, `network.py`, `radio.py`, `scheduling.py`, `planning.py`, `additional_data.py`: generate the named data modules
- `randomness.py`: seeded random generators

## Libraries

- `openpyxl`: used only to write the `.xlsx` file. It does no generation or algorithm work.