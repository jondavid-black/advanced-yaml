# YAQL CLI

::: mkdocs-argparse
    :module: yaql.cli
    :function: get_parser

## Interactive Shell Commands

The YAQL CLI provides an interactive shell for executing queries and managing data. Once inside the shell (by running `yaql`), you can use the following commands:

### `load_schema`
Load a YASL schema definition.

**Usage:** `load_schema <path_to_yasl_file_or_dir>`

### `load_data`
Load YAML data files.

**Usage:** `load_data <path_to_yaml_file_or_dir>`

### `store_schema`
Store the current schema to a file.

**Usage:** `store_schema <path_to_output_yasl_file>`

### `store_data`
Store the current database contents to YAML.

**Usage:** `store_data <path_to_output_yaml_file_or_dir>`

### `sql`
Execute a SQL query against the in-memory database.

**Usage:** `sql <query>`

### `exit` / `quit`
Exit the YAQL shell.
