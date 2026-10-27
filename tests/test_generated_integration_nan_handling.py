"""Behaviour tests for NaN handling on generated integration example models."""

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
def app_config_payload() -> dict:
    with open(INTEGRATION_DATA / "app_config.json") as f:
        return json.load(f)


@pytest.fixture
def product_create_payload() -> dict:
    with open(INTEGRATION_DATA / "product_api_request.json") as f:
        return json.load(f)


def _product_create_minimal(**overrides):
    base = {
        "product_id": "P1",
        "name": "Name",
        "category": "Cat",
        "price": 10.0,
        "stock": 1,
        "description": None,
        "specifications": {
            "switch_type": "Blue",
            "layout": "Full",
            "connectivity": ["USB"],
        },
        "supplier_info": {"supplier_id": "S1", "name": "Supplier"},
        "is_active": True,
        "tags": None,
    }
    base.update(overrides)
    return base


def test_app_config_parses_valid_integration_fixture(app_config_payload):
    config = AppConfig(**app_config_payload)
    assert config.application_name == "SmartApp"
    assert config.debug_mode is True
    assert config.server_settings.port == 8080


def test_app_config_float_nan_at_top_level_raises(app_config_payload):
    app_config_payload["debug_mode"] = float("nan")
    with pytest.raises(ValidationError) as exc_info:
        AppConfig(**app_config_payload)
    assert exc_info.value.errors()[0]["loc"] == ("debug_mode",)


def test_product_create_request_parses_valid_integration_fixture(
    product_create_payload,
):
    product = ProductCreateRequest(**product_create_payload)
    assert product.product_id == "P008"
    assert product.price == pytest.approx(129.99)
    assert product.description.startswith("Mechanical")


def test_product_create_request_nan_optional_description_becomes_none():
    product = ProductCreateRequest(
        **_product_create_minimal(description=float("nan"))
    )
    assert product.description is None


def test_product_create_request_nan_required_price_raises():
    with pytest.raises(ValidationError) as exc_info:
        ProductCreateRequest(**_product_create_minimal(price=float("nan")))
    assert exc_info.value.errors()[0]["loc"] == ("price",)


def test_sales_record_accepts_finite_float_fields():
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
    assert math.isfinite(record.UnitPrice)


def test_sales_record_nan_float_field_raises():
    with pytest.raises(ValidationError) as exc_info:
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
    assert exc_info.value.errors()[0]["loc"] == ("QuantitySold",)
