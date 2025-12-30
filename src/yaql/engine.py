import datetime
import logging
from pathlib import Path
from typing import Annotated, Any, Optional, get_args, get_origin

from pydantic import BaseModel
from sqlalchemy import JSON, Column, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, Session, SQLModel, create_engine, select

from yasl.cache import YaslRegistry
from yasl.core import load_data_files, load_schema_files
from yasl.pydantic_types import YASLBaseModel
from yasl.sql.types import AstropyQuantityType, PydanticType

# --- Helper functions ---


def _get_sql_type(annotation: Any) -> Any:
    """Determine the SQLAlchemy/SQLModel type for a given Pydantic annotation."""
    # Basic mapping
    if annotation is int or annotation is Optional[int]:
        return None  # Let SQLModel infer Integer
    if annotation is str or annotation is Optional[str]:
        return None  # Let SQLModel infer String
    if annotation is bool or annotation is Optional[bool]:
        return None  # Let SQLModel infer Boolean
    if annotation is float or annotation is Optional[float]:
        return None  # Let SQLModel infer Float
    if annotation is datetime.date or annotation is Optional[datetime.date]:
        return None  # Let SQLModel infer Date
    if annotation is datetime.time or annotation is Optional[datetime.time]:
        return None  # Let SQLModel infer Time
    if annotation is datetime.datetime or annotation is Optional[datetime.datetime]:
        return None  # Let SQLModel infer DateTime

    # Check for Astropy Quantity
    # Note: We'd need a robust way to detect this.
    # For now, if the type name is in our known physical types map, we might handle it.
    # But since we are inspecting the *python type* (annotation), we check class name or module.
    type_name = getattr(annotation, "__name__", str(annotation))
    if "Quantity" in type_name or "astropy" in str(annotation):
        return Column(AstropyQuantityType)

    # Complex types (lists, dicts, nested models) -> JSON storage
    # This is a simplification. Ideally, relationships should be used for nested models.
    # But given the dynamic nature of YASL->SQL mapping requested:
    return (
        Column(PydanticType(annotation))
        if isinstance(annotation, type) and issubclass(annotation, YASLBaseModel)
        else Column(JSON)
    )


