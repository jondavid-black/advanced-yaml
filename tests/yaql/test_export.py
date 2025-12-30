import shutil
from pathlib import Path

from yaql.engine import export_data, load_data, load_schema


def test_export_data():
    # Setup paths
    base_dir = Path("tests/yaql/export_test_data")
    if base_dir.exists():
        shutil.rmtree(base_dir)
    base_dir.mkdir(parents=True)

    schema_dir = base_dir / "schemas"
    schema_dir.mkdir()
    data_dir = base_dir / "data"
    data_dir.mkdir()
    export_dir = base_dir / "export"

    # 1. Create a Schema with Nested Types
    # Parent: Order
    # Child: Item (Nested in Order)

    schema_content = """
definitions:
  test.store:
    types:
      Address:
        properties:
          street:
            type: str
          city:
            type: str

      Item:
        properties:
          name:
            type: str
            presence: required
          price:
            type: float
            presence: required

      Order:
        properties:
          oid:
            type: int
            presence: required
          customer:
            type: str
          billing_address:
             type: test.store.Address
          items:
            type: test.store.Item[]
"""
    (schema_dir / "store.yasl").write_text(schema_content)

    # 2. Create Data
    data_content = """
oid: 101
customer: "Alice"
billing_address:
  street: "123 Main St"
  city: "Wonderland"
items:
  - name: "Apple"
    price: 0.50
  - name: "Banana"
    price: 0.30
"""
    (data_dir / "order_101.yaml").write_text(data_content)

    # 3. Load Schema and Data
    assert load_schema(str(schema_dir))
    assert load_data(str(data_dir)) == 1  # 1 Order loaded

    # 4. Export Data
    count = export_data(str(export_dir))

    # 5. Verify Export
    # We expect:
    # export_dir/test.store/Order_1.yaml
    # Item should NOT exist as separate file
    # Address should NOT exist as separate file (it is nested)

    assert count == 1

    order_file = export_dir / "test.store" / "Order_1.yaml"
    assert order_file.exists()

    # Check contents
    from ruamel.yaml import YAML

    yaml = YAML()
    with open(order_file) as f:
        data = yaml.load(f)

    assert data["customer"] == "Alice"
    assert len(data["items"]) == 2
    assert data["billing_address"]["city"] == "Wonderland"

    # Ensure Item/Address files are NOT created
    item_files = list((export_dir / "test.store").glob("Item_*.yaml"))
    assert len(item_files) == 0

    address_files = list((export_dir / "test.store").glob("Address_*.yaml"))
    assert len(address_files) == 0

    # Cleanup
    shutil.rmtree(base_dir)


def test_export_data_min_mode():
    # Setup paths
    base_dir = Path("tests/yaql/export_test_min_mode")
    if base_dir.exists():
        shutil.rmtree(base_dir)
    base_dir.mkdir(parents=True)

    schema_dir = base_dir / "schemas"
    schema_dir.mkdir()
    data_dir = base_dir / "data"
    data_dir.mkdir()
    export_dir = base_dir / "export"

    # 1. Create Schema
    schema_content = """
definitions:
  test.min:
    types:
      Product:
        properties:
          sku:
            type: str
          name:
            type: str
"""
    (schema_dir / "products.yasl").write_text(schema_content)

    # 2. Create Multiple Data Files for Product
    (data_dir / "p1.yaml").write_text("sku: 'A001'\nname: 'Widget A'")
    (data_dir / "p2.yaml").write_text("sku: 'B002'\nname: 'Widget B'")

    # 3. Load Schema and Data
    assert load_schema(str(schema_dir))
    assert load_data(str(data_dir)) == 2

    # 4. Export Data in Min Mode
    count = export_data(str(export_dir), min_mode=True)

    # 5. Verify Export
    # We expect:
    # export_dir/test.min/Product.yaml (One file!)
    # It should contain two documents separated by ---

    assert count == 1  # 1 file written (Product.yaml)

    product_file = export_dir / "test.min" / "Product.yaml"
    assert product_file.exists()

    # Check contents
    from ruamel.yaml import YAML

    yaml = YAML()
    with open(product_file) as f:
        docs = list(yaml.load_all(f))

    assert len(docs) == 2
    names = {d["name"] for d in docs}
    assert "Widget A" in names
    assert "Widget B" in names

    # Cleanup
    shutil.rmtree(base_dir)
