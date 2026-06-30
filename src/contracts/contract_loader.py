"""
contract_loader.py
------------------
Loads and parses YAML data contract definitions. Each contract specifies
the expected schema, column-level constraints, and quality thresholds
for a particular data feed.
"""

import yaml
from pathlib import Path
from typing import Any


def load_contract(contract_path: str) -> dict[str, Any]:
    """Load a YAML data contract file and return it as a dictionary.

    Args:
        contract_path: Path to the YAML contract file.

    Returns:
        Parsed contract as a nested dictionary.

    Raises:
        FileNotFoundError: If the contract file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    # TODO: Add contract schema validation (ensure required keys exist)
    # TODO: Support contract versioning and migration
    path = Path(contract_path)
    if not path.exists():
        raise FileNotFoundError(f"Contract file not found: {contract_path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def get_expected_columns(contract: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract the list of expected column definitions from a contract.

    Args:
        contract: Parsed contract dictionary.

    Returns:
        List of column spec dicts from the contract schema.
    """
    # TODO: Add validation that schema.columns key exists
    return contract.get("schema", {}).get("columns", [])


def get_quality_thresholds(contract: dict[str, Any]) -> dict[str, Any]:
    """Extract quality thresholds from a contract.

    Args:
        contract: Parsed contract dictionary.

    Returns:
        Dictionary of quality thresholds.
    """
    # TODO: Add default thresholds if not specified in contract
    return contract.get("quality", {})
