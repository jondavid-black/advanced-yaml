"""
YASL CLI main entry point.
"""

import argparse
import sys

from common import advanced_yaml_version
from yasl import check_paths, check_schema


def get_parser():
    parser = argparse.ArgumentParser(
        prog="yasl", description="YASL - YAML Advanced Schema Language CLI Tool"
    )

    parser.add_argument(
        "--version", action="store_true", help="Show version information and exit"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress output except for errors"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--output",
        choices=["text", "json", "yaml"],
        default="text",
        help="Set output format (text, json, yaml). Default is text.",
    )

    subparsers = parser.add_subparsers(
        title="commands", dest="command", help="Available commands"
    )

    # Command: check (formerly the default behavior)
    check_parser = subparsers.add_parser(
        "check", help="Check mixed YASL schemas and YAML data"
    )
    check_parser.add_argument(
        "paths",
        nargs="+",
        help="List of files or directories containing schemas and data",
    )
    check_parser.add_argument(
        "--model",
        dest="model_name",
        help="Specific YASL schema type name to validate data against (optional)",
    )

    # Command: schema (new command)
    schema_parser = subparsers.add_parser(
        "schema", help="Check the validity of a YASL schema file"
    )
    schema_parser.add_argument(
        "schema",
        help="YASL schema file or directory",
    )

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    if args.verbose and args.quiet:
        print("❌ Cannot use both --quiet and --verbose.")
        sys.exit(1)

    if args.version:
        print(f"YASL version {advanced_yaml_version()}")
        sys.exit(0)

    if args.command == "check":
        success = check_paths(
            args.paths,
            model_name=args.model_name,
            disable_log=False,
            quiet_log=args.quiet,
            verbose_log=args.verbose,
            output=args.output,
        )
        if not success:
            sys.exit(1)
        else:
            sys.exit(0)

    elif args.command == "schema":
        valid = check_schema(
            args.schema,
            disable_log=False,
            quiet_log=args.quiet,
            verbose_log=args.verbose,
            output=args.output,
        )
        if not valid:
            sys.exit(1)
        else:
            sys.exit(0)

    else:
        # Default behavior for backward compatibility or if no command is provided but arguments are present
        # However, since we switched to subparsers, standard argparse behavior is to require a command or show help.
        # But the requirement said: "The current behavior should be converted to 'yasl check <schema> <data>'."
        # If we want to strictly follow that, we enforce using 'check'.
        # If we want to support the old syntax, we'd need to manually parse args or use a trick.
        # Given "convert to", I assume explicit command is preferred.
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
