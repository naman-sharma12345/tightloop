# app-01: csvstat (Python, stdlib only)

Build a command-line tool `csvstat.py` in the workspace root. It is run as:

    python3 csvstat.py FILE COLUMN OP

- FILE: path to a CSV file whose first row is a header.
- COLUMN: a column name from the header.
- OP: one of `count`, `min`, `max`, `mean`.

Behavior:
- `count` prints the number of non-empty values in the column.
- `min` / `max` print the smallest / largest numeric value in the column.
- `mean` prints the arithmetic mean of the numeric values, rounded to 2
  decimal places (standard Python round-half-to-even is fine).
- Values that are empty strings are ignored by every op.
- Output is the single number followed by a newline, nothing else.
- If the file does not exist, the column is missing, or the column has no
  usable numeric values (for min/max/mean), print an error to stderr and
  exit with status 1.

Only the Python standard library may be used.
