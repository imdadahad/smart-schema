import importlib.util
import json
import math
from pathlib import Path

import pytest
from pydantic import ValidationError

from examples.generated_integration_models.app_config_model import AppConfig
from examples.generated_integration_models.product_create_request_model import (
    ProductCreateRequest,
)
from examples.generated_integration_models.sales_record_model import SalesRecord
from smart_schema.core import model_utils

EXAMPLES_DIR = Path("examples/integration_data")


@pytest.fixture
def app_config_payload() -> dict:
    return json.loads((EXAMPLES_DIR / "app_config.json").read_text())


@pytest.fixture
def product_create_payload() -> dict:
    return json.loads((EXAMPLES_DIR / "product_api_request.json").read_text())


@pytest.fixture
def sales_record_payload() -> dict:
    return {
        "Date": "2024-07-01",
        "ProductID": "P001",
        "ProductName": "Laptop Pro",
        "Category": "Electronics",
        "QuantitySold": 10.0,
        "UnitPrice": 1200.0,
        "TotalPrice": 12000.0,
        "Region": "North",
    }


def _load_test_data_model_class():
    module_path = Path(__file__).parent / "data" / "test_model.py"
    spec = importlib.util.spec_from_file_location(
        "smart_schema_tests_data_test_model", module_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.TestModel


def test_app_config_converts_float_nan_to_none_before_bool_coercion(
    app_config_payload,
):
    payload = {**app_config_payload, "debug_mode": float("nan")}
    with pytest.raises(ValidationError) as exc_info:
        AppConfig(**payload)
    assert exc_info.value.errors()[0]["loc"] == ("debug_mode",)
    assert exc_info.value.errors()[0]["input"] is None


def test_product_create_request_accepts_nan_on_optional_description(
    product_create_payload,
):
    payload = {**product_create_payload, "description": float("nan")}
    instance = ProductCreateRequest(**payload)
    assert instance.description is None


def test_sales_record_rejects_nan_on_required_float_field(sales_record_payload):
    payload = {**sales_record_payload, "QuantitySold": float("nan")}
    with pytest.raises(ValidationError) as exc_info:
        SalesRecord(**payload)
    assert exc_info.value.errors()[0]["loc"] == ("QuantitySold",)
    assert exc_info.value.errors()[0]["input"] is None


def test_generate_pydantic_model_handle_nan_converts_float_nan():
    schema = {
        "value": {"type": float, "is_nullable": True, "description": "nullable float"},
    }
    model = model_utils.generate_pydantic_model(schema, "NanSchemaModel")
    assert model.handle_nan(float("nan")) is None
    assert model.handle_nan(2.5) == 2.5


def test_generate_pydantic_model_keeps_float_nan_on_nullable_field_instance():
    schema = {
        "value": {"type": float, "is_nullable": True, "description": "nullable float"},
    }
    model = model_utils.generate_pydantic_model(schema, "NanInstanceModel")
    instance = model(value=float("nan"))
    assert isinstance(instance.value, float)
    assert math.isnan(instance.value)


def test_test_data_model_converts_nan_on_optional_string_field():
    test_model = _load_test_data_model_class()
    instance = test_model(a=1, b=float("nan"))
    assert instance.b is None


def test_test_data_model_rejects_nan_on_required_int_field():
    test_model = _load_test_data_model_class()
    with pytest.raises(ValidationError) as exc_info:
        test_model(a=float("nan"))
    assert exc_info.value.errors()[0]["loc"] == ("a",)
    assert exc_info.value.errors()[0]["input"] is None
