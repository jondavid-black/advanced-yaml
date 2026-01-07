import datetime
import logging
import re
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

import markdown_it
import numpy as np
import requests
from pydantic import field_validator, model_validator

from yasl.cache import YaslRegistry
from yasl.pydantic_types import IfThen, Property, TypeDef
from yasl.validator_helpers import _ensure_comparable


def unique_value_validator(
    cls,
    value: Any,
    type_name: str,
    property_name: str,
    type_namespace: str | None = None,
):
    registry = YaslRegistry()
    registry.register_unique_value(type_name, property_name, value, type_namespace)
    return value


# list validation
def list_min_validator(cls, value: list[Any], bound: int):
    if len(value) < bound:
        raise ValueError(f"List must contain at least {bound} items")
    return value


def list_max_validator(cls, value: list[Any], bound: int):
    if len(value) > bound:
        raise ValueError(f"List must contain at most {bound} items")
    return value


# numeric validation
def gt_validator(cls, value, bound):
    val, bnd = _ensure_comparable(value, bound)
    if val <= bnd:
        raise ValueError(f"Value must be greater than {bound}")
    return value


def ge_validator(cls, value, bound):
    val, bnd = _ensure_comparable(value, bound)
    if val < bnd:
        raise ValueError(f"Value must be greater than or equal to {bound}")
    return value


def lt_validator(cls, value, bound):
    val, bnd = _ensure_comparable(value, bound)
    if val >= bnd:
        raise ValueError(f"Value must be less than {bound}")
    return value


def le_validator(cls, value, bound):
    val, bnd = _ensure_comparable(value, bound)
    if val > bnd:
        raise ValueError(f"Value must be less than or equal to {bound}")
    return value


def exclude_validator(cls, value, excluded_values):
    # Need to handle exclusion list potentially containing quantities
    # This one is tricky because excluded_values is a list.
    # We should probably try to convert 'value' to match items in list, or vice versa.
    # For now, let's keep it simple and iterate.

    for ex in excluded_values:
        val, ex_val = _ensure_comparable(value, ex)

        # Handle astropy quantity comparison explicitly
        if hasattr(val, "unit") and hasattr(ex_val, "unit"):
            try:
                # Check if units are equivalent first
                # Ensure .unit attribute exists and is not None (double check)
                val_unit = getattr(val, "unit", None)
                ex_unit = getattr(ex_val, "unit", None)

                if (
                    val_unit is not None
                    and ex_unit is not None
                    and val_unit.is_equivalent(ex_unit)
                ):
                    # Convert val to ex_val unit for comparison
                    val_conv = val.to(ex_unit)
                    # Check for equality with tolerance for floats
                    if np.isclose(val_conv.value, ex_val.value):
                        raise ValueError(f"Value must not be one of {excluded_values}")
            except Exception:
                pass

        # Check for simple equality as well (catches cases where astropy equality fails or isn't applicable)
        if val == ex_val:
            raise ValueError(f"Value must not be one of {excluded_values}")

    return value


def multiple_of_validator(cls, value, bound):
    # Modulo with physical types is supported by astropy
    val, bnd = _ensure_comparable(value, bound)
    # Note: astropy Quantity modulo returns a Quantity.
    # We check if result is zero (or close to zero for floats).

    if hasattr(val, "unit") and hasattr(bnd, "unit"):
        # For physical types, convert value to bound's unit before modulo
        # to avoid floating point issues with different bases (like m vs cm)
        try:
            val_conv = val.to(bnd.unit)
            remainder = val_conv.value % bnd.value
            # Use a small tolerance for floating point comparisons
            if abs(remainder) > 1e-9 and abs(remainder - bnd.value) > 1e-9:
                raise ValueError(f"Value must be a multiple of {bound}")
        except Exception as e:
            # Fallback if conversion fails (though _ensure_comparable should catch unit mismatch)
            if val % bnd != 0:
                raise ValueError(f"Value must be a multiple of {bound}") from e

    else:
        if val % bnd != 0:
            raise ValueError(f"Value must be a multiple of {bound}")
    return value


