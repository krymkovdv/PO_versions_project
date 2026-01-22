# tests/unit/test_schemas.py
import pytest
from pydantic import ValidationError
from app.schemas import TractorsSchema, UserCreate, SoftwareSchema

def test_tractors_schema_valid():
    data = {
        "model": "K-7",
        "vin": "TEST123",
        "oh_hour": 100,
        "region": "RU-MOS",
        "consumer": "Dealer A",
        "serv_center": "Center 1"
    }
    schema = TractorsSchema(**data)
    assert schema.model == "K-7"

def test_tractors_schema_missing_field():
    data = {
        "model": "K-7",
        "vin": "TEST123",
        "oh_hour": 100,
        # missing required fields
    }
    with pytest.raises(ValidationError):
        TractorsSchema(**data)

def test_user_create_valid():
    data = {
        "username": "testuser",
        "password": "pass123",
        "role": "moderator"
    }
    schema = UserCreate(**data)
    assert schema.username == "testuser"

def test_user_create_invalid_role():
    data = {
        "username": "testuser",
        "password": "pass123",
        "role": "invalid_role"
    }
    with pytest.raises(ValidationError):
        UserCreate(**data)

def test_software_schema_valid():
    data = {
        "path": "sw.bin",
        "name": "MySW",
        "inner_name": "Inner",
        "release_date": "2024-01-01T00:00:00",
        "description": "A software"
    }
    schema = SoftwareSchema(**data)
    assert schema.name == "MySW"

def test_tractors_schema_validation_error():
    from app.schemas import TractorsSchema
    from pydantic import ValidationError

    incomplete_data = {
        "model": "K-7",
        "vin": "TEST123"
        # missing oh_hour, region, consumer, serv_center
    }

    with pytest.raises(ValidationError):
        TractorsSchema(**incomplete_data)