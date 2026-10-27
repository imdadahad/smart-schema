"""Behaviour tests for generated integration models that normalize float NaN inputs."""

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

INTEGRATION_DATA = Path("examples/integration_data")


@pytest.fixture
def app_config_payload() -> dict:
    return json.loads((INTEGRATION_DATA / "app_config.json").read_text())


@pytest.fixture
def product_create_payload() -> dict:
    return json.loads((INTEGRATION_DATA / "product_api_request.json").read_text())


def test_app_config_accepts_valid_integration_payload(app_config_payload):
    config = AppConfig(**app_config_payload)

    assert config.application_name == "SmartApp"
    assert config.server_settings.port == 8080
    assert config.debug_mode is True


def test_app_config_nan_top_level_field_is_treated_as_missing(app_config_payload):
    app_config_payload["version"] = math.nan

    with pytest.raises(ValidationError) as exc_info:
        AppConfig(**app_config_payload)

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("version",)
    assert errors[0]["input"] is None


def test_product_create_request_accepts_valid_integration_payload(
    product_create_payload,
):
    product = ProductCreateRequest(**product_create_payload)

    assert product.product_id == "P008"
    assert product.price == 129.99
    assert product.description.startswith("Mechanical gaming keyboard")


def test_product_create_request_nan_optional_description_becomes_none(
    product_create_payload,
):
    product_create_payload["description"] = math.nan

    product = ProductCreateRequest(**product_create_payload)

    assert product.description is None


def test_product_create_request_nan_optional_tags_becomes_none(product_create_payload):
    product_create_payload["tags"] = math.nan

    product = ProductCreateRequest(**product_create_payload)

    assert product.tags is None


def test_product_create_request_nan_required_price_rejected(product_create_payload):
    product_create_payload["price"] = math.nan

    with pytest.raises(ValidationError) as exc_info:
        ProductCreateRequest(**product_create_payload)

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("price",)
    assert errors[0]["input"] is None


def test_sales_record_accepts_finite_float_metrics():
    record = SalesRecord(
        Date="2024-07-01",
        ProductID="P001",
        ProductName="Laptop Pro",
        Category="Electronics",
        QuantitySold=10.0,
        UnitPrice=1200.0,
        TotalPrice=12000.0,
        Region="North",
    )

    assert record.QuantitySold == 10.0
    assert record.UnitPrice == 1200.0


def test_sales_record_nan_quantity_sold_rejected():
    with pytest.raises(ValidationError) as exc_info:
        SalesRecord(
            Date="2024-07-01",
            ProductID="P001",
            ProductName="Laptop Pro",
            Category="Electronics",
            QuantitySold=math.nan,
            UnitPrice=1200.0,
            TotalPrice=12000.0,
            Region="North",
        )

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("QuantitySold",)
    assert errors[0]["input"] is None


def test_sales_record_non_float_input_unchanged_for_strings():
    record = SalesRecord(
        Date="2024-07-02",
        ProductID="P002",
        ProductName="Wireless Mouse",
        Category="Accessories",
        QuantitySold=50,
        UnitPrice=25.5,
        TotalPrice=1275.0,
        Region="West",
    )

    assert record.ProductName == "Wireless Mouse"
    assert record.QuantitySold == 50
