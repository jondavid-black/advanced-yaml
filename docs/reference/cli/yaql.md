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

### `export_data`
Export the current database contents to YAML files.

**Usage:** `export_data <path_to_output_dir> [min]`

**Options:**
* `min`: If specified, writes all records of a type to a single file separated by '---'.

### `sql`
Execute a SQL query against the in-memory database.

**Usage:** `sql <query>`

### `exit` / `quit`
Exit the YAQL shell.
