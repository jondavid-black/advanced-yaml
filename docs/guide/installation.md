# Installation

## Prerequisites

**Advanced YAML** requires Python **3.12** or greater. Please ensure you have a compatible version of Python installed on your system before proceeding.

You can check your current python version with:

```bash
python --version
```

## Installing from PyPI

Advanced YAML is published on the Python Package Index (PyPI) and can be installed using standard Python tooling.

### Using pip

To install using the standard `pip` package manager:

```bash
pip install advanced-yaml
```

### Using Poetry

If you are managing your project with [Poetry](https://python-poetry.org/):

```bash
poetry add advanced-yaml
```

### Using uv

If you are using [uv](https://github.com/astral-sh/uv) for fast package management:

```bash
uv add advanced-yaml
```

## Verification

Once installed, you can verify that the CLI tools are available in your path:

```bash
yasl --version
yaql --version
```
