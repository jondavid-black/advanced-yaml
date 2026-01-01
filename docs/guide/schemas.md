# Using Schemas

This guide provides a comprehensive overview of how to define schemas using **YASL** (YAML Advanced Schema Language).

## Schema Structure

A YASL schema file is a standard YAML file that follows a specific structure. The root of the document must contain a `definitions` key.

```yaml
definitions:
  <namespace>:
    types:
      <type_name>:
        # Type definition...
    enums:
      <enum_name>:
        # Enum definition...
```

### Components

*   **Definitions**: The top-level container for all schema definitions.
*   **Namespace**: A logical grouping for your types and enums (e.g., `acme`, `my_app`, `common`). This helps avoid naming collisions when importing schemas.
*   **Types**: Defines the data structures (models) and their validation rules.
*   **Enums**: Defines reusable sets of allowed values.

## Defining Types

Types are the core building blocks of a YASL schema. A type defines a set of **properties** that an object must have.

```yaml
definitions:
  my_app:
    types:
      user:
        description: A registered user.
        properties:
          username:
            type: str
            presence: required
          age:
            type: int
            presence: optional
```

### Property Attributes

Each property within a type can have several attributes to control its validation:

| Attribute | Description | Values |
| :--- | :--- | :--- |
| `type` | **Required.** The data type of the property. | `str`, `int`, `bool`, `float`, `date`, `datetime`, `list[...]`, `map[...]`, or a custom type/enum name. |
| `description` | Documentation for the property. | Any string. |
| `presence` | Whether the property is mandatory. | `required`, `optional` (default: `optional`). |
| `default` | A default value if the property is missing. | Any valid value for the type. |

## Defining Enums

Enums (Enumerations) allow you to define a fixed set of valid values for a property.

```yaml
definitions:
  my_app:
    enums:
      status:
        description: The status of a task.
        values:
          - pending
          - in_progress
          - completed
          - cancelled
```

You can then use this enum in a type definition:

```yaml
    types:
      task:
        properties:
          title:
            type: str
          current_status:
            type: status  # References the 'status' enum defined above
```

## Collection Types

### Lists

To define a list of items, append `[]` to the type name.

```yaml
properties:
  tags:
    type: str[]        # A list of strings
  scores:
    type: int[]        # A list of integers
  history:
    type: status[]     # A list of enum values
```

### Maps

To define a dictionary (key-value pairs), use the syntax `map[KeyType, ValueType]`.

*   **KeyType**: Must be `str`, `int`, or an Enum.
*   **ValueType**: Can be any primitive, custom type, or enum.

```yaml
properties:
  settings:
    type: map[str, str]       # String keys, String values
  daily_scores:
    type: map[date, int]      # Date keys, Integer values
```

## Validator Reference

YASL provides a comprehensive suite of validators to ensure your data meets specific constraints. These validators can be applied to properties in your schema definition.

### String Validators
Applies to `str`, `string`, `text`.

*   `str_min`: Validates the string has at least this many characters.
*   `str_max`: Validates the string has at most this many characters.
*   `str_regex`: Validates the string matches the provided regular expression pattern.

### Numeric Validators
Applies to `int`, `float`, and physical quantity types.

When used with physical quantities, these validators automatically handle unit conversions. For example, checking if `500 m` is `lt: 1 km` will correctly pass validation.

*   `gt`: Greater than (`>`).
*   `ge`: Greater than or equal to (`>=`).
*   `lt`: Less than (`<`).
*   `le`: Less than or equal to (`<=`).
*   `multiple_of`: Value must be a multiple of this number (e.g., `1 m` is a multiple of `10 cm`).
*   `exclude`: A list of specific values that are not allowed. Checks for physical equivalence (e.g., excluding `1000 m` will also exclude `1 km`).

**Example with Physical Units:**

```yaml
properties:
  distance:
    type: length
    gt: 10 m       # Validates that distance is > 10 meters
    lt: 5 km       # Validates that distance is < 5 kilometers
  wavelength:
    type: length
    exclude:
      - 550 nm     # Excludes specific wavelength
```

### List Validators
Applies to any list property.

*   `list_min`: The list must contain at least this many items.
*   `list_max`: The list must contain at most this many items.

### Date & Time Validators
Applies to `date`, `datetime`, and `clocktime` types.

*   `before`: The value must be strictly before this date/time.
*   `after`: The value must be strictly after this date/time.

### File & Path Validators
Applies to `path` types or strings representing file system paths.

*   `path_exists`: If `true`, validates that the path exists on the local filesystem.
*   `is_dir`: If `true`, validates that the path is a directory (must end with a separator or have no extension).
*   `is_file`: If `true`, validates that the path is a file (must have an extension).
*   `file_ext`: A list of allowed file extensions (e.g., `["txt", "md"]` or `[".txt", ".md"]`).

### URL Validators
Applies to `url` types or strings representing URLs.

*   `url_base`: Validates that the URL belongs to a specific base domain/netloc.
*   `url_protocols`: A list of allowed URL schemes (e.g., `["http", "https"]`).
*   `url_reachable`: If `true`, performs a network request (HEAD) to ensure the URL returns a success status code (200-399).

### General Property Validators

*   `unique`: If `true`, ensures the value of this property is unique across all loaded instances of this type.
*   `any_of`: Validates that the value matches one of the specified types.
*   `presence`: Controls the strictness of field presence.
    *   `preferred`: Logs a warning if the field is missing, but does not fail validation.

### Type-Level Validators
These validators are defined at the type level rather than the property level and enforce relationships between fields.

*   `only_one`: A list of field names where **exactly one** must be present.
*   `at_least_one`: A list of field names where **at least one** must be present.
*   `if_then`: Conditional validation rules.
    *   `eval`: The field to check.
    *   `value`: The value(s) the `eval` field must match to trigger the rule.
    *   `present`: List of fields that **must** be present if the condition is met.
    *   `absent`: List of fields that **must** be absent if the condition is met.

## Using Namespaces

You can use types and enums defined in other namespaces using dot notation: `<namespace>.<name>`.

```yaml
definitions:
  common:
    enums:
      country_code:
        values: [US, CA, UK, FR]

  logistics:
    types:
      address:
        properties:
          street:
            type: str
          country:
            type: common.country_code  # Use across namespaces
```
