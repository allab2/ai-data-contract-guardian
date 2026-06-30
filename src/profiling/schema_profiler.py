"""
schema_profiler.py
------------------
Extracts the actual schema from a DataFrame: column names, data types,
null counts, unique counts, and basic statistics. This "observed schema"
is compared against the data contract to detect drift and quality issues.
"""

import pandas as pd
from typing import Any


def profile_schema(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Extract the observed schema profile from a DataFrame.

    Returns a list of column descriptors, each containing:
      - name: column name
      - dtype: Pandas dtype as string
      - null_count: number of null values
      - null_pct: percentage of null values
      - unique_count: number of unique non-null values
      - sample_values: up to 5 example values

    Args:
        df: The DataFrame to profile.

    Returns:
        A list of dicts describing each column.
    """
    # TODO: Implement full schema profiling logic
    # TODO: Add min/max/mean for numeric columns
    # TODO: Add pattern detection for string columns
    profile = []
    for col in df.columns:
        profile.append(
            {
                "name": col,
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "null_pct": round(df[col].isnull().mean(), 4),
                "unique_count": int(df[col].nunique()),
                "sample_values": df[col].dropna().head(5).tolist(),
            }
        )
    return profile