# string validation
def str_min_validator(cls, value: str, min_length: int):
    if len(value) < min_length:
        raise ValueError(f"String must be at least {min_length} characters long")
    return value


def str_max_validator(cls, value: str, max_length: int):
    if len(value) > max_length:
        raise ValueError(f"String must be at most {max_length} characters long")
    return value


def str_regex_validator(cls, value: str, regex: str):
    if not re.fullmatch(regex, value):
        raise ValueError(f"Value '{value}' does not match pattern '{regex}'")
    return value


# date validators
def date_before_validator(
    cls,
    value: datetime.datetime | datetime.date | datetime.time,
    before: datetime.datetime | datetime.date | datetime.time,
):
    if not isinstance(value, type(before)):
        raise ValueError(
            f"Type of value '{type(value)}' does not match type of 'before' '{type(before)}'"
        )
    if value >= before:  # type: ignore
        raise ValueError(f"Date '{value}' must be before '{before}'")
    return value


def date_after_validator(
    cls,
    value: datetime.datetime | datetime.date | datetime.time,
    after: datetime.datetime | datetime.date | datetime.time,
):
    if not isinstance(value, type(after)):
        raise ValueError(
            f"Type of value '{type(value)}' does not match type of 'after' '{type(after)}'"
        )
    if value <= after:  # type: ignore
        raise ValueError(f"Date '{value}' must be after '{after}'")
    return value


# url validators
def url_base_validator(cls, value: str, url_base: str):
    parsed = urlparse(value)
    if url_base != parsed.netloc:
        raise ValueError(f"URL '{value}' does not have a base of '{url_base}'")
    return value


def url_protocol_validator(cls, value: str, protocols: list[str]):
    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme not in protocols:
        raise ValueError(f"URL '{value}' must use one of the protocols {protocols}")
    return value


def url_reachable_valiator(cls, value: str, reachable: bool):
    if reachable:
        try:
            response = requests.head(value, allow_redirects=True, timeout=3)
            if response.status_code >= 400:
                raise ValueError(
                    f"URL '{value}' is not reachable (status {response.status_code})"
                )
        except requests.RequestException as e:
            raise ValueError(f"URL '{value}' is not reachable: {e}") from e
    return value


def is_dir_validator(cls, value: str, is_dir: bool):
    path = Path(value)
    # Check if the path looks like a directory (ends with separator or no suffix)
    if not (path.suffix == "" or value.endswith(("/", "\\"))):
        raise ValueError(f"Path '{value}' must be a directory")
    return value


def is_file_validator(cls, value: str, is_file: bool):
    path = Path(value)
    # Check if the path looks like a file (does not end with a separator, has a suffix)
    if not (path.suffix != "" and not value.endswith(("/", "\\"))):
        raise ValueError(f"Path '{value}' must be a file")
    return value


def file_ext_validator(cls, value: str, extensions: list[str]):
    path = Path(value)
    # First, ensure it's a file
    is_file_validator(cls, value, True)
    # Check if the file has one of the allowed extensions
    if extensions and path.suffix not in [
        f".{ext}" if not ext.startswith(".") else ext for ext in extensions
    ]:
        raise ValueError(
            f"File '{value}' must have one of the following extensions: {extensions}"
        )
    return value


def path_exists_validator(cls, value: str, exists: bool):
    path = Path(value)
    # Check if the path exists on the filesystem
    if exists and not path.exists():
        raise ValueError(f"Path '{value}' must exist on the filesystem")
    return value


# ref validators
def ref_exists_validator(cls, value: Any, target: str):
    type_name, property_name = target.rsplit(".", 1)
    type_namespace = None
    if type_name and "." in type_name:
        type_namespace, type_name = type_name.rsplit(".", 1)

    registry = YaslRegistry()

    def check_value(v):
        if not registry.unique_value_exists(
            type_name, property_name, v, type_namespace
        ):
            raise ValueError(
                f"Referenced value '{v}' does not exist for 'ref[{target}]"
            )

    if isinstance(value, list):
        for v in value:
            check_value(v)
    else:
        check_value(value)

    return value


