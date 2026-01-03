import os

from yasl.core import load_schema_files

path = "tests/yasl/repro_order.yasl"
if os.path.exists(path):
    print(f"Testing {path}")
    result = load_schema_files(path)
    if result:
        print("Success")
    else:
        print("Failed")
else:
    print("File not found")
