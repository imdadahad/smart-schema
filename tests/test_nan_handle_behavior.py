"""Behavior tests for pre-parse NaN handling on generated and utility models."""

import copy
import json
import math
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from examples.generated_integration_models.app_config_model import AppConfig
from examples.generated_integration_models.product_create_request_model import (
    ProductCreateRequest,
)
from examples.generated_integration_models.sales_record_model import SalesRecord
from smart_schema.core import model_utils
from tests.data.test_model import TestModel

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples" / "integration_data"


def _product_create_payload() -> dict:
    with open(EXAMPLES_DIR / "product_api_request.json") as f:
        return json.load(f)


def _app_config_payload() -> dict:
    with open(EXAMPLES_DIR / "app_config.json") as f:
        return json.load(f)


def _sales_record_kwargs() -> dict:
    row = pd.read_csv(EXAMPLES_DIR / "sales_records.csv", nrows=1).iloc[0]
    return {
        "Date": pd.Timestamp(row["Date"]).to_pydatetime(),
        "ProductID": row["ProductID"],
        "ProductName": row["ProductName"],
        "Category": row["Category"],
        "QuantitySold": float(row["QuantitySold"]),
        "UnitPrice": float(row["UnitPrice"]),
        "TotalPrice": float(row["TotalPrice"]),
        "Region": row["Region"],
    }


def test_test_model_optional_field_nan_becomes_none():
    instance = TestModel(a=1, b=float("nan"))
    assert instance.a == 1
    assert instance.b is None


def test_test_model_required_field_nan_raises_validation_error():
    with pytest.raises(ValidationError):
        TestModel(a=float("nan"))


def test_generate_pydantic_model_handle_nan_converts_float_nan():
    schema = {
        "value": {"type": float, "is_nullable": True, "default": None},
    }
    model = model_utils.generate_pydantic_model(schema, "NanUtilityModel")
    assert model.handle_nan(float("nan")) is None
    assert model.handle_nan(2.5) == 2.5


def test_generate_pydantic_model_optional_float_nan_persists_on_validation():
    schema = {
        "value": {"type": float, "is_nullable": True, "default": None},
    }
    model = model_utils.generate_pydantic_model(schema, "NanUtilityModel")
    instance = model(value=float("nan"))
    assert instance.value is not None
    assert math.isnan(instance.value)


def test_product_create_request_optional_nan_fields_become_none():
    payload = _product_create_payload()
    payload["description"] = float("nan")
    payload["tags"] = float("nan")
    instance = ProductCreateRequest(**payload)
    assert instance.description is None
    assert instance.tags is None


def test_sales_record_required_float_nan_raises_validation_error():
    kwargs = _sales_record_kwargs()
    kwargs["QuantitySold"] = float("nan")
    with pytest.raises(ValidationError):
        SalesRecord(**kwargs)


def test_sales_record_valid_row_parses():
    instance = SalesRecord(**_sales_record_kwargs())
    assert instance.QuantitySold == 10.0
    assert instance.ProductID == "P001"


def test_app_config_nested_required_int_nan_raises_validation_error():
    payload = copy.deepcopy(_app_config_payload())
    payload["server_settings"]["port"] = float("nan")
    with pytest.raises(ValidationError):
        AppConfig(**payload)


def test_app_config_valid_payload_parses():
    instance = AppConfig(**_app_config_payload())
    assert instance.application_name == "SmartApp"
    assert instance.server_settings.port == 8080
