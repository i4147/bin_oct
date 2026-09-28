#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that accepts a CSV file path as a command-line argument, reads it into a pandas DataFrame, and sorts the rows in descending order based on the "score" column.
The script should then export the sorted DataFrame to a JSON file, using the same base filename as the input but with a ".json" extension, saved in the same location.
Use pathlib for handling the file path and suffix replacement."""

import sys
from pathlib import Path
import pandas as pd

fn = Path(sys.argv[1])
df = pd.read_csv(str(fn))
df_sorted = df.sort_values(by="score", ascending=False)
outfile = fn.with_suffix(".json")
df_sorted.to_json(str(outfile))
