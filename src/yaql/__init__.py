"""
YAQL - YAML Advanced Query Language

YAQL provides a standard SQL query interface for YAML data.
YAQL dynamically loads YAML data into an in-memory SQLite database, allowing users to execute SQL queries against the data.
YAQL generated database schemas are derived from YASL schema definitions, ensuring data integrity and consistency.
"""

from .cli import main
from .engine import YaqlEngine

__all__ = ["main", "YaqlEngine"]
