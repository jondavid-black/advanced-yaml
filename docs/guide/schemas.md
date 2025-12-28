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

### Validation Rules

YASL supports specific validation rules depending on the property's `type`:

#### Numbers (`int`, `float`)

*   `ge`: Greater than or equal to.
*   `gt`: Greater than.
*   `le`: Less than or equal to.
*   `lt`: Less than.
*   `multiple_of`: Must be a multiple of this number.

#### Strings (`str`)

*   `min_len`: Minimum length.
*   `max_len`: Maximum length.
*   `pattern`: A regular expression that the string must match.

#### Files & Paths (`path`)

*   `path_exists`: Boolean. Checks if the path exists on the filesystem.
*   `is_file`: Boolean. Checks if it is a file.
*   `is_dir`: Boolean. Checks if it is a directory.
*   `file_ext`: List of allowed file extensions (e.g., `['.txt', '.md']`).

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

## References and Namespaces

You can reference types and enums defined in other namespaces using dot notation: `<namespace>.<name>`.

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
            type: common.country_code  # Reference across namespaces
```
