# validate_config_with_lines.py
import json
import logging
import os
import sys
import tomllib
import traceback
from collections.abc import Callable
from enum import Enum
from io import StringIO
from pathlib import Path
from typing import Annotated, Any, Optional, TextIO, cast, get_args, get_origin

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    create_model,
)
from ruamel.yaml import YAML, YAMLError

from yasl.cache import YaslRegistry
from yasl.primitives import PRIMITIVE_TYPE_MAP, ReferenceMarker
from yasl.pydantic_types import Enumeration, TypeDef, YASLBaseModel, YaslRoot
from yasl.validators import property_validator_factory, type_validator_factory


# --- Logging Setup ---
class YamlFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        yaml = YAML()
        log_dict = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        stream = StringIO()
        log_list = []
        log_list.append(log_dict)
        yaml.dump(log_list, stream)
        return stream.getvalue().strip()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_dict = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        return json.dumps(log_dict)


def _setup_logging(
    disable: bool,
    verbose: bool,
    quiet: bool,
    output: str,
    stream: StringIO | TextIO = sys.stdout,
):
    logger = logging.getLogger()
    logger.handlers.clear()
    if disable:
        logger.disabled = True
        return
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    else:
        level = logging.INFO
    logger.setLevel(level)
    handler = logging.StreamHandler(stream)
    if output == "json":
        handler.setFormatter(JsonFormatter())
    elif output == "yaml":
        handler.setFormatter(YamlFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


# --- YASL Models and Validation Logic ---


def yasl_version() -> str:
    """
    Get the version of the YASL package.

    Returns:
        str: The version string defined in pyproject.toml, or an error message if the file cannot be read.
    """
    try:
        pyproject_path = os.path.join(os.path.dirname(__file__), "../../pyproject.toml")
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
        return pyproject["project"]["version"]
    except Exception:
        # fallback to old version if pyproject.toml is missing or malformed
        return "Unknown due to internal error reading pyproject.toml"


def yasl_eval(
    yasl_schema: str,
    yaml_data: str,
    model_name: str | None = None,
    disable_log: bool = False,
    quiet_log: bool = False,
    verbose_log: bool = False,
    output: str = "text",
    log_stream: StringIO | TextIO = sys.stdout,
) -> list[BaseModel] | None:
    """
    Evaluate YAML data against a YASL schema.

    Args:
        yasl_schema (str): Path to the YASL schema file or directory.
        yaml_data (str): Path to the YAML data file or directory.
        model_name (str, optional): Specific model name to use for validation. If not provided, the model will be auto-detected.
        disable_log (bool): If True, disables all logging output.
        quiet_log (bool): If True, suppresses all output except for errors.
        verbose_log (bool): If True, enables verbose logging output.
        output (str): Output format for logs. Options are 'text', 'json', or 'yaml'. Default is 'text'.
        log_stream (StringIO): Stream to which logs will be written. Default is sys.stdout.

    Returns:
        Optional[List[BaseModel]]: List of validated Pydantic models if validation is successful, None otherwise.
    """

    _setup_logging(
        disable=disable_log,
        verbose=verbose_log,
        quiet=quiet_log,
        output=output,
        stream=log_stream,
    )
    log = logging.getLogger("yasl")
    log.debug(f"YASL Version - {yasl_version()}")
    log.debug(f"YASL Schema - {yasl_schema}")
    log.debug(f"YAML Data - {yaml_data}")

    registry = YaslRegistry()

    yasl_files = []
    if Path(yasl_schema).is_dir():
        for p in Path(yasl_schema).rglob("*.yasl"):
            yasl_files.append(p)
        if not yasl_files:
            log.error(f"❌ No .yasl files found in directory '{yasl_schema}'")
            registry.clear_caches()
            return None
        log.debug(f"Found {len(yasl_files)} .yasl files in directory '{yasl_schema}'")
    else:
        if not Path(yasl_schema).exists():
            log.error(f"❌ YASL schema file '{yasl_schema}' not found")
            registry.clear_caches()
            return None
        yasl_files.append(Path(yasl_schema))

    yaml_files = []
    if Path(yaml_data).is_dir():
        for p in Path(yaml_data).rglob("*.yaml"):
            yaml_files.append(p)
        if not yaml_files:
            log.error(f"❌ No .yaml files found in directory '{yaml_data}'")
            registry.clear_caches()
            return None
        log.debug(f"Found {len(yaml_files)} .yaml files in directory '{yaml_data}'")
    else:
        if not Path(yaml_data).exists():
            log.error(f"❌ YAML data file '{yaml_data}' not found")
            registry.clear_caches()
            return None
        yaml_files.append(Path(yaml_data))

    yasl_results = []
    for yasl_file in yasl_files:
        yasl = load_schema_files(str(yasl_file))
        if yasl is None:
            log.error("❌ YASL schema validation failed. Exiting.")
            registry.clear_caches()
            return None
        yasl_results.extend(yasl)

    results = []

    for yaml_file in yaml_files:
        results = load_data_files(str(yaml_file), model_name)

        if not results or len(results) == 0:
            log.error(
                f"❌ Validation failed. Unable to validate data in YAML file {yaml_file}."
            )
            registry.clear_caches()
            return None

    registry.clear_caches()
    return results


def check_schema(
    yasl_schema: str,
    disable_log: bool = False,
    quiet_log: bool = False,
    verbose_log: bool = False,
    output: str = "text",
    log_stream: StringIO | TextIO = sys.stdout,
) -> bool:
    """
    Check the validity of a YASL schema file or directory.

    Args:
        yasl_schema (str): Path to the YASL schema file or directory.
        disable_log (bool): If True, disables all logging output.
        quiet_log (bool): If True, suppresses all output except for errors.
        verbose_log (bool): If True, enables verbose logging output.
        output (str): Output format for logs. Options are 'text', 'json', or 'yaml'. Default is 'text'.
        log_stream (StringIO): Stream to which logs will be written. Default is sys.stdout.

    Returns:
        bool: True if the schema is valid, False otherwise.
    """
    _setup_logging(
        disable=disable_log,
        verbose=verbose_log,
        quiet=quiet_log,
        output=output,
        stream=log_stream,
    )
    log = logging.getLogger("yasl")
    log.debug(f"YASL Version - {yasl_version()}")
    log.debug(f"Checking YASL Schema - {yasl_schema}")

    registry = YaslRegistry()
    registry.clear_caches()

    yasl_files = []
    if Path(yasl_schema).is_dir():
        for p in Path(yasl_schema).rglob("*.yasl"):
            yasl_files.append(p)
        if not yasl_files:
            log.error(f"❌ No .yasl files found in directory '{yasl_schema}'")
            return False
        log.debug(f"Found {len(yasl_files)} .yasl files in directory '{yasl_schema}'")
    else:
        if not Path(yasl_schema).exists():
            log.error(f"❌ YASL schema file '{yasl_schema}' not found")
            return False
        yasl_files.append(Path(yasl_schema))

    all_valid = True
    for yasl_file in yasl_files:
        yasl = load_schema_files(str(yasl_file))
        if yasl is None:
            log.error(f"❌ YASL schema validation failed for '{yasl_file}'.")
            all_valid = False
        else:
            log.info(f"✅ YASL schema '{yasl_file}' is valid.")

    registry.clear_caches()
    return all_valid


def gen_enum_from_enumerations(namespace: str, enum_defs: dict[str, Enumeration]):
    """
    Dynamically generate a Python Enum class from an Enumeration instance.
    Each value in the Enumeration becomes a member of the Enum.
    """
    registry = YaslRegistry()
    for enum_name, enum_def in enum_defs.items():
        if registry.get_enum(enum_name, namespace) is not None:
            # We skip if it already exists to handle diamond dependencies gracefully
            return

        enum_members = {value: value for value in enum_def.values}
        enum_cls = Enum(enum_name, enum_members)
        enum_cls.__module__ = namespace
        registry.register_enum(enum_name, enum_cls, namespace)


class _DeferTypeGeneration(Exception):
    pass


def _resolve_ref_type(
    namespace: str,
    all_type_defs: dict[tuple[str, str], TypeDef],
    prop_name: str,
    typedef_name: str,
    type_lookup: str,
    type_map: dict[str, Any],
) -> Any:
    ref_target = type_lookup[4:-1]

    if "." not in ref_target:
        raise ValueError(
            f"Reference '{ref_target}' for property '{prop_name}' must be in the format TypeName.PropertyName or Namespace.TypeName.PropertyName"
        )

    ref_type_name, property_name = ref_target.rsplit(".", 1)
    ref_type_namespace = None
    if "." in ref_type_name:
        ref_type_namespace, ref_type_name = ref_type_name.rsplit(".", 1)

    # Lookup target definition
    target_def = None
    target_key = (ref_type_namespace or namespace, ref_type_name)
    if target_key in all_type_defs:
        target_def = all_type_defs[target_key]

    if not target_def:
        # Check registry for imported/already registered types
        registry = YaslRegistry()
        target_model = registry.get_type(ref_type_name, ref_type_namespace, namespace)
        if target_model:
            # Find the field in the pydantic model
            if property_name not in target_model.model_fields:
                raise ValueError(
                    f"Referenced property '{property_name}' in type '{ref_type_name}' not found for property '{prop_name}'"
                )

            field_info = target_model.model_fields[property_name]

            # Check for uniqueness in json_schema_extra
            is_unique = False
            if field_info.json_schema_extra and isinstance(
                field_info.json_schema_extra, dict
            ):
                is_unique = field_info.json_schema_extra.get("unique", False)

            if not is_unique:
                raise ValueError(
                    f"Referenced property '{ref_type_name}.{property_name}' must be unique to be used as a reference for property '{typedef_name}.{prop_name}'"
                )

            def get_underlying_type(t):
                if get_origin(t) is Annotated:
                    return get_underlying_type(get_args(t)[0])
                return t

            base_type = get_underlying_type(field_info.annotation)
            return Annotated[base_type, ReferenceMarker(ref_target)]

    if target_def:
        if property_name not in target_def.properties:
            raise ValueError(
                f"Referenced property '{property_name}' in type '{ref_type_name}' not found for property '{prop_name}'"
            )
        target_prop = target_def.properties[property_name]

        if not target_prop.unique:
            raise ValueError(
                f"Referenced property '{ref_type_name}.{property_name}' must be unique to be used as a reference for property '{typedef_name}.{prop_name}'"
            )

        if target_prop.type not in type_map:
            raise ValueError(
                f"Referenced property '{ref_type_name}.{property_name}' must be a primitive type to be used as a reference for property '{typedef_name}.{prop_name}'"
            )

        base_type = type_map[target_prop.type]
        return Annotated[base_type, ReferenceMarker(ref_target)]

    else:
        raise ValueError(
            f"Referenced type '{ref_type_name}' for property '{prop_name}' not found in type definitions"
        )


def _resolve_map_type(
    namespace: str,
    all_type_defs: dict[tuple[str, str], TypeDef],
    registry: YaslRegistry,
    prop_name: str,
    type_lookup: str,
    type_map: dict[str, Any],
) -> Any:
    key_str, value_str = type_lookup[4:-1].split(",", 1)

    # Process Key
    key_type_lookup = key_str.strip()
    key_type_lookup_ns = None
    if "." in key_type_lookup:
        key_type_lookup_ns, key_type_lookup = key_type_lookup.rsplit(".", 1)

    if key_str in ["str", "string"]:
        key = str
    elif key_str == "int":
        key = int
    else:
        # Check enum
        enum_type = registry.get_enum(key_type_lookup, key_type_lookup_ns, namespace)
        if enum_type:
            key = enum_type
        else:
            acceptable_keys = ["str", "string", "int"] + [
                f"{ns}.{n}" if ns else n for n, ns in registry.get_enums()
            ]
            raise ValueError(
                f"Map key type '{key_str}' for property '{prop_name}' must be one of {acceptable_keys}."
            )

    # Process Value
    value_type_lookup = value_str.strip()
    value_type_lookup_ns = None
    map_value_is_list = False

    if value_type_lookup.endswith("[]"):
        value_type_lookup = value_type_lookup[:-2]
        map_value_is_list = True

    if "." in value_type_lookup:
        value_type_lookup_ns, value_type_lookup = value_type_lookup.rsplit(".", 1)

    py_type = None
    if value_type_lookup in type_map:
        py_type = type_map[value_type_lookup]
    elif registry.get_enum(value_type_lookup, value_type_lookup_ns, namespace):
        py_type = registry.get_enum(value_type_lookup, value_type_lookup_ns, namespace)
    elif registry.get_type(value_type_lookup, value_type_lookup_ns, namespace):
        py_type = registry.get_type(value_type_lookup, value_type_lookup_ns, namespace)
    else:
        # Check if pending in all_type_defs
        target_key = (value_type_lookup_ns or namespace, value_type_lookup)
        if target_key in all_type_defs:
            raise _DeferTypeGeneration()

        raise ValueError(
            f"Unknown map value type '{value_type_lookup}' for property '{prop_name}'"
        )

    if map_value_is_list:
        py_type = list[py_type]

    return dict[key, py_type]


def _resolve_simple_type(
    namespace: str,
    all_type_defs: dict[tuple[str, str], TypeDef],
    registry: YaslRegistry,
    prop_name: str,
    type_lookup: str,
    type_lookup_namespace: str | None,
    type_map: dict[str, Any],
) -> Any:
    if type_lookup in type_map:
        return type_map[type_lookup]
    elif registry.get_enum(type_lookup, type_lookup_namespace, namespace):
        return registry.get_enum(type_lookup, type_lookup_namespace, namespace)
    elif registry.get_type(type_lookup, type_lookup_namespace, namespace):
        return registry.get_type(type_lookup, type_lookup_namespace, namespace)
    else:
        # Check if pending in all_type_defs
        target_key = (type_lookup_namespace or namespace, type_lookup)
        if target_key in all_type_defs:
            raise _DeferTypeGeneration()

        raise ValueError(f"Unknown type '{type_lookup}' for property '{prop_name}'")


def gen_pydantic_type_models(all_type_defs: dict[tuple[str, str], TypeDef]):
    """
    Dynamically generate Pydantic model classes from a list of TypeDef instances.
    Each property in the TypeDef becomes a field in the generated model.
    """
    registry = YaslRegistry()

    # Queue of types to process
    pending_types = list(all_type_defs.items())

    while pending_types:
        progress = False
        retry_queue = []

        for (namespace, typedef_name), type_def in pending_types:
            # Skip if already registered (e.g. from a previous pass or run)
            if registry.get_type(typedef_name, namespace) is not None:
                progress = True
                continue

            try:
                fields: dict[str, Any] = {}
                validators: dict[str, Callable] = {}

                for prop_name, prop in type_def.properties.items():
                    type_map = PRIMITIVE_TYPE_MAP
                    type_lookup = prop.type
                    type_lookup_namespace = None
                    is_list = False
                    is_ref = False
                    is_map = False
                    py_type = None

                    if type_lookup.endswith("[]"):
                        type_lookup = prop.type[:-2]
                        is_list = True

                    # Check for namespace or ref/map indicators
                    if (
                        "ref[" not in type_lookup
                        and "map[" not in type_lookup
                        and "." in type_lookup
                    ):
                        parts = type_lookup.split(".")
                        type_lookup = parts[-1]
                        type_lookup_namespace = ".".join(parts[:-1])

                    if type_lookup.startswith("ref[") and type_lookup.endswith("]"):
                        is_ref = True

                    if type_lookup.startswith("map[") and type_lookup.endswith("]"):
                        is_map = True

                    # --- RESOLVE TYPE ---

                    if is_ref:
                        py_type = _resolve_ref_type(
                            namespace,
                            all_type_defs,
                            prop_name,
                            typedef_name,
                            type_lookup,
                            type_map,
                        )

                    elif is_map:
                        py_type = _resolve_map_type(
                            namespace,
                            all_type_defs,
                            registry,
                            prop_name,
                            type_lookup,
                            type_map,
                        )

                    else:
                        py_type = _resolve_simple_type(
                            namespace,
                            all_type_defs,
                            registry,
                            prop_name,
                            type_lookup,
                            type_lookup_namespace,
                            type_map,
                        )

                    if is_list and not is_map:  # map handled list internally
                        py_type = list[py_type]

                    # --- FIELD CONSTRUCTION ---
                    is_required = prop.presence == "required"
                    # Default handling logic...
                    if not is_required:
                        py_type = Optional[py_type]

                    default_val = (
                        prop.default
                        if prop.default is not None
                        else (None if not is_required else ...)
                    )

                    # Fix for type checker: cast explicitly to dict[str, Any] or equivalent
                    field_extra: dict[str, Any] = {"unique": prop.unique}

                    fields[prop_name] = (
                        py_type,
                        Field(default=default_val, json_schema_extra=field_extra),  # type: ignore
                    )

                    validators[f"{prop_name}__validator"] = property_validator_factory(
                        typedef_name, namespace, type_def, prop_name, prop
                    )

                # --- MODEL CREATION ---
                fields["yaml_line"] = (Optional[int], Field(default=None, exclude=True))
                validators["__validate__"] = type_validator_factory(type_def)

                model = create_model(  # type: ignore
                    typedef_name,
                    __base__=YASLBaseModel,
                    __module__=namespace,
                    __validators__=validators,
                    __config__={"extra": "forbid"},
                    **fields,  # type: ignore
                )
                registry.register_type(typedef_name, model, namespace)
                progress = True

            except _DeferTypeGeneration:
                retry_queue.append(((namespace, typedef_name), type_def))

        if not progress and retry_queue:
            # We are stuck.
            names = [n for (_, n), _ in retry_queue]
            raise ValueError(
                f"Unable to resolve dependencies for types: {names}. Circular dependency or missing dependency."
            )

        pending_types = retry_queue


# --- Helper function to find the line number ---
def _get_line_for_error(data: Any, loc: tuple[str | int, ...]) -> int | None:
    """Traverse the ruamel.yaml data to find the line number for an error location."""
    current_data = data
    try:
        for key in loc:
            current_data = current_data[key]
        # .lc is the line/column accessor in ruamel.yaml
        return current_data.lc.line + 1
    except (KeyError, IndexError, AttributeError):
        # Fallback if we can't find the exact key (e.g., for a missing key)
        # We can try to get the line of the parent object.
        parent_data = data
        for key in loc[:-1]:
            parent_data = parent_data[key]
        try:
            return parent_data.lc.line + 1
        except AttributeError:
            return None


def load_schema(data: dict[str, Any]) -> YaslRoot:
    """
    Load and validate a YASL schema from a dictionary and add the generated types to the registry.

    This function parses a raw dictionary into a YaslRoot object, generating
    any defined enumerations and Pydantic models in the process. Note that
    schema imports are NOT supported when loading directly from a dictionary;
    use `load_schema_files` if import resolution is required.

    Args:
        data (dict[str, Any]): The raw dictionary containing the YASL schema definition.

    Returns:
        YaslRoot: The validated and parsed YASL root object.

    Raises:
        ValueError: If the schema defines imports (which are not supported in this mode),
            or if type generation fails (e.g. duplicate definitions, invalid references).
        ValidationError: If the input data does not match the expected YASL structure.
    """
    log = logging.getLogger("yasl")
    yasl = YaslRoot(**data)
    if yasl is None:
        raise ValueError("Failed to parse YASL schema from data {data}")
    if yasl.imports is not None:
        log.error(
            "Imports are not supported by the 'load_schema' function.  Use 'load_schema_files' instead."
        )
        raise ValueError(
            "YASL import not supported when processing from data dictionary."
        )
    if yasl.metadata is not None:
        log.debug(f"YASL Metadata: {yasl.metadata}")

    # Phase 1: Enums
    if yasl.definitions is not None:
        for namespace, yasl_item in yasl.definitions.items():
            if yasl_item.enums is not None:
                gen_enum_from_enumerations(namespace, yasl_item.enums)

    # Phase 2: Collect Types
    all_types: dict[tuple[str, str], TypeDef] = {}
    if yasl.definitions is not None:
        for namespace, yasl_item in yasl.definitions.items():
            if yasl_item.types is not None:
                for name, type_def in yasl_item.types.items():
                    all_types[(namespace, name)] = type_def

    # Phase 3: Generate Types
    if all_types:
        gen_pydantic_type_models(all_types)

    return yasl


def _inject_line_numbers(data: Any, model: BaseModel):
    """
    Recursively inject line numbers into Pydantic models from ruamel.yaml data.
    """
    # model.yaml_line is already defined in YASLBaseModel as Optional[int]
    # but pyright might complain if it doesn't know 'model' is YASLBaseModel.
    # We check isinstance above but pyright might need help.
    if isinstance(model, YASLBaseModel):
        if hasattr(data, "lc") and hasattr(data.lc, "line"):
            model.yaml_line = data.lc.line + 1

    if isinstance(model, BaseModel):
        for field_name in type(model).model_fields:
            if field_name in data and isinstance(data[field_name], dict):
                # Try to get the child model
                child_val = getattr(model, field_name)
                if isinstance(child_val, BaseModel):
                    _inject_line_numbers(data[field_name], child_val)
                elif isinstance(child_val, dict):
                    # For dicts of models (like properties: dict[str, Property])
                    for k, v in child_val.items():
                        if isinstance(v, BaseModel) and k in data[field_name]:
                            _inject_line_numbers(data[field_name][k], v)


def _parse_schema_files_recursive(
    path: str, log: logging.Logger, visited_paths: set[str] | None = None
) -> list[YaslRoot] | None:
    if visited_paths is None:
        visited_paths = set()

    abs_path = os.path.abspath(path)
    if abs_path in visited_paths:
        log.debug(f"Skipping already loaded schema: {path}")
        return []
    visited_paths.add(abs_path)

    log.debug(f"--- Attempting to load schema '{path}' ---")

    data = None
    try:
        results = []
        yaml_loader = YAML(typ="rt")
        docs = []
        with open(path) as f:
            docs.extend(yaml_loader.load_all(f))

        for data in docs:
            yasl = YaslRoot(**data)
            _inject_line_numbers(data, yasl)

            if yasl is None:
                raise ValueError("Failed to parse YASL schema from data {data}")

            # Recurse for imports
            if yasl.imports is not None:
                for imp in yasl.imports:
                    imp_path = imp
                    if not Path(imp_path).exists():
                        # try relative to current schema file
                        imp_path = Path(path).parent / imp
                        if not imp_path.exists():
                            raise FileNotFoundError(f"Import file '{imp}' not found")
                        imp_path = imp_path.as_posix()

                    log.debug(
                        f"Importing additional schema '{imp}' - resolved to '{imp_path}'"
                    )

                    imported_roots = _parse_schema_files_recursive(
                        str(imp_path), log, visited_paths
                    )
                    if imported_roots is None:  # Propagate failure
                        return None
                    results.extend(imported_roots)

            if yasl.metadata is not None:
                log.debug(f"YASL Metadata: {yasl.metadata}")

            results.append(yasl)

        if not results:
            log.error(f"❌ No YASL schema definitions found in '{path}'")
            return None

        return results

    except FileNotFoundError:
        log.error(f"❌ Error - YASL schema file not found at '{path}'")
        return None
    except SyntaxError as e:
        log.error(f"❌ Error - Syntax error in YASL schema file '{path}'\n  - {e}")
        return None
    except YAMLError as e:
        log.error(f"❌ Error - YAML error while parsing YASL schema '{path}'\n  - {e}")
        return None
    except ValidationError as e:
        log.error(
            f"❌ YASL schema validation of {path} failed with {len(e.errors())} error(s):"
        )
        for error in e.errors():
            line = _get_line_for_error(data, error["loc"])
            path_str = " -> ".join(map(str, error["loc"]))
            if line:
                log.error(f"  - Line {line}: '{path_str}' -> {error['msg']}")
            else:
                log.error(f"  - Location '{path_str}' -> {error['msg']}")
        return None
    except Exception as e:
        log.error(f"❌ An schema error occurred processing '{path}' - {type(e)} - {e}")
        traceback.print_exc()
        return None


# --- Main schema validation logic ---
def load_schema_files(path: str) -> list[YaslRoot] | None:
    """
    Load and validate YASL schema(s) from a file.

    This function reads a YAML file containing one or more YASL schema definitions.
    It recursively resolves any imports specified in the schemas.
    For each valid schema, it generates the corresponding Python Enums and Pydantic models
    and registers them in the YaslRegistry.

    Args:
        path (str): The file path to the YASL schema file.

    Returns:
        list[YaslRoot] | None: A list of validated YaslRoot objects if successful,
        or None if validation fails or the file cannot be read.

    Note:
        The function catches most exceptions (FileNotFoundError, YAMLError, ValidationError)
        and logs them as errors, returning None.
    """
    log = logging.getLogger("yasl")

    # 1. Load all roots recursively
    roots = _parse_schema_files_recursive(path, log)
    if roots is None:
        return None

    # 2. Generate Enums (Pass 1)
    for root in roots:
        if root.definitions:
            for namespace, defs in root.definitions.items():
                if defs.enums:
                    gen_enum_from_enumerations(namespace, defs.enums)

    # 3. Collect Types (Pass 2)
    all_types: dict[tuple[str, str], TypeDef] = {}
    for root in roots:
        if root.definitions:
            for namespace, defs in root.definitions.items():
                if defs.types:
                    for name, typedef in defs.types.items():
                        all_types[(namespace, name)] = typedef

    # 4. Generate Types (Pass 3 - Multi-pass within generator)
    if all_types:
        try:
            gen_pydantic_type_models(all_types)
        except ValueError as e:
            # Try to enrich the error message if possible, though we don't have direct access
            # to the YaslRoot objects easily here in the exception handler without iterating again.
            # However, the user asked to see *where* we output the error message and include the line.
            # The error 'e' comes from gen_pydantic_type_models or its helpers.

            # To get line numbers, we need to find which definition caused the error.
            # The ValueError message often contains the type/property name (e.g. "Unknown type 'foo' for property 'bar'").
            # We can search the 'roots' to find that definition and get its line number.

            error_msg = str(e)

            # Simple heuristic: try to find the property or type name in the error message
            # and locate it in the loaded roots.
            found_line = None

            # We iterate through roots to find the problematic definition if we can match the error message content.
            # This is a best-effort attempt to provide better context.
            if roots:
                for root in roots:
                    # This requires the YaslRoot to have line info attached, which Pydantic models usually don't have by default unless we add it.
                    # But wait! We parsed using ruamel.yaml earlier, and YaslRoot is a Pydantic model.
                    # If we kept the original data or if YaslRoot has the line number field...
                    # We added yaml_line to YASLBaseModel just now!

                    # Let's search inside the definitions
                    if root.definitions:
                        for _ns, defs in root.definitions.items():
                            if defs.types:
                                for _type_name, type_def in defs.types.items():
                                    # Check if this type definition is related to the error
                                    # For "Unknown type 'X' for property 'Y'", we look for property 'Y' in type_def.
                                    if type_def.properties:
                                        for (
                                            prop_name,
                                            prop_def,
                                        ) in type_def.properties.items():
                                            # We might check if error_msg contains property name
                                            if (
                                                f"for property '{prop_name}'"
                                                in error_msg
                                            ):
                                                if (
                                                    hasattr(prop_def, "yaml_line")
                                                    and prop_def.yaml_line
                                                ):
                                                    found_line = prop_def.yaml_line
                                                    # We don't easily know the filename here unless we stored it in the root or passed it along.
                                                    # But 'roots' comes from 'load_schema_files(path)'.
                                                    # Since we recurse, it's hard to know exact file if imported,
                                                    # but if it's the main file, we know 'path'.
                                                    # For now let's just show line number if we find it.
                                                    break
                                    if found_line:
                                        break
                                if found_line:
                                    break
                            if found_line:
                                break
                        if found_line:
                            break

            if found_line:
                log.error(f"❌ Error generating type models (Line {found_line}): {e}")
            else:
                log.error(f"❌ Error generating type models: {e}")

            return None

    log.debug("✅ YASL schema validation successful!")
    return roots


def load_data(
    yaml_data: dict[str, Any], schema_name: str, schema_namespace: str | None = None
) -> Any:
    """
    Validate a dictionary of data against a specific registered YASL schema.

    This function retrieves the Pydantic model corresponding to the given schema name
    and namespace from the YaslRegistry, and then attempts to validate the provided
    data against it.

    Args:
        yaml_data (dict[str, Any]): The raw dictionary containing the YAML data to validate.
        schema_name (str): The name of the schema type to validate against.
        schema_namespace (str | None): The namespace where the schema is defined.

    Returns:
        Any: An instance of the validated Pydantic model if successful,
        or None if validation fails or the schema cannot be found.

    Note:
        The function catches ValidationError and SyntaxError, logs the details,
        and returns None.
    """
    log = logging.getLogger("yasl")
    try:
        result = None
        registry = YaslRegistry()

        model = registry.get_type(schema_name, schema_namespace)

        if model is None:
            log.error(
                f"❌ No schema found with name '{schema_name}' and namespece '{schema_namespace}'."
            )
            return None
        else:
            result = cast(type[BaseModel], model)(**yaml_data)  # type: ignore
            if result is None:
                log.error(f"YAML did not validate against schema '{schema_name}'.")
                return None

        log.info("✅ YAML data validation successful!")
        return result
    except ValidationError as e:
        log.error(f"❌ Validation failed with {len(e.errors())} error(s):")
        for error in e.errors():
            log.error(f"  - {error['msg']}")
        return None
    except SyntaxError as e:
        log.error(f"❌ SyntaxError in file YAML data - {getattr(e, 'msg', str(e))}")
        if hasattr(e, "text") and e.text:
            log.error(f"  > {e.text.strip()}")
        return None


# --- Main data validation logic ---
def load_data_files(path: str, model_name: str | None = None) -> Any:
    """
    Load and validate YAML data from a file against YASL schemas.

    This function reads a YAML file (which may contain multiple documents) and attempts
    to validate each document against a registered YASL schema.

    If `model_name` is provided, validation is attempted against that specific schema.
    If `model_name` is None, the function attempts to auto-detect the appropriate schema
    by matching the root keys of the YAML data against the fields of registered types.

    Args:
        path (str): The file path to the YAML data file.
        model_name (str | None): The name of the schema to validate against.
            If None, schema auto-detection is performed.

    Returns:
        Any: A list of validated Pydantic models (one for each document in the YAML file)
        if successful, or None if validation fails or the file cannot be read.

    Note:
        The function catches exceptions like FileNotFoundError, SyntaxError, YAMLError,
        and ValidationError, logging them as errors and returning None.
    """
    log = logging.getLogger("yasl")
    log.debug(f"--- Attempting to validate data '{path}' ---")
    docs = []
    data = None
    try:
        yaml_loader = YAML(typ="rt")
        with open(path) as f:
            docs.extend(yaml_loader.load_all(f))

    except FileNotFoundError:
        log.error(f"❌ Error - File not found at '{path}'")
        return None
    except SyntaxError as e:
        log.error(f"❌ Error - Syntax error in data file '{path}'\n  - {e}")
        return None
    except YAMLError as e:
        log.error(f"❌ Error - YAML error while parsing data '{path}'\n  - {e}")
        return None
    except ValueError as e:
        log.error(f"❌ Error - value error while parsing data '{path}'\n  - {e}")
        return None
    except Exception as e:
        log.error(f"❌ An unexpected error occurred - {type(e)} - {e}")
        traceback.print_exc()
        return None
    try:
        results = []
        registry = YaslRegistry()
        for data in docs:
            candidate_model_names: list[tuple[str, str | None]] = []
            if model_name is None:
                root_keys: list[str] = list(data.keys())
                log.debug(f"Auto-detecting schema for YAML root keys in '{path}'")
                yasl_result = registry.get_types()
                for type_id, type_def in yasl_result.items() or []:
                    type_name, type_namespace = type_id
                    type_def_root_keys: list[str] = list(type_def.model_fields.keys())
                    if all(k in type_def_root_keys for k in root_keys):
                        log.debug(
                            f"Auto-detected root model '{type_name}' for YAML file '{path}'"
                        )
                        candidate_model_names.append((type_name, type_namespace))
            else:
                registry_item = registry.get_type(model_name)
                if registry_item:
                    candidate_model_names.append(
                        (model_name, registry_item.__module__ or None)
                    )
                else:
                    candidate_model_names.append((model_name, None))

            log.debug(
                f"Identified candidate model names for '{path}' - {candidate_model_names}"
            )

            for schema_name, schema_namespace in candidate_model_names:
                if registry.get_type(schema_name, schema_namespace) is None:
                    continue
                model = registry.get_type(schema_name, schema_namespace)
                log.debug(
                    f"Using schema '{schema_name}' for data validation of {path}."
                )

                # Inject line number if available
                if hasattr(data, "lc") and hasattr(data.lc, "line"):
                    data["yaml_line"] = data.lc.line + 1

                if model is not None:
                    result = cast(type[BaseModel], model)(**data)  # type: ignore
                    if result is not None:
                        results.append(result)
                        break
                    else:
                        log.debug(
                            f"Data in '{path}' did not validate against schema '{schema_name}'."
                        )

        if not results or len(results) == 0:
            log.error(f"❌ No valid schema found to validate data in '{path}'")
            return None
        log.info(f"✅ YAML '{path}' data validation successful!")
        return results
    except ValidationError as e:
        log.error(f"❌ Validation failed with {len(e.errors())} error(s):")
        for error in e.errors():
            line = _get_line_for_error(data, error["loc"])
            path_str = " -> ".join(map(str, error["loc"]))
            if line:
                log.error(f"  - Line {line} - '{path_str}' -> {error['msg']}")
            else:
                log.error(f"  - Location '{path_str}' -> {error['msg']}")
        return None
    except SyntaxError as e:
        log.error(
            f"❌ SyntaxError in file '{path}' "
            f"at line {getattr(e, 'lineno', '?')}, offset {getattr(e, 'offset', '?')} - {getattr(e, 'msg', str(e))}"
        )
        if hasattr(e, "text") and e.text:
            log.error(f"  > {e.text.strip()}")
        return None
    except Exception as e:
        log.error(f"❌ An unexpected error occurred - {type(e)} - {e}")
        traceback.print_exc()
        return None