# any validator
def any_of_validator(cls, value: Any, any_of: list[str], namespace: str | None = None):
    registry = YaslRegistry()
    for t in any_of:
        if t.endswith("[]"):
            elem_type_name = t[:-2]

            # Helper to check if a value matches the element type
            def check_list_item(item, type_name):
                # Primitive types
                if type_name == "str":
                    return isinstance(item, str)
                if type_name == "int":
                    return isinstance(item, int)
                if type_name == "float":
                    return isinstance(item, float)
                if type_name == "bool":
                    return isinstance(item, bool)

                # Check for enums/types in registry
                ns = namespace
                name = type_name
                if "." in type_name:
                    ns, name = type_name.rsplit(".", 1)

                enum_cls = registry.get_enum(name, ns, namespace)
                if (
                    enum_cls
                    and isinstance(item, str)
                    and item in [e.value for e in cast(Any, enum_cls)]
                ):  # type: ignore
                    return True

                type_cls = registry.get_type(name, ns, namespace)
                # For complex types, validation usually happens during parsing,
                # but 'value' here might already be parsed or raw dict
                if type_cls:
                    # This is tricky without fully instantiating, but Pydantic handles recursive models.
                    # If 'item' is already a model instance:
                    if isinstance(item, type_cls):
                        return True
                    # If 'item' is a dict, we can't easily check without trying to parse
                    if isinstance(item, dict):
                        return True  # Optimistic check?

                return False

            if isinstance(value, list):
                # We can't easily validate complex types inside list here without full context.
                # Relying on 'eval' was dangerous and context-missing.
                # For now, let's trust that if the schema says list[], and we have a list,
                # and items *look* okay, it's a match.
                # NOTE: This validator logic is fragile for complex types mixed with primitives in any_of.
                # Improving support for primitives first:
                try:
                    if all(check_list_item(v, elem_type_name) for v in value):
                        return value
                except Exception:
                    pass
        else:
            # Primitive checks
            if t == "str" and isinstance(value, str):
                return value
            if t == "int" and isinstance(value, int):
                return value
            if t == "float" and isinstance(value, float):
                return value
            if t == "bool" and isinstance(value, bool):
                return value

            # Registry checks
            ns = namespace
            name = t
            if "." in t:
                ns, name = t.rsplit(".", 1)

            enum_cls = registry.get_enum(name, ns, namespace)
            if enum_cls:
                # Value matches if it is a valid value for this enum
                # The registry stores the Enum class itself (subclass of enum.Enum)
                # To iterate over values, we access the members.
                # Cast to Any to bypass static analysis complaining about iterating over Enum class
                # which is valid in runtime Python (iterating over Enum class yields members)
                if isinstance(value, str) and value in [
                    e.value for e in cast(Any, enum_cls)
                ]:
                    return value

            type_cls = registry.get_type(name, ns, namespace)
            if type_cls:
                if isinstance(value, type_cls):
                    return value
                if isinstance(value, dict):
                    # If it's a dict, we might want to let Pydantic try to coerce it later?
                    # But 'any_of_validator' runs *after* field assignment?
                    # Actually this is a field_validator.
                    # If the target type is a Pydantic model, 'value' might still be a dict here.
                    # We can't fully validate it here without parsing.
                    # But we can check if it looks like the target model?
                    # Let's assume yes for now if it is a dict.
                    return value

    # If we fall through, we try to produce a helpful error,
    # but the previous logic using `eval(t)` was causing NameError because
    # the types weren't in scope.
    raise ValueError(f"Value '{value}' must be one of {any_of}")


# enum validator
def enum_validator(cls, value: Any, values: list[str]):
    str_value = str(value)
    if str_value.split(".")[-1] not in values:
        raise ValueError(f"Value '{value}' must be one of {values}")
    return value


