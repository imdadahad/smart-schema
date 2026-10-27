import importlib.util
import json
import math
from pathlib import Path

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_MODELS_DIR = REPO_ROOT / "examples" / "generated_integration_models"
INTEGRATION_DATA_DIR = REPO_ROOT / "examples" / "integration_data"


def _load_model_module(module_filename: str, module_name: str):
    path = INTEGRATION_MODELS_DIR / module_filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def app_config_model():
    return _load_model_module("app_config_model.py", "app_config_model")


@pytest.fixture(scope="module")
def product_create_request_model():
    return _load_model_module("product_create_request_model.py", "product_create_request_model")


@pytest.fixture(scope="module")
def sales_record_model():
    return _load_model_module("sales_record_model.py", "sales_record_model")


@pytest.fixture(scope="module")
def app_config_example() -> dict:
    return json.loads((INTEGRATION_DATA_DIR / "app_config.json").read_text())


@pytest.fixture(scope="module")
def product_create_request_example() -> dict:
    return json.loads((INTEGRATION_DATA_DIR / "product_api_request.json").read_text())


def test_app_config_accepts_integration_example(app_config_model, app_config_example):
    config = app_config_model.AppConfig(**app_config_example)

    assert config.application_name == "SmartApp"
    assert config.server_settings.port == 8080
    assert config.database_connection.connection_options.max_connections == 100


def test_app_config_nan_string_field_coerced_to_none_before_validation(
    app_config_model, app_config_example
):
    payload = json.loads(json.dumps(app_config_example))
    payload["version"] = float("nan")

    with pytest.raises(ValidationError) as exc_info:
        app_config_model.AppConfig(**payload)

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("version",)
    assert errors[0]["type"] == "string_type"
    assert errors[0]["input"] is None


def test_app_config_nan_bool_field_coerced_to_none_before_validation(
    app_config_model, app_config_example
):
    payload = json.loads(json.dumps(app_config_example))
    payload["debug_mode"] = float("nan")

    with pytest.raises(ValidationError) as exc_info:
        app_config_model.AppConfig(**payload)

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("debug_mode",)
    assert errors[0]["type"] == "bool_type"
    assert errors[0]["input"] is None


def test_product_create_request_accepts_integration_example(
    product_create_request_model, product_create_request_example
):
    product = product_create_request_model.ProductCreateRequest(**product_create_request_example)

    assert product.product_id == "P008"
    assert product.price == pytest.approx(129.99)
    assert product.specifications.connectivity == ["USB-C", "Bluetooth"]


def test_product_create_request_nan_optional_fields_become_none(
    product_create_request_model, product_create_request_example
):
    payload = json.loads(json.dumps(product_create_request_example))
    payload["description"] = float("nan")
    payload["tags"] = float("nan")

    product = product_create_request_model.ProductCreateRequest(**payload)

    assert product.description is None
    assert product.tags is None


def test_product_create_request_nan_required_float_fails_validation(
    product_create_request_model, product_create_request_example
):
    payload = json.loads(json.dumps(product_create_request_example))
    payload["price"] = float("nan")

    with pytest.raises(ValidationError) as exc_info:
        product_create_request_model.ProductCreateRequest(**payload)

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("price",)
    assert errors[0]["type"] == "float_type"
    assert errors[0]["input"] is None


def test_sales_record_accepts_valid_numeric_fields(sales_record_model):
    record = sales_record_model.SalesRecord(
        Date="2024-07-01",
        ProductID="P001",
        ProductName="Laptop Pro",
        Category="Electronics",
        QuantitySold=10.0,
        UnitPrice=1200.0,
        TotalPrice=12000.0,
        Region="North",
    )

    assert record.QuantitySold == pytest.approx(10.0)
    assert record.TotalPrice == pytest.approx(12000.0)


def test_sales_record_finite_floats_are_not_altered(sales_record_model):
    record = sales_record_model.SalesRecord(
        Date="2024-07-01",
        ProductID="P001",
        ProductName="Laptop Pro",
        Category="Electronics",
        QuantitySold=0.5,
        UnitPrice=1200.0,
        TotalPrice=600.0,
        Region="North",
    )

    assert math.isfinite(record.QuantitySold)
    assert record.QuantitySold == pytest.approx(0.5)


def test_sales_record_nan_float_field_coerced_to_none_before_validation(sales_record_model):
    with pytest.raises(ValidationError) as exc_info:
        sales_record_model.SalesRecord(
            Date="2024-07-01",
            ProductID="P001",
            ProductName="Laptop Pro",
            Category="Electronics",
            QuantitySold=float("nan"),
            UnitPrice=1200.0,
            TotalPrice=12000.0,
            Region="North",
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("QuantitySold",)
    assert errors[0]["type"] == "float_type"
    assert errors[0]["input"] is None
