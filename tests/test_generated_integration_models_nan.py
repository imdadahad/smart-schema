"""Behaviour tests for generated integration models' NaN pre-processing."""

import json
import math
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from examples.generated_integration_models.app_config_model import AppConfig
from examples.generated_integration_models.product_create_request_model import (
    ProductCreateRequest,
)
from examples.generated_integration_models.sales_record_model import SalesRecord

INTEGRATION_DATA = Path("examples/integration_data")


@pytest.fixture(scope="session")
def app_config_payload() -> dict:
    with open(INTEGRATION_DATA / "app_config.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def product_create_payload() -> dict:
    with open(INTEGRATION_DATA / "product_api_request.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def sales_record_row() -> dict:
    df = pd.read_csv(INTEGRATION_DATA / "sales_records.csv")
    return df.iloc[0].to_dict()


def test_app_config_accepts_valid_integration_json(app_config_payload):
    config = AppConfig(**app_config_payload)
    assert config.application_name == "SmartApp"
    assert config.version == "1.2.3"
    assert config.debug_mode is True
    assert config.server_settings.port == 8080


def test_app_config_rejects_nan_bool_field(app_config_payload):
    payload = {**app_config_payload, "debug_mode": math.nan}
    with pytest.raises(ValidationError) as exc_info:
        AppConfig(**payload)
    assert exc_info.value.error_count() >= 1


def test_product_create_request_accepts_valid_integration_json(product_create_payload):
    product = ProductCreateRequest(**product_create_payload)
    assert product.product_id == "P008"
    assert product.price == 129.99
    assert product.description.startswith("Mechanical")


def test_product_create_request_maps_nan_optional_description_to_none(
    product_create_payload,
):
    payload = {**product_create_payload, "description": math.nan}
    product = ProductCreateRequest(**payload)
    assert product.description is None


def test_product_create_request_rejects_nan_required_price(product_create_payload):
    payload = {**product_create_payload, "price": math.nan}
    with pytest.raises(ValidationError) as exc_info:
        ProductCreateRequest(**payload)
    assert exc_info.value.error_count() >= 1


def test_sales_record_accepts_valid_csv_row(sales_record_row):
    record = SalesRecord(**sales_record_row)
    assert record.ProductID == "P001"
    assert record.QuantitySold == 10.0
    assert record.Region == "North"


def test_sales_record_rejects_nan_quantity_sold(sales_record_row):
    payload = {**sales_record_row, "QuantitySold": math.nan}
    with pytest.raises(ValidationError) as exc_info:
        SalesRecord(**payload)
    assert exc_info.value.error_count() >= 1


def test_sales_record_preserves_non_nan_float_quantity(sales_record_row):
    payload = {**sales_record_row, "QuantitySold": 10.5}
    record = SalesRecord(**payload)
    assert record.QuantitySold == 10.5
