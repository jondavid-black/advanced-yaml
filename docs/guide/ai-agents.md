# AI Agent Instructions

This guide provides a standardized set of instructions you can include in your project's `AGENTS.md` (or similar system prompt file) to help AI assistants understand and work with **YASL** (YAML Advanced Schema Language).

## Recommended Prompt

Copy and paste the following block into your agent instructions file.

````markdown
# YASL (YAML Advanced Schema Language) Guidelines

This project uses YASL for data validation and schema definition. When working with YAML files in this repository, adhere to the following rules and structures.

## 1. Schema Structure

All YASL schemas must be valid YAML files (`.yasl` extension recommended) with a root `definitions` key.

### Basic Skeleton
```yaml
definitions:
  <namespace>:          # Logical grouping (e.g., 'common', 'config', 'app')
    types:              # Define data models here
      <TypeName>:
        description: "Optional description of the type"
        properties:
          <property_name>:
            type: <primitive_type>
            presence: required  # optional (default), required, preferred
        validators:
          at_least_one: [<property_name>, property_name]
            # ... additional validators
    enums:              # Define reusable value sets here
      <EnumName>:
        values:
          - value1
          - value2
```

### Namespaces
*   Use namespaces to avoid naming collisions.
*   Refer to types in the same namespace by name: `type: User`.
*   Refer to types in other namespaces by dot notation: `type: common.Address`.

## 2. Supported Primitives

YASL supports a rich set of primitives. **You must use these exact type names.**

### Standard Types
*   `str` / `string`: Text.
*   `int`: Integer.
*   `float`: Floating-point number.
*   `bool`: Boolean (`true`/`false`).
*   `any`: Any valid YAML value.

### Time & Date
*   `date`: ISO 8601 Date (`YYYY-MM-DD`).
*   `datetime`: ISO 8601 DateTime (`YYYY-MM-DDTHH:MM:SS`).
*   `clocktime`: Time of day (`HH:MM:SS`).

### Filesystem & Network
*   `path`: A file system path.
*   `url`: A web URL.

### Collections
*   `<Type>[]`: A list of items (e.g., `str[]`, `int[]`, `common.Address[]`).
*   `map[<KeyType>, <ValueType>]`: A dictionary. Keys must be `str`, `int`, or an Enum. (e.g., `map[str, int]`).

### References
*   `ref[<Type>]`: A reference to another object defined elsewhere in the data. The referenced object must have a property marked with `unique: true`.
    *   Example: `owner: { type: ref[User] }` matches a User's unique identifier.

### Physical Quantities (SI Units)
YASL parses strings with units into physical quantities.
*   `length` (e.g., "10 m", "5 km")
*   `mass` (e.g., "5 kg", "100 g")
*   `time` (e.g., "10 s", "2 min") - *Physical duration, distinct from `clocktime`.*
*   `velocity` (e.g., "10 m/s", "100 km/h")
*   `temperature` (e.g., "300 K")
*   `frequency` (e.g., "60 Hz")
*   `angle` (e.g., "90 deg", "1 rad")
*   `area` (e.g., "100 m2")
*   `volume` (e.g., "10 liters", "5 m3")
*   `pressure` (e.g., "101 kPa", "1 bar")
*   `energy` (e.g., "100 J", "1 kWh")
*   `power` (e.g., "100 W")
*   `voltage` / `electrical potential` (e.g., "12 V")
*   `current` / `electrical current` (e.g., "10 A")
*   `resistance` / `electrical resistance` (e.g., "50 ohm")
*   `data quantity` (e.g., 8 byte, 50 Gb)

## 3. Validation Rules

Apply these validators as keys under the property definition.

### General Validators
*   `presence`:
    *   `optional` (default): Field can be omitted.
    *   `required`: Field must exist.
    *   `preferred`: Warns if missing, but valid.
*   `unique`: `true` enforces global uniqueness for this property value across the dataset.
*   `default`: Provides a default value if missing.

### Numeric & Physical Validators
Applies to `int`, `float`, and physical types. **Physical validators automatically handle unit conversion.**
*   `gt`: Greater than (`>`). (e.g., `gt: 10 m` allows "11 m" and "1 km", rejects "5 m").
*   `ge`: Greater than or equal to (`>=`).
*   `lt`: Less than (`<`).
*   `le`: Less than or equal to (`<=`).
*   `multiple_of`: Value is a multiple of X. (e.g., `multiple_of: 0.5`).
*   `exclude`: List of forbidden values.

### String Validators
Applies to `str`.
*   `str_min`: Min length (int).
*   `str_max`: Max length (int).
*   `str_regex`: Regex pattern string.

### Path/File Validators
Applies to `path` and `str`.
*   `path_exists`: `true` checks if path exists on disk.
*   `is_file`: `true` ensures it's a file.
*   `is_dir`: `true` ensures it's a directory.
*   `file_ext`: List of allowed extensions (e.g., `['.py', '.txt']`).

### URL Validators
Applies to `url` and `str`.
*   `url_protocols`: List of allowed schemes (e.g., `['https']`).
*   `url_reachable`: `true` attempts a network request to verify reachability.

### Type-Level Validators
Defined at the `Type` level within 'validators' (sibling to `properties`).
*   `only_one`: List of fields; exactly one must be present.
*   `at_least_one`: List of fields; one or more must be present.
*   `if_then`:
    ```yaml
    if_then:
      - eval: status           # Check this field
        value: [active]        # If equal to 'active'
        present: [start_date]  # Then 'start_date' must exist
        absent: [reason]       # And 'reason' must NOT exist
    ```

## 4. CLI Workflow

Use the CLI to verify your schemas and data.

1.  **Check Schema Syntax**:
    ```bash
    yasl schema <path/to/schema.yasl>
    ```

2.  **Validate Data against Schema**:
    ```bash
    yasl check <path/to/schema.yasl> <path/to/data.yaml> --type <RootTypeName>
    ```

## 5. Comprehensive Example

```yaml
definitions:
  config:
    types:
      ServerConfig:
        description: Main configuration for the server
        properties:
          host_ipv4:
            type: str
            str_regex: ^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$
          host_ipv6:
            type: str
          port:
            type: int
            gt: 1024
            lt: 65535
            default: 8080
          max_upload_size:
            type: data quantity
            le: 50 mb
            description: Max file upload size
          timeout:
            type: time
            default: 30 s
          environment:
            type: EnvEnum
            presence: required
        validators:
          at_least_one: [host_ipv4, host_ipv6]

    enums:
      EnvEnum:
        values: [dev, stage, prod]
```
````