# map validator
def map_validator(
    cls,
    value: dict[Any, Any],
    key_type: str,
    value_type: str,
    any_of: list[str] | None = None,
):
    # validate key type is str, int, or an enumation
    registry = YaslRegistry()
    enum_namespace = None
    enum_name = key_type
    if "." in key_type:
        enum_namespace, enum_name = key_type.rsplit(".", 1)
    if (
        key_type not in ["str", "int"]
        and registry.get_enum(enum_name, enum_namespace) is None
    ):
        raise ValueError(f"Map key type '{key_type}' is not supported")
    # validate value type of any is allowed by constraints
    if value_type == "any" and any_of is not None:
        if not any(isinstance(v, eval(t)) for t in any_of for v in value.values()):
            raise ValueError(f"Map values must be one of {any_of}")
    return value


# type validator
def type_validator(cls, value: str, namespace: str | None = None):
    registry = YaslRegistry()
    from yasl.primitives import PRIMITIVE_TYPE_MAP

    # 1. Check if it's a primitive type
    if value in PRIMITIVE_TYPE_MAP:
        return value

    # 2. Check if it's a list of primitives or complex types
    if value.endswith("[]"):
        base_type = value[:-2]
        # Recursively validate the base type
        type_validator(cls, base_type, namespace)
        return value

    # 3. Check if it's a map
    if value.startswith("map[") and value.endswith("]"):
        # Basic check for map structure, deeper validation requires parsing
        map_content = value[4:-1]
        if "," not in map_content:
            raise ValueError(f"Invalid map type format: '{value}'")

        # Recursively validate key and value types
        try:
            key_type, value_type = [t.strip() for t in map_content.split(",", 1)]
        except ValueError as e:
            raise ValueError(
                f"Invalid map type format: '{value}'. Expected 'map[key_type, value_type]'"
            ) from e

        # Validate key type (must be str, int, or enum according to map_validator rules)
        # First check if it is a valid type in general
        type_validator(cls, key_type, namespace)

        # Then check specific map key constraints if we want to be strict strictly about valid YASL maps
        # map_validator enforces: str, int, or enum.
        registry = YaslRegistry()
        is_enum = False
        enum_ns = namespace
        enum_name = key_type
        if "." in key_type:
            parts = key_type.rsplit(".", 1)
            enum_ns = parts[0]
            enum_name = parts[1]

        if registry.get_enum(enum_name, enum_ns, namespace) is not None:
            is_enum = True

        if key_type not in ["str", "int"] and not is_enum:
            raise ValueError(
                f"Invalid map key type: '{key_type}'. Must be 'str', 'int', or an Enum."
            )

        # Validate value type recursively
        type_validator(cls, value_type, namespace)

        return value

    # 4. Check if it's a reference
    if value.startswith("ref[") and value.endswith("]"):
        # We accept refs as valid type definitions
        return value

    # 5. Check if it's a registered type or enum
    # Handle optional namespace in value
    val_name = value
    val_ns = namespace
    if "." in value:
        parts = value.rsplit(".", 1)
        val_ns = parts[0]
        val_name = parts[1]

    if registry.get_type(val_name, val_ns, namespace) is not None:
        return value

    if registry.get_enum(val_name, val_ns, namespace) is not None:
        return value

    # Check for similar types or namespace confusion to provide better error messages
    # Case 1: Type exists in another namespace
    if "." not in value:  # If user didn't specify namespace
        # Search all namespaces for this type name
        found_namespaces = []
        for (name, ns), _ in registry.yasl_type_defs.items():
            if name == val_name and ns != val_ns:
                found_namespaces.append(ns)
        for (name, ns), _ in registry.yasl_enumerations.items():
            if name == val_name and ns != val_ns:
                found_namespaces.append(ns)

        if found_namespaces:
            valid_namespaces = ", ".join(
                sorted([str(n) for n in set(found_namespaces)])
            )
            raise ValueError(
                f"Type '{value}' not found in namespace '{val_ns or 'default'}'. Did you mean one of: {valid_namespaces}?"
            )

    raise ValueError(f"Type '{value}' is not a valid primitive or registered type.")


