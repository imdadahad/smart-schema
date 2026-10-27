"""Behaviour tests for generated integration models' pre-parse NaN handling."""

import json
import math
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from examples.generated_integration_models.app_config_model import AppConfig
from examples.generated_integration_models.product_create_request_model import (
    ProductCreateRequest,
)
from examples.generated_integration_models.sales_record_model import SalesRecord

INTEGRATION_DATA = Path("examples/integration_data")


@pytest.fixture
def app_config_dict():
    return json.loads((INTEGRATION_DATA / "app_config.json").read_text())


@pytest.fixture
def product_create_dict():
    return json.loads((INTEGRATION_DATA / "product_api_request.json").read_text())


def test_app_config_parses_valid_fixture(app_config_dict):
    config = AppConfig(**app_config_dict)
    assert config.application_name == "SmartApp"
    assert config.server_settings.port == 8080


def test_app_config_nan_in_nested_numeric_field_raises(app_config_dict):
    payload = dict(app_config_dict)
    payload["server_settings"] = dict(
        app_config_dict["server_settings"], port=float("nan")
    )
    with pytest.raises(ValidationError):
        AppConfig(**payload)


def test_product_create_request_nan_optional_description_becomes_none(
    product_create_dict,
):
    payload = dict(product_create_dict, description=float("nan"))
    model = ProductCreateRequest(**payload)
    assert model.description is None
    assert model.price == product_create_dict["price"]


def test_product_create_request_nan_required_price_raises(product_create_dict):
    payload = dict(product_create_dict, price=float("nan"))
    with pytest.raises(ValidationError):
        ProductCreateRequest(**payload)


def test_product_create_request_non_nan_float_price_unchanged(product_create_dict):
    model = ProductCreateRequest(**product_create_dict)
    assert model.price == pytest.approx(129.99)
    assert not math.isnan(model.price)


def test_sales_record_nan_required_float_field_raises():
    with pytest.raises(ValidationError):
        SalesRecord(
            Date=datetime(2024, 7, 1),
            ProductID="P001",
            ProductName="Laptop Pro",
            Category="Electronics",
            QuantitySold=float("nan"),
            UnitPrice=1200.0,
            TotalPrice=12000.0,
            Region="North",
        )


def test_sales_record_numeric_fields_accept_finite_floats():
    record = SalesRecord(
        Date=datetime(2024, 7, 1),
        ProductID="P001",
        ProductName="Laptop Pro",
        Category="Electronics",
        QuantitySold=10.0,
        UnitPrice=1200.0,
        TotalPrice=12000.0,
        Region="North",
    )
    assert record.QuantitySold == pytest.approx(10.0)
    assert record.UnitPrice == pytest.approx(1200.0)
    assert record.TotalPrice == pytest.approx(12000.0)
