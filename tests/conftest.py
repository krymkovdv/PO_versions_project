# tests/conftest.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.main import app as original_app

@pytest.fixture(scope="function", autouse=True)
def setup_mocks():
    # Мокаем require_role на уровне модуля routes
    with patch('app.routes.require_role', return_value=lambda: True):
        yield

@pytest.fixture(scope="function")
def client(setup_mocks):
    # Создаём TestClient для оригинального приложения
    # Это сработает, потому что setup_mocks мокает require_role до вызова эндпоинтов
    with TestClient(original_app) as c:
        yield c