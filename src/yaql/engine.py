import json
import logging
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional, cast

from pydantic import BaseModel
from ruamel.yaml import YAML

from yasl.cache import YaslRegistry
from yasl.core import load_data_files, load_schema_files


# Helper to adapt python date/datetime types to sqlite TEXT
def adapt_date_iso(val):
    return val.isoformat()


def adapt_datetime_iso(val):
    return val.isoformat()


sqlite3.register_adapter(date, adapt_date_iso)
sqlite3.register_adapter(datetime, adapt_datetime_iso)


class YaqlEngine:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self.cursor = self.conn.cursor()
        self.registry = YaslRegistry()
        self.unsaved_changes = False
        self.log = logging.getLogger("yaql")

        # Keep track of which tables map to which YASL types for export
        # key: table_name, value: (type_name, namespace)
        self.table_map: dict[str, tuple[str, str | None]] = {}

    def load_schema(self, schema_path: str) -> bool:
        """Loads YASL schema files and creates corresponding SQLite tables."""
        try:
            path = Path(schema_path)
            files_to_load = []

            if path.is_dir():
                # Find all .yasl files
                for p in path.rglob("*.yasl"):
                    files_to_load.append(p)
            elif path.exists():
                files_to_load.append(path)
            else:
                self.log.error(f"Schema path not found: {schema_path}")
                return False

            if not files_to_load:
                self.log.error(f"No schema files found in {schema_path}")
                return False

            total_success = True
            for file_path in files_to_load:
                # Use str(file_path) because load_schema_files expects a string
                loaded_schemas = load_schema_files(str(file_path))
                if not loaded_schemas:
                    self.log.error(f"Failed to load schema file: {file_path}")
                    total_success = False
                    continue  # Try loading others

            self._sync_db_with_registry()
            return total_success
        except Exception as e:
            self.log.error(f"Failed to load schema: {e}")
            return False

    def _sync_db_with_registry(self):
        """Iterates through the YASL registry and creates tables for new types."""
        types = self.registry.get_types()
        for (name, namespace), model_cls in types.items():
            # Cast model_cls to Type[BaseModel] as it returns the class itself
            cls = cast(type[BaseModel], model_cls)
            table_name = self._get_table_name(name, namespace)
            if not self._table_exists(table_name):
                self._create_table(table_name, cls)
                self.table_map[table_name] = (name, namespace)

    def _get_table_name(self, name: str, namespace: str | None) -> str:
        if namespace and namespace != "default":
            # Sanitize namespace for SQL
            sanitized_ns = namespace.replace(".", "_")
            return f"{sanitized_ns}_{name}"
        return name

    def _table_exists(self, table_name: str) -> bool:
        res = self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
            (table_name,),
        )
        return res.fetchone() is not None

    def _create_table(self, table_name: str, model_cls: type[BaseModel]):
        columns = []
        for field_name, field_info in model_cls.model_fields.items():
            if field_name == "yaml_line":
                continue

            # Determine SQL type based on annotation
            sql_type = "TEXT"
            annotation = field_info.annotation

            if annotation is int or annotation is Optional[int]:
                sql_type = "INTEGER"
            elif annotation is float or annotation is Optional[float]:
                sql_type = "REAL"
            elif annotation is bool or annotation is Optional[bool]:
                sql_type = "BOOLEAN"

            columns.append(f'"{field_name}" {sql_type}')

        create_stmt = f'CREATE TABLE "{table_name}" ({", ".join(columns)});'
        self.log.debug(f"Creating table: {create_stmt}")
        self.cursor.execute(create_stmt)
        self.conn.commit()

    def load_data(self, data_path: str) -> int:
        """Loads data from YAML files into the database."""
        try:
            path = Path(data_path)
            files_to_load = []

            if path.is_dir():
                for p in path.rglob("*.yaml"):
                    files_to_load.append(p)
                for p in path.rglob("*.yml"):
                    files_to_load.append(p)
            elif path.exists():
                files_to_load.append(path)
            else:
                self.log.error(f"Data path not found: {data_path}")
                return 0

            total_count = 0
            for file_path in files_to_load:
                results = load_data_files(str(file_path))
                if not results:
                    continue

                for model_instance in results:
                    if self._insert_model(model_instance):
                        total_count += 1

            if total_count > 0:
                self.unsaved_changes = True
            return total_count
        except Exception as e:
            self.log.error(f"Failed to load data: {e}")
            return 0

    def _insert_model(self, model_instance: BaseModel) -> bool:
        cls = model_instance.__class__
        # Finding the registry key for this class
        found_key = None
        for key, val in self.registry.get_types().items():
            if val == cls:
                found_key = key
                break

        if not found_key:
            self.log.error(f"Could not find registered type for model {cls}")
            return False

        name, namespace = found_key
        table_name = self._get_table_name(name, namespace)

        # Verify table exists (in case schema wasn't loaded first or properly)
        if not self._table_exists(table_name):
            self.log.error(f"Table '{table_name}' does not exist for model {name}")
            return False

        data = model_instance.model_dump()
        if "yaml_line" in data:
            del data["yaml_line"]

        columns = list(data.keys())
        placeholders = ["?"] * len(columns)
        values = []
        for v in data.values():
            if isinstance(v, (dict, list, BaseModel)):
                values.append(json.dumps(v, default=str))
            else:
                values.append(v)

        try:
            sql = f'INSERT INTO "{table_name}" ({", ".join(f"{c}" for c in columns)}) VALUES ({", ".join(placeholders)})'
            self.cursor.execute(sql, values)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.log.error(f"Failed to insert row: {e}")
            return False

    def execute_sql(self, query: str) -> Optional[list[dict]]:
        try:
            # Check if it's a modification query to set unsaved_changes
            lower_query = query.strip().lower()
            if any(
                lower_query.startswith(x)
                for x in ["insert", "update", "delete", "create", "drop", "alter"]
            ):
                self.unsaved_changes = True

            cursor = self.cursor.execute(query)
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                results = [
                    dict(zip(columns, row, strict=False)) for row in cursor.fetchall()
                ]
                return results
            else:
                self.conn.commit()
                return None
        except sqlite3.Error as e:
            self.log.error(f"SQL Error: {e}")
            raise

    def store_schema(self, output_path: str) -> bool:
        """Exports the current schema definitions to a YASL file."""
        try:
            schema_yaml = self.registry.export_schema()
            with open(output_path, "w") as f:
                f.write(schema_yaml)
            return True
        except Exception as e:
            self.log.error(f"Failed to store schema: {e}")
            return False

    def store_data(self, output_path: str):
        path = Path(output_path)
        yaml = YAML()
        yaml.default_flow_style = False

        data_to_dump = []

        # Dump all known tables
        for table_name in self.table_map:
            # Select all data
            rows = self.execute_sql(f'SELECT * FROM "{table_name}"')
            if not rows:
                continue

            # Convert back to native types (undoing JSON serialization)
            type_name, namespace = self.table_map[table_name]
            model_cls = self.registry.get_type(type_name, namespace)

            if not model_cls:
                continue

            # Need to cast to class to access model_fields
            cls = cast(type[BaseModel], model_cls)

            for row in rows:
                clean_row = {}
                for k, v in row.items():
                    if k not in cls.model_fields:
                        continue

                    field = cls.model_fields[k]

                    if isinstance(v, str):
                        try:
                            # Check schema type roughly
                            annotation = field.annotation
                            if not (annotation is str or annotation is Optional[str]):
                                clean_row[k] = json.loads(v)
                            else:
                                clean_row[k] = v
                        except (json.JSONDecodeError, TypeError):
                            clean_row[k] = v
                    else:
                        clean_row[k] = v

                data_to_dump.append(clean_row)

        if path.suffix in [".yaml", ".yml"]:
            with open(path, "w") as f:
                yaml.dump(data_to_dump, f)
        else:
            path.mkdir(parents=True, exist_ok=True)
            with open(path / "export.yaml", "w") as f:
                yaml.dump(data_to_dump, f)

        self.unsaved_changes = False

    def close(self):
        self.conn.close()
