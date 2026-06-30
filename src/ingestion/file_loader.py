"""
file_loader.py
--------------
Loads incoming data files (CSV, Parquet, JSON) into Pandas DataFrames
and optionally registers them as DuckDB tables for SQL-based profiling.
"""

import pandas as pd
import duckdb
from pathlib import Path


def load_csv(file_path: str) -> pd.DataFrame:
    """Load a CSV file into a Pandas DataFrame.

    Args:
        file_path: Path to the CSV file.

    Returns:
        A Pandas DataFrame containing the file contents.

    Raises:
        FileNotFoundError: If the file does not exist.
        pd.errors.ParserError: If the file cannot be parsed as CSV.
    """
    # TODO: Add support for configurable delimiters, encodings, and date parsing
    # TODO: Add logging for file load events
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_csv(file_path)


def register_in_duckdb(
    df: pd.DataFrame, table_name: str, con: duckdb.DuckDBPyConnection = None
) -> duckdb.DuckDBPyConnection:
    """Register a DataFrame as a DuckDB virtual table for SQL queries.

    Args:
        df: The DataFrame to register.
        table_name: Name for the virtual table.
        con: Optional existing DuckDB connection.

    Returns:
        The DuckDB connection with the table registered.
    """
    # TODO: Add support for persistent DuckDB databases
    # TODO: Add schema inference logging
    if con is None:
        con = duckdb.connect()
    con.register(table_name, df)
    return con