# markdown validator
def markdown_validator(cls, value: str):
    try:
        md = markdown_it.MarkdownIt()
        tokens = md.parse(value)
        if not tokens:
            raise ValueError("Markdown content is empty or invalid.")
        return value
    except Exception as e:
        raise ValueError("Markdown content is not valid.") from e


def property_validator_factory(
    typedef_name: str,
    type_namespace: str,
    type_def: TypeDef,
    property_name: str,
    property: Property,
) -> Callable:
    validators = []
    # list validators
    if property.list_min is not None:
        validators.append(partial(list_min_validator, bound=property.list_min))
    if property.list_max is not None:
        validators.append(partial(list_max_validator, bound=property.list_max))

    # unique validator
    if property.unique:
        if "." in property_name:
            property_namespace, property_name = property_name.rsplit(".", 1)
        else:
            property_namespace = type_namespace
        validators.append(
            partial(
                unique_value_validator,
                type_name=typedef_name,
                property_name=property_name,
                type_namespace=property_namespace,
            )
        )

    # numeric validators
    if property.gt is not None:
        validators.append(partial(gt_validator, bound=property.gt))
    if property.ge is not None:
        validators.append(partial(ge_validator, bound=property.ge))
    if property.lt is not None:
        validators.append(partial(lt_validator, bound=property.lt))
    if property.le is not None:
        validators.append(partial(le_validator, bound=property.le))
    if property.exclude is not None:
        validators.append(partial(exclude_validator, excluded_values=property.exclude))
    if property.multiple_of is not None:
        validators.append(partial(multiple_of_validator, bound=property.multiple_of))

    # string validators
    if property.str_min is not None:
        validators.append(partial(str_min_validator, min_length=property.str_min))
    if property.str_max is not None:
        validators.append(partial(str_max_validator, max_length=property.str_max))
    if property.str_regex is not None:
        validators.append(partial(str_regex_validator, regex=property.str_regex))

    # date validators
    if property.before is not None:
        validators.append(partial(date_before_validator, before=property.before))
    if property.after is not None:
        validators.append(partial(date_after_validator, after=property.after))

    # path validators
    if property.path_exists is not None:
        validators.append(partial(path_exists_validator, exists=property.path_exists))
    if property.is_dir is not None:
        validators.append(partial(is_dir_validator, is_dir=property.is_dir))
    if property.is_file is not None:
        validators.append(partial(is_file_validator, is_file=property.is_file))
    if property.file_ext is not None:
        validators.append(partial(file_ext_validator, extensions=property.file_ext))

    # uri validators
    if property.url_base is not None:
        validators.append(partial(url_base_validator, url_base=property.url_base))
    if property.url_protocols is not None:
        validators.append(
            partial(url_protocol_validator, protocols=property.url_protocols)
        )
    if property.url_reachable is not None:
        validators.append(
            partial(url_reachable_valiator, reachable=property.url_reachable)
        )

    # any validator
    if property.any_of is not None and not property.type.startswith("map[]"):
        validators.append(
            partial(any_of_validator, any_of=property.any_of, namespace=type_namespace)
        )

    # ref validators (always validate references)
    if property.type.startswith("ref[") and (
        property.no_ref_check is None or property.no_ref_check is False
    ):
        ref_target = property.type[4:-1]
        if ref_target.endswith("]["):  # This occurs for ref types that are lists
            ref_target = ref_target[:-2]

        validators.append(partial(ref_exists_validator, target=ref_target))

    # enum validators
    registry = YaslRegistry()
    enum_names: list[tuple[str, str | None]] = registry.get_enums()

    if property.type in dict(enum_names).keys():
        enum_type = registry.get_enum(property.type, type_def.namespace)
        if enum_type is None:
            raise ValueError(
                f"Enum type '{property.type}' not found for property '{property_name}' in type '{typedef_name}'"
            )
        validators.append(partial(enum_validator, values=[e.value for e in enum_type]))  # type: ignore

    # map validators
    if property.type.startswith("map["):
        # extract key and value types
        map_types = property.type[4:-1]
        if "," not in map_types:
            raise ValueError(f"Map type '{property.type}' is not valid")
        key_type, value_type = map(str.strip, map_types.split(",", 1))
        validators.append(
            partial(
                map_validator,
                key_type=key_type,
                value_type=value_type,
                any_of=property.any_of,
            )
        )

    # type validator
    if property.type == "type":
        validators.append(partial(type_validator, namespace=type_namespace))

    # markdown validator
    if property.type == "markdown":
        validators.append(markdown_validator)

    def multi_validator(cls, value):
        for validator in validators:
            value = validator(cls, value)
        return value

    return field_validator(property_name)(multi_validator)


