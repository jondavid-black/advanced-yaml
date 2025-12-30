"""
YAQL - YAML Advanced Query Language

YAQL provides a standard SQL query interface for YAML data.
YAQL dynamically loads YAML data into an in-memory SQLite database, allowing users to execute SQL queries against the data.
YAQL generated database schemas are derived from YASL schema definitions, ensuring data integrity and consistency.
"""

from yaql.cli import main
from yaql.engine import export_data, get_session, load_data, load_schema

__all__ = ["main", "get_session", "load_schema", "load_data", "export_data"]
