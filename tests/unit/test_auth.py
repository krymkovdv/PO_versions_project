# tests/unit/test_auth.py
import pytest
from unittest.mock import MagicMock, patch
from app.authorization import authenticate_user, create_access_token, verify_password, get_password_hash
from app.models import UserDB

def test_verify_password():
    plain = "password123"
    hashed = get_password_hash(plain)

    assert verify_password(plain, hashed) is True
    assert verify_password("wrong", hashed) is False

def test_verify_password_false():
    plain = "password123"
    wrong_plain = "wrongpass"
    hashed = get_password_hash(plain)

    assert verify_password(wrong_plain, hashed) is False

def test_get_password_hash():
    password = "password123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    assert hash1 != hash2  # Хэши должны быть разными из-за соли
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True

def test_create_access_token():
    data = {"sub": "testuser", "role": "user"}
    token = create_access_token(data)

    assert isinstance(token, str)
    assert len(token) > 0

def test_authenticate_user_success():
    mock_db = MagicMock()
    user = UserDB(id=1, username="testuser", password_hash=get_password_hash("password"), role="user")
    mock_db.query.return_value.filter.return_value.first.return_value = user

    result = authenticate_user(mock_db, "testuser", "password")

    assert result is not None
    assert result.username == "testuser"

def test_authenticate_user_wrong_password():
    mock_db = MagicMock()
    user = UserDB(id=1, username="testuser", password_hash=get_password_hash("password"), role="user")
    mock_db.query.return_value.filter.return_value.first.return_value = user

    result = authenticate_user(mock_db, "testuser", "wrongpass")

    assert result is False  # ✅ authenticate_user возвращает False, если пароль неверный

def test_authenticate_user_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = authenticate_user(mock_db, "nonexistent", "password")

    assert result is False  # ✅ authenticate_user возвращает False, если пользователь не найден

def test_authenticate_user_exception():
    mock_db = MagicMock()
    mock_db.query.side_effect = Exception("DB Connection Failed")

    from app.authorization import authenticate_user

    result = authenticate_user(mock_db, "testuser", "password")

    assert result is False  


def test_verify_password_false():
    plain = "password123"
    wrong_plain = "wrongpass"
    hashed = get_password_hash(plain)

    assert verify_password(wrong_plain, hashed) is False

def test_get_password_hash():
    password = "password123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    assert hash1 != hash2  # Хэши должны быть разными из-за соли
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True

def test_create_access_token():
    data = {"sub": "testuser", "role": "user"}
    token = create_access_token(data)

    assert isinstance(token, str)
    assert len(token) > 0

def test_authenticate_user_success():
    mock_db = MagicMock()
    user = UserDB(id=1, username="testuser", password_hash=get_password_hash("password"), role="user")
    mock_db.query.return_value.filter.return_value.first.return_value = user

    result = authenticate_user(mock_db, "testuser", "password")

    assert result is not None
    assert result.username == "testuser"

def test_authenticate_user_wrong_password():
    mock_db = MagicMock()
    user = UserDB(id=1, username="testuser", password_hash=get_password_hash("password"), role="user")
    mock_db.query.return_value.filter.return_value.first.return_value = user

    result = authenticate_user(mock_db, "testuser", "wrongpass")

    assert result is False  # ✅ authenticate_user возвращает False, если пароль неверный

def test_authenticate_user_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = authenticate_user(mock_db, "nonexistent", "password")

    assert result is False  # ✅ authenticate_user возвращает False, если пользователь не найден

# --- Тесты для оставшихся строк в authorization.py (охват 45-67, 70-77) ---

def test_authenticate_user_exception():
    mock_db = MagicMock()
    mock_db.query.side_effect = Exception("DB Connection Failed")

    from app.authorization import authenticate_user

    result = authenticate_user(mock_db, "testuser", "password")

    assert result is False  # или None, в зависимости от логики