class YaqlEngine:
    def __init__(self, db_url: str = "sqlite:///:memory:"):
        self.engine = create_engine(db_url)
        self.registry = YaslRegistry()
        self.log = logging.getLogger("yaql")
        self.sql_models: dict[str, type[SQLModel]] = {}
        self._session_maker = sessionmaker(bind=self.engine)  # Standard sessionmaker

    @property
    def session(self) -> Session:
        """Returns a new SQLModel Session."""
        return Session(self.engine)

    def load_schema(self, schema_path: str) -> bool:
        """Loads YASL schema files and dynamically creates SQLModel classes."""
        try:
            # Clear previous state
            SQLModel.metadata.clear()
            self.sql_models.clear()
            self.registry.clear_caches()
            self.registry._init_registry()

            path = Path(schema_path)
            files_to_load = []

            if path.is_dir():
                for p in path.rglob("*.yasl"):
                    files_to_load.append(p)
            elif path.exists():
                files_to_load.append(path)
            else:
                self.log.error(f"Schema path not found: {schema_path}")
                return False

            if not files_to_load:
                return False

            total_success = True
            for file_path in files_to_load:
                loaded = load_schema_files(str(file_path))
                if not loaded:
                    total_success = False

            self._sync_registry_to_sqlmodel()
            return total_success
        except Exception as e:
            self.log.error(f"Failed to load schema: {e}")
            return False

    def _sync_registry_to_sqlmodel(self):
        """Converts registered Pydantic models to SQLModel classes."""

        types = self.registry.get_types()
        self.log.info(
            f"Syncing registry to SQLModel. Found {len(types)} types in registry."
        )

        # Helper to reverse lookup class -> table_name
        class_to_table = {}
        for (name, namespace), cls in types.items():
            class_to_table[cls] = self._get_table_name(name, namespace)

        for (name, namespace), pydantic_model in types.items():
            self.log.info(f"Processing type: {namespace}.{name}")
            table_name = self._get_table_name(name, namespace)

            # Dynamic creation of SQLModel class
            fields = {}
            annotations = {}

            # Primary Key
            annotations["id"] = Optional[int]
            fields["id"] = Field(default=None, primary_key=True)

            for field_name, field_info in pydantic_model.model_fields.items():
                if field_name == "yaml_line":
                    continue

                annotation = field_info.annotation

                # Unwrap Optional/Union/Annotated
                check_type = annotation
                if get_origin(annotation) is Annotated:
                    check_type = get_args(annotation)[0]

                # Unwrap Optional/Union again if it was inside Annotated or just there
                if get_origin(check_type) is not None:
                    args = get_args(check_type)
                    # Find the first non-None arg
                    for arg in args:
                        if arg is not type(None):
                            check_type = arg
                            break

                # 1. Check for ReferenceMarker (Existing logic for manual FKs)
                # ... (keep existing metadata extraction logic?) ...
                # Actually, I'll rewrite the loop to be cleaner and integrate the new logic.

                metadata = field_info.metadata
                is_ref = False
                ref_target = None

                # Check metadata for ReferenceMarker
                for meta in metadata:
                    if (
                        "ReferenceMarker" in str(type(meta))
                        or "ReferenceMarker" in type(meta).__name__
                    ):
                        is_ref = True
                        if hasattr(meta, "target"):
                            ref_target = meta.target
                        break
                    if "ref[" in repr(meta):
                        is_ref = True
                        if hasattr(meta, "target"):
                            ref_target = meta.target
                        break

                # Check Annotated args for ReferenceMarker
                if not is_ref and get_origin(annotation) is Annotated:
                    for arg in get_args(annotation):
                        if (
                            "ReferenceMarker" in str(type(arg))
                            or "ReferenceMarker" in type(arg).__name__
                        ):
                            is_ref = True
                            if hasattr(arg, "target"):
                                ref_target = arg.target
                            break
                        if "ref[" in repr(arg):
                            is_ref = True
                            if hasattr(arg, "target"):
                                ref_target = arg.target
                            break

                if is_ref and ref_target:
                    # ... Existing ReferenceMarker handling ...
                    # We can keep this block mostly as is, but cleaner.
                    # Copying the existing logic for ReferenceMarker...
                    self.log.info(f"Found reference: {field_name} -> {ref_target}")
                    target_parts = ref_target.rsplit(".", 1)
                    if len(target_parts) == 2:
                        target_type_str, target_prop = target_parts
                        target_ns = namespace
                        target_type_name = target_type_str
                        if "." in target_type_str:
                            target_ns, target_type_name = target_type_str.rsplit(".", 1)

                        target_table_name = self._get_table_name(
                            target_type_name, target_ns
                        )
                        fk_string = f"{target_table_name}.{target_prop}"

                        # Determine base type for the column
                        base_type = check_type

                        annotations[field_name] = base_type  # Keep original type hint

                        # Map base_type to SQLAlchemy type
                        from sqlalchemy import (
                            Boolean,
                            Date,
                            DateTime,
                            Float,
                            ForeignKey,
                            Integer,
                            String,
                            Time,
                        )

                        sa_type = String
                        if base_type is int:
                            sa_type = Integer
                        elif base_type is bool:
                            sa_type = Boolean
                        elif base_type is float:
                            sa_type = Float
                        elif base_type is datetime.date:
                            sa_type = Date
                        elif base_type is datetime.datetime:
                            sa_type = DateTime
                        elif base_type is datetime.time:
                            sa_type = Time

                        fields[field_name] = Field(
                            default=None,
                            sa_column=Column(sa_type, ForeignKey(fk_string)),
                        )
                        continue

                # 2. Check for Nested YASLBaseModel (New Logic)
                if isinstance(check_type, type) and issubclass(
                    check_type, YASLBaseModel
                ):
                    # It's a nested model!
                    target_table_name = class_to_table.get(check_type)
                    if target_table_name:
                        self.log.info(
                            f"Converting nested model {field_name} ({check_type.__name__}) to FK on {target_table_name}.id"
                        )

                        # Create FK field
                        fk_field_name = f"{field_name}_id"
                        fk_string = f"{target_table_name}.id"

                        from sqlalchemy import ForeignKey, Integer

                        annotations[fk_field_name] = Optional[int]
                        fields[fk_field_name] = Field(
                            default=None,
                            sa_column=Column(Integer, ForeignKey(fk_string)),
                        )

                        # We do NOT add the original field to the SQLModel class
                        # because we want to store the ID, not the JSON/Object.
                        # However, for convenience, we could add it as a Relationship, but let's stick to the prompt:
                        # "store these in the table ... and create a foreign key"
                        continue

                # 3. Fallback to standard handling
                annotations[field_name] = field_info.annotation
                sa_column = _get_sql_type(
                    field_info.annotation
                )  # This will still return JSON for lists/dicts

                # Override _get_sql_type behavior for YASLBaseModel if it slipped through?
                # _get_sql_type uses PydanticType for YASLBaseModel.
                # Since we handled YASLBaseModel above, this call shouldn't return PydanticType for them,
                # UNLESS it's a list[YASLBaseModel] or something not caught by check_type logic.

                if sa_column is not None:
                    fields[field_name] = Field(sa_column=sa_column, default=None)
                else:
                    fields[field_name] = Field(default=None)

            # Create the class dynamically
            metaclass = type(SQLModel)
            sql_model_cls = metaclass(
                name,
                (SQLModel,),
                {
                    "__tablename__": table_name,
                    "__annotations__": annotations,
                    "__module__": namespace or "default",
                    "__table_args__": {"extend_existing": True},
                    **fields,
                },
                table=True,
            )
            self.sql_models[table_name] = sql_model_cls
            self.log.info(f"Created SQLModel class for table: {table_name}")

        # Create tables
        self.log.info(f"Tables in metadata: {list(SQLModel.metadata.tables.keys())}")
        SQLModel.metadata.create_all(self.engine)

    def _get_table_name(self, name: str, namespace: str | None) -> str:
        if namespace and namespace != "default":
            return f"{namespace.replace('.', '_')}_{name}"
        return name

    def load_data(self, data_path: str) -> int:
        """Loads data from YAML files into the database."""
        try:
            path = Path(data_path)
            files = []
            if path.is_dir():
                files.extend(path.rglob("*.yaml"))
                files.extend(path.rglob("*.yml"))
            elif path.exists():
                files.append(path)

            count = 0
            with self.session as session:
                for f in files:
                    results = load_data_files(str(f))
                    if not results:
                        continue

                    for pydantic_obj in results:
                        if self._insert_object(session, pydantic_obj):
                            count += 1
                session.commit()
            return count
        except Exception as e:
            self.log.error(f"Failed to load data: {e}")
            return 0

    def _insert_object(self, session: Session, pydantic_obj: BaseModel) -> Any:
        # Find corresponding SQLModel
        # Reverse lookup in registry to find name/namespace
        cls = pydantic_obj.__class__
        found_key = None
        for key, val in self.registry.get_types().items():
            if val == cls:
                found_key = key
                break

        if not found_key:
            return None

        name, namespace = found_key
        table_name = self._get_table_name(name, namespace)
        sql_model_cls = self.sql_models.get(table_name)

        if not sql_model_cls:
            return None

        # Convert pydantic data to sqlmodel data
        data = pydantic_obj.model_dump(exclude={"yaml_line"})

        # Handle nested models recursively
        replacements = {}
        # Iterate over keys in the dumped data to find potential nested models
        for field_name in list(data.keys()):
            # Access the original attribute value to get the object, not the dict
            if not hasattr(pydantic_obj, field_name):
                continue

            value = getattr(pydantic_obj, field_name)

            if isinstance(value, BaseModel):
                # Recursive insert
                nested_sql_obj = self._insert_object(session, value)
                if nested_sql_obj:
                    session.flush()  # Ensure ID is generated
                    replacements[f"{field_name}_id"] = nested_sql_obj.id

        # Update data with IDs and remove original nested objects
        for key, val in replacements.items():
            data[key] = val
            original_key = key[:-3]  # remove _id
            if original_key in data:
                del data[original_key]

        # Instantiate and add
        try:
            sql_obj = sql_model_cls(**data)
            session.add(sql_obj)
            return sql_obj
        except Exception as e:
            self.log.error(
                f"Failed to instantiate {table_name}: {e}. Data keys: {data.keys()}"
            )
            return None

    def export_data(self, export_path: str, min_mode: bool = False) -> int:
        """
        Dumps the contents of the database into YAML files.

        Args:
            export_path: Directory where the YAML files will be written.
            min_mode: If True, writes all records of a type to a single file separated by '---'.

        Returns:
            Number of files written.
        """
        from ruamel.yaml import YAML

        from yasl.pydantic_types import YASLBaseModel

        path = Path(export_path)
        path.mkdir(parents=True, exist_ok=True)

        yaml = YAML()
        yaml.default_flow_style = False
        yaml.explicit_start = True  # Adds '---' at start of document

        # 1. Identify Nested Relations (ParentTable -> list of {col, target_table, field_name})
        nested_relations: dict[str, list[dict]] = {}
        # Also keep track of consumed IDs to avoid exporting them as roots
        consumed_ids: set[tuple[str, int]] = set()

        # Build the relations map from Registry/SQLModels
        types = self.registry.get_types()

        # We need a map of PydanticType -> TableName
        pydantic_to_table = {}
        for (name, namespace), cls in types.items():
            table_name = self._get_table_name(name, namespace)
            pydantic_to_table[cls] = table_name

        for (name, namespace), pydantic_model in types.items():
            table_name = self._get_table_name(name, namespace)

            for field_name, field_info in pydantic_model.model_fields.items():
                annotation = field_info.annotation

                # Unwrap types (similar to _sync_registry_to_sqlmodel)
                check_type = annotation
                if get_origin(annotation) is Annotated:
                    check_type = get_args(annotation)[0]

                if get_origin(check_type) is not None:
                    args = get_args(check_type)
                    for arg in args:
                        if arg is not type(None):
                            check_type = arg
                            break

                # Check if it was handled as a Nested Model FK
                # (Logic must match _sync_registry_to_sqlmodel Lines 240-266 approx)
                # But carefully: ReferenceMarkers are skipped there.

                # We need to verify if this field IS a nested model in the SQL mapping.
                # Inspecting the SQLModel class directly might be safer if possible,
                # but inspecting the Registry is easier for logic.

                # Simplified check: Is it a YASLBaseModel subclass AND NOT a reference?
                # We assume ReferenceMarkers were handled/stripped or don't match issubclass directly if wrapped.
                # But wait, check_type is the raw class.

                # We need to ensure it's NOT a reference.
                is_ref = False
                metadata = field_info.metadata
                for meta in metadata:
                    if (
                        "ReferenceMarker" in str(type(meta))
                        or "ReferenceMarker" in type(meta).__name__
                    ):
                        is_ref = True
                if not is_ref and get_origin(annotation) is Annotated:
                    for arg in get_args(annotation):
                        if (
                            "ReferenceMarker" in str(type(arg))
                            or "ReferenceMarker" in type(arg).__name__
                        ):
                            is_ref = True

                if (
                    not is_ref
                    and isinstance(check_type, type)
                    and issubclass(check_type, YASLBaseModel)
                ):
                    # This is a nested relation
                    target_table = pydantic_to_table.get(check_type)
                    if target_table:
                        if table_name not in nested_relations:
                            nested_relations[table_name] = []
                        nested_relations[table_name].append(
                            {
                                "col": f"{field_name}_id",
                                "target_table": target_table,
                                "field_name": field_name,
                            }
                        )

        # 2. Collect consumed IDs
        with self.session as session:
            for parent_table, relations in nested_relations.items():
                parent_cls = self.sql_models.get(parent_table)
                if not parent_cls:
                    continue

                # Select only the relevant FK columns
                # Construct query dynamically?
                # Simpler: fetch all objects and iterate.
                # For large DBs this is bad, but for "dump to yaml" it's probably acceptable for now.
                rows = session.exec(select(parent_cls)).all()
                for row in rows:
                    for rel in relations:
                        child_id = getattr(row, rel["col"], None)
                        if child_id is not None:
                            consumed_ids.add((rel["target_table"], child_id))

            # 3. Export
            count = 0

            # Helper to recursively serialize
            def serialize_row(row_obj, t_name):
                # Convert to dict
                data = row_obj.model_dump()

                # Remove internal fields
                if "id" in data:
                    del data["id"]
                if "yaml_line" in data:
                    del data["yaml_line"]

                # Handle Nested Relations
                if t_name in nested_relations:
                    for rel in nested_relations[t_name]:
                        fk_col = rel["col"]
                        child_id = getattr(row_obj, fk_col, None)

                        # Remove the _id field from data
                        if fk_col in data:
                            del data[fk_col]

                        if child_id is not None:
                            # Fetch child
                            c_model = self.sql_models.get(rel["target_table"])
                            if c_model:
                                c_row = session.get(c_model, child_id)
                                if c_row:
                                    child_data = serialize_row(
                                        c_row, rel["target_table"]
                                    )
                                    data[rel["field_name"]] = child_data

                # Remove None values? YASL seems to prefer skipping optional/missing.
                # Pydantic dump default usually keeps them as None.
                # Let's filter None values to be cleaner and match typical YAML style
                return {k: v for k, v in data.items() if v is not None}

            for table_name, model_cls in self.sql_models.items():
                # Determine Namespace and Type Name
                ns = model_cls.__module__
                type_name = model_cls.__name__

                ns_dir = path / (ns if ns else "default")
                ns_dir.mkdir(parents=True, exist_ok=True)

                # In min_mode, we open one file per type
                min_docs = []

                rows = session.exec(select(model_cls)).all()

                for row in rows:
                    if (table_name, getattr(row, "id")) in consumed_ids:  # noqa: B009
                        continue

                    data_dict = serialize_row(row, table_name)

                    if min_mode:
                        min_docs.append(data_dict)
                    else:
                        # Filename: {Type}_{id}.yaml
                        row_id = getattr(row, "id")  # noqa: B009
                        file_name = f"{type_name}_{row_id}.yaml"
                        file_path = ns_dir / file_name

                        with open(file_path, "w") as f:
                            yaml.dump(data_dict, f)

                        count += 1

                if min_mode and min_docs:
                    file_name = f"{type_name}.yaml"
                    file_path = ns_dir / file_name
                    with open(file_path, "w") as f:
                        yaml.dump_all(min_docs, f)
                    count += 1  # Count files, not records in min mode? Prompt says "number of files written"

            return count

    def execute_sql(self, query: str) -> list[dict] | None:
        """Execute raw SQL (fallback)."""
        with self.engine.connect() as conn:
            try:
                # Use sqlalchemy text() for proper execution of raw strings
                result = conn.execute(text(query))

                # Check if it returns rows (SELECT)
                if result.returns_rows:
                    return [dict(row._mapping) for row in result]

                # If modification query (INSERT, UPDATE, etc), commit
                conn.commit()
                return None
            except Exception as e:
                self.log.error(f"SQL Execution error: {e}")
                raise e


_yaql_engine = YaqlEngine()


def load_schema(schema_path: str) -> bool:
    """
    Load YASL schema definitions into the global YAQL engine.

    Args:
        schema_path: Path to a .yasl file or a directory containing .yasl files.

    Returns:
        True if all schemas were loaded successfully, False otherwise.
    """
    return _yaql_engine.load_schema(schema_path)


def load_data(data_path: str) -> int:
    """
    Load YAML data files into the global YAQL engine.

    Args:
        data_path: Path to a .yaml/.yml file or a directory containing such files.

    Returns:
        The number of data records successfully loaded.
    """
    return _yaql_engine.load_data(data_path)


def export_data(export_path: str, min_mode: bool = False) -> int:
    """
    Exports the data from the global YAQL engine to YAML files.

    Args:
        export_path: Directory where the YAML files will be written.
        min_mode: If True, writes all records of a type to a single file separated by '---'.

    Returns:
        Number of files written.
    """
    return _yaql_engine.export_data(export_path, min_mode=min_mode)


def get_session() -> Session:
    """
    Get a new SQLModel Session bound to the global YAQL engine.

    Returns:
        A new Session object for interacting with the database.
    """
    return _yaql_engine.session
