# Using References in YASL

YASL allows you to create relationships between different data types using the `ref[Target]` syntax. This ensures referential integrity across your data, validating that a referenced value actually exists in the target collection.

## Basic Syntax

The reference syntax is `ref[TargetType.PropertyName]`, where:
*   `TargetType` is the name of the YASL type you are referencing.
*   `PropertyName` is the specific field in that type you want to match against.

**Note:** The target property **must** be marked as `unique: true` in its definition.

## Example: Customers and Orders

Imagine you have a list of customers and a list of orders. Each order belongs to a customer, and you want to ensure that every order references a valid, existing customer.

### 1. Define the Schema

```yaml
# schema.yasl
definitions:
  store:
    types:
      customer:
        properties:
          id:
            type: int
            unique: true  # Required for references!
            presence: required
          name:
            type: str
            presence: required
      
      order:
        properties:
          order_id:
            type: int
            presence: required
          customer_id:
            type: ref[customer.id]  # Validate that this value exists in store.customer.id
            presence: required
```

### 2. Valid Data

In this example, the data passes validation because customer `101` exists.

```yaml
# data.yaml
- id: 101
  name: "Alice Smith"

- order_id: 500
  customer_id: 101  # Valid! Matches Alice's ID.
```

### 3. Invalid Data (Referential Integrity Failure)

This data will fail validation because there is no customer with ID `999`.

```yaml
# bad_data.yaml
- id: 101
  name: "Alice Smith"

- order_id: 501
  customer_id: 999  # Error! Referential integrity check fails.
```

## How It Works

When YASL validates your data:

1.  **First Pass (Individual Validation):** It checks that all fields match their basic types (e.g., `int`, `str`).
2.  **Reference Resolution:** It identifies all fields using the `ref[...]` type.
3.  **Integrity Check:** It scans the entire dataset to ensure that every `ref[Target.Property]` value has a corresponding match in the `Target` type's `Property` list.

This guarantees that your data is not only syntactically correct but also relationally consistent.