# type validators
def only_one_validator(cls, values: dict[str, Any], fields: list[str]):
    data_keys = [key for key, val in values.model_dump().items() if val is not None]  # type: ignore
    if sum(1 for field in fields if field in data_keys) != 1:
        raise ValueError(f"Exactly one of {fields} must be present")
    return values


def at_least_one_validator(cls, values: dict[str, Any], fields: list[str]):
    data_keys = [key for key, val in values.model_dump().items() if val is not None]  # type: ignore
    if sum(1 for field in fields if field in data_keys) < 1:
        raise ValueError(f"At least one of {fields} must be present")
    return values


def if_then_validator(cls, values: dict[str, Any], if_then: IfThen):
    eval_field = if_then.eval
    eval_value = if_then.value
    present_fields = if_then.present or []
    absent_fields = if_then.absent or []
    values_dict = values.model_dump()  # type: ignore
    if eval_field in values_dict:
        eval_value_type = type(values_dict[eval_field])
        typed_eval_value = [eval_value_type(v) for v in eval_value]
        if values_dict[eval_field] in typed_eval_value:
            for field in present_fields:
                if field not in values_dict or values_dict[field] is None:
                    raise ValueError(
                        f"Field '{field}' must be present when '{eval_field}' is in {eval_value}"
                    )
            for field in absent_fields:
                if field in values_dict and values_dict[field] is not None:
                    raise ValueError(
                        f"Field '{field}' must be absent when '{eval_field}' is in {eval_value}"
                    )
    return values


def preferred_presence_validator(cls, values: Any, properties: dict[str, Property]):
    log = logging.getLogger("yasl")
    values_dict = values.model_dump()

    # Access the hidden yaml_line field if it exists
    line_info = ""
    if hasattr(values, "yaml_line") and values.yaml_line is not None:
        line_info = f" at line {values.yaml_line}"

    for prop_name, prop in properties.items():
        if prop.presence == "preferred":
            if prop_name not in values_dict or values_dict[prop_name] is None:
                log.warning(
                    f"⚠️  Warning: Preferred property '{prop_name}' is missing{line_info}"
                )
    return values


def type_validator_factory(model: TypeDef) -> Callable:
    validators = []
    if model.validators is not None:
        if model.validators.only_one is not None:
            validators.append(
                partial(only_one_validator, fields=model.validators.only_one)
            )
        if model.validators.at_least_one is not None:
            validators.append(
                partial(at_least_one_validator, fields=model.validators.at_least_one)
            )
        if model.validators.if_then is not None:
            for item in model.validators.if_then:
                validators.append(partial(if_then_validator, if_then=item))

    if model.properties:
        validators.append(
            partial(preferred_presence_validator, properties=model.properties)
        )

    @model_validator(mode="after")
    def multi_validator(cls, values):
        for validator in validators:
            values = validator(cls, values)
        return values

    return multi_validator  # type: ignore
