from importlib.metadata import PackageNotFoundError, version


def advanced_yaml_version() -> str:
    try:
        return version("advanced-yaml")
    except PackageNotFoundError:
        return "Unknown (package not installed)"
