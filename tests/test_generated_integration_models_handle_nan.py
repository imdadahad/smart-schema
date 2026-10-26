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


@pytest.fixture(scope="session")
def integration_data_dir() -> Path:
    return Path("examples/integration_data")


@pytest.fixture
def product_create_payload(integration_data_dir: Path) -> dict:
    with open(integration_data_dir / "product_api_request.json") as f:
        return json.load(f)


@pytest.fixture
def app_config_payload(integration_data_dir: Path) -> dict:
    with open(integration_data_dir / "app_config.json") as f:
        return json.load(f)


def test_app_config_parses_valid_payload(app_config_payload: dict):
    config = AppConfig(**app_config_payload)
    assert config.application_name == "SmartApp"
    assert config.server_settings.port == 8080
    assert config.debug_mode is True


def test_app_config_rejects_float_nan_on_required_bool(app_config_payload: dict):
    payload = {**app_config_payload, "debug_mode": float("nan")}
    with pytest.raises(ValidationError):
        AppConfig(**payload)


def test_product_create_request_optional_description_nan_becomes_none(
    product_create_payload: dict,
):
    payload = {**product_create_payload, "description": float("nan")}
    product = ProductCreateRequest(**payload)
    assert product.description is None


def test_product_create_request_optional_tags_nan_becomes_none(
    product_create_payload: dict,
):
    payload = {**product_create_payload, "tags": float("nan")}
    product = ProductCreateRequest(**payload)
    assert product.tags is None


def test_product_create_request_rejects_float_nan_on_required_price(
    product_create_payload: dict,
):
    payload = {**product_create_payload, "price": float("nan")}
    with pytest.raises(ValidationError):
        ProductCreateRequest(**payload)


def test_product_create_request_keeps_finite_float_price(
    product_create_payload: dict,
):
    payload = {**product_create_payload, "price": 99.5}
    product = ProductCreateRequest(**payload)
    assert product.price == 99.5
    assert not math.isnan(product.price)


def test_sales_record_parses_finite_float_metrics():
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
    assert record.QuantitySold == 10.0
    assert record.TotalPrice == 12000.0


def test_sales_record_rejects_float_nan_on_required_quantity():
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
