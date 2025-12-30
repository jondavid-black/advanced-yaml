"""
YAQL CLI main entry point.
"""

import argparse
import cmd
import logging
import sys

from common.utils import advanced_yaml_version

from .engine import YaqlEngine


class YaqlShell(cmd.Cmd):
    intro = "Welcome to the YAQL shell.   Type help or ? to list commands.\n"
    prompt = "(yaql) "

    def __init__(self, engine: YaqlEngine):
        super().__init__()
        self.engine = engine
        self.log = logging.getLogger(__name__)

    def do_load_schema(self, arg):
        """
        Load a YASL schema definition.
        Usage: load_schema <path_to_yasl_file_or_dir>
        """
        if not arg:
            self.log.error("❌ Please provide a file path or directory.")
            return

        self.log.info(f"Loading schema from: {arg}")
        if self.engine.load_schema(arg):
            self.log.info("✅ Schema loaded successfully.")
        else:
            self.log.error("❌ Failed to load schema.")

    def do_load_data(self, arg):
        """
        Load YAML data files.
        Usage: load_data <path_to_yaml_file_or_dir>
        """
        if not arg:
            self.log.error("❌ Please provide a file path or directory.")
            return

        self.log.info(f"Loading data from: {arg}")
        count = self.engine.load_data(arg)
        self.log.info(f"✅ Loaded {count} data records.")

    def do_store_schema(self, arg):
        """
        Store the current schema to a file.
        Usage: store_schema <path_to_output_yasl_file>
        """
        if not arg:
            self.log.error("❌ Please provide an output file path.")
            return

        # Not implemented in the new SQLModel engine yet
        # We need to serialize sql_models back to YASL
        self.log.error("❌ store_schema is not yet implemented for SQLModel engine.")

    def do_export_data(self, arg):
        """
        Export the current database contents to YAML files.
        Usage: export_data <path_to_output_dir> [min]

        Options:
            min     If specified, writes all records of a type to a single file separated by '---'.
        """
        if not arg:
            self.log.error("❌ Please provide an output directory.")
            return

        args = arg.split()
        path = args[0]
        min_mode = False

        if len(args) > 1 and args[1] == "min":
            min_mode = True

        self.log.info(f"Exporting data to: {path} (min_mode={min_mode})")
        count = self.engine.export_data(path, min_mode=min_mode)
        self.log.info(f"✅ Exported {count} data files.")

    def do_sql(self, arg):
        """
        Execute a SQL query against the in-memory database.
        Usage: sql <query>
        """
        if not arg:
            self.log.error("❌ Please provide a SQL query.")
            return

        try:
            results = self.engine.execute_sql(arg)

            if results is None:
                self.log.info("Query executed successfully.")
            elif len(results) == 0:
                self.log.info("Query executed successfully (no results).")
            else:
                # Basic table printing
                headers = results[0].keys()
                print(" | ".join(headers))
                print("-" * (sum(len(h) for h in headers) + 3 * len(headers)))
                for row in results:
                    print(" | ".join(str(v) for v in row.values()))

        except Exception as e:
            self.log.error(f"❌ SQL Error: {e}")

    def do_exit(self, arg):
        """Exit the YAQL shell."""
        # Unsaved changes tracking removed for now
        # if self.engine.unsaved_changes:
        #     confirm = input(
        #         "⚠️ You have unsaved changes. Are you sure you want to exit? (y/N): "
        #     )
        #     if confirm.lower() != "y":
        #         return

        # self.engine.close() # Close is not really needed for memory db, but good practice if exposed
        self.log.info("Goodbye!")
        return True

    def do_quit(self, arg):
        """Exit the YAQL shell."""
        return self.do_exit(arg)


def get_parser():
    parser = argparse.ArgumentParser(
        prog="yaql", description="YAQL - YAML Advanced Query Language CLI Tool"
    )

    parser.add_argument(
        "--version", action="store_true", help="Show version information and exit"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress output except for errors"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    if args.verbose and args.quiet:
        print("❌ Cannot use both --quiet and --verbose.")
        sys.exit(1)

    if args.version:
        print(f"YAQL version {advanced_yaml_version()}")
        sys.exit(0)

    # Configure logging based on flags
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.ERROR

    logging.basicConfig(level=log_level, format="%(message)s")

    engine = YaqlEngine()
    shell = YaqlShell(engine)

    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting...")
        # engine.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
