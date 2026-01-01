# Quick Start

This guide will help you get started with **YASL** (YAML Advanced Schema Language) by defining a simple schema, creating a data file, and validating it using the CLI.

## 1. Define a Schema

Create a file named `person.yasl`. This file defines the structure and validation rules for our data. We'll define a `person` type in the `acme` namespace.

```yaml title="person.yasl"
definitions:
  acme:
    types:
      person:
        description: Information about a person.
        properties:
          name:
            type: str
            description: The person's full name.
            presence: required
          age:
            type: int
            description: The person's age.
            presence: required
            ge: 0       # Must be greater than or equal to 0
            lt: 125     # Must be less than 125
          email:
            type: str
            description: Contact email address.
            presence: optional
            pattern: "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
```

You can verify that your schema file is syntactically correct using the `schema` command:

```bash
yasl schema person.yasl
```

## 2. Create Data

Now, create a YAML file named `data.yaml` that adheres to the schema we just defined. You can have multiple YAML documents in a single file separated by `---`.

```yaml title="data.yaml"
name: John Doe
age: 30
email: john.doe@example.com
---
name: Jane Smith
age: 25
# email is optional, so we can omit it
```

## 3. Validate

Use the `yasl check` command to validate your data against the schema.

```bash
yasl check person.yasl data.yaml
```

**Expected Output:**

If everything is correct, you should see a success message (depending on your logging level, it might be silent on success or show a confirmation).

```text
✅ YAML 'data.yaml' data validation successful!
```

## 4. Experimenting with Errors

Try modifying `data.yaml` to violate a rule, for example, by setting `age` to `150` or removing the required `name` field.

```yaml title="data.yaml (invalid)"
name: Highlander
age: 400  # This violates the 'lt: 125' rule
```

Run the validation command again:

```bash
yasl check person.yasl data.yaml
```

**Expected Output:**

YASL will report the validation error:

```text
❌ Validation failed with 1 error(s):
  - Line 2 - 'age' -> Input should be less than 125
```

## Next Steps

*   Explore the **[YASL CLI Reference](../reference/cli/yasl.md)** for more command options.
*   Check out the **[YASL API Reference](../reference/api/yasl.md)** to use YASL in your Python code.
