# Generator

From the project root:

```bash
python3 generator/main.py --seed 11 --output cases.xlsx
```

`main.py` reads arguments, `builder.py` assembles cases, and `workbook.py` writes Excel. The other files generate their named data modules. `schema.py` defines the required sheets and column order; `claims.py` computes exhaustive tier-S answers.
