# tests/unit/test_routes.py
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock
from app.models import Tractors
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock, Mock
from app.models import Tractors, Software, ComponentParts, Software2ComponentPart, TelemetryComponents
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock
from app.models import Tractors, Software, ComponentParts, Software2ComponentPart, TelemetryComponents
from unittest.mock import ANY
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

def test_get_users(client):  # ✅ Принимаем client как параметр
    with patch('app.CRUDs.get_users', return_value=[]) as mock_crud:
        response = client.get("/users/")
        assert response.status_code == 200
        mock_crud.assert_called_once()

def test_login_for_access_token(client):  # ✅ Принимаем client как параметр
    # Мокаем authenticate_user в routes.py, а не в authorization.py
    with patch('app.routes.authenticate_user') as mock_auth:
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.role = "user"
        mock_auth.return_value = mock_user

        with patch('app.routes.create_access_token', return_value="fake-token"):
            response = client.post("/token/", data={"username": "testuser", "password": "password"})

            assert response.status_code == 200
            assert "access_token" in response.json()

def test_get_tractors(client):  # ✅ Принимаем client как параметр
    with patch('app.CRUDs.get_tractors', return_value=[]) as mock_crud:
        response = client.get("/tractors/")
        assert response.status_code == 200
        mock_crud.assert_called_once()

def test_create_tractor_success(client):  # ✅ Принимаем client как параметр
    tractor_data = {
        "model": "K-7",
        "vin": "TEST123",
        "oh_hour": 100,
        "last_activity": "2024-11-20T10:00:00",
        "assembly_date": "2024-05-10T10:00:00",
        "region": "RU-MOS",
        "consumer": "Dealer A",
        "serv_center": "Center 1"
    }

    with patch('app.CRUDs.create_tractor', return_value=tractor_data) as mock_crud:
        response = client.post("/tractors/", json=tractor_data)

        assert response.status_code == 201
        mock_crud.assert_called_once()

def test_create_tractor_duplicate_vin(client):  # ✅ Принимаем client как параметр
    tractor_data = {
        "model": "K-7",
        "vin": "EXISTING_VIN",
        "oh_hour": 100,
        "last_activity": "2024-11-20T10:00:00",
        "assembly_date": "2024-05-10T10:00:00",
        "region": "RU-MOS",
        "consumer": "Dealer A",
        "serv_center": "Center 1"
    }

    # Имитируем, что в БД уже есть такой vin
    with patch('app.models.Tractors') as MockTractor:
        instance = MockTractor.return_value
        instance.vin = "EXISTING_VIN"

        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = instance

            response = client.post("/tractors/", json=tractor_data)

            assert response.status_code == 400
            assert "already exists" in response.json()["detail"]


# tests/unit/test_routes.py


# ... существующие тесты ...

# --- Новые тесты для routes (исправленные) ---

def test_get_software(client):
    with patch('app.CRUDs.get_software', return_value=[]) as mock_crud:
        response = client.get("/software/")
        assert response.status_code == 200
        mock_crud.assert_called_once()

def test_create_software(client):
    sw_data = {
        "path": "new.bin",
        "name": "NewSW",
        "inner_name": "NewInner",
        "release_date": "2024-01-01T00:00:00",
        "description": "A new software"
    }

    with patch('app.CRUDs.create_software', return_value=sw_data) as mock_crud:
        response = client.post("/software/", json=sw_data)

        assert response.status_code == 201
        mock_crud.assert_called_once()

def test_delete_software(client):
    with patch('app.CRUDs.delete_software', return_value=True) as mock_crud:
        response = client.delete("/software/1")
        assert response.status_code == 204
        # ✅ Исправлено: используем ANY для первого аргумента (db)
        mock_crud.assert_called_once_with(ANY, 1)

def test_get_component_parts(client):
    with patch('app.CRUDs.get_component_parts', return_value=[]) as mock_crud:
        response = client.get("/component-parts/")
        assert response.status_code == 200
        mock_crud.assert_called_once()

def test_create_component_part(client):
    part_data = {
        "component": 1,
        "part_type": "main"
    }

    # ✅ Мокаем CRUD, чтобы не вызывать проверку в routes.py
    with patch('app.CRUDs.create_component_part', return_value=part_data) as mock_crud:
        response = client.post("/component-parts/", json=part_data)

        assert response.status_code == 201
        mock_crud.assert_called_once()

def test_delete_component_part(client):
    with patch('app.CRUDs.delete_component_part', return_value=True) as mock_crud:
        response = client.delete("/component-parts/1")
        assert response.status_code == 204
        # ✅ Исправлено: используем ANY для первого аргумента (db)
        mock_crud.assert_called_once_with(ANY, 1)

def test_get_software_component_links(client):
    with patch('app.CRUDs.get_software_component_parts', return_value=[]) as mock_crud:
        response = client.get("/software-component-links/")
        assert response.status_code == 200
        mock_crud.assert_called_once()

def test_create_software_component_link(client):
    link_data = {
        "component_part_id": 1,
        "software_id": 1,
        "is_major": False,
        "status": "s"
    }

    with patch('app.CRUDs.create_software_component_part', return_value=link_data) as mock_crud:
        response = client.post("/software-component-links/", json=link_data)

        assert response.status_code == 201
        mock_crud.assert_called_once()

def test_create_software_component_link_sqlalchemy_error(client):
    link_data = {
        "component_part_id": 1,
        "software_id": 1,
        "is_major": False,
        "status": "s"
    }

    with patch('app.CRUDs.create_software_component_part', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/software-component-links/", json=link_data)
        assert response.status_code == 500

def test_delete_software_component_link(client):
    with patch('app.CRUDs.delete_software_component_part', return_value=True) as mock_crud:
        response = client.delete("/software-component-links/1")
        assert response.status_code == 204
        # ✅ Исправлено: используем ANY для первого аргумента (db)
        mock_crud.assert_called_once_with(ANY, 1)

def test_get_telemetry_components(client):
    with patch('app.CRUDs.get_telemetry_components', return_value=[]) as mock_crud:
        response = client.get("/telemetry-components/")
        assert response.status_code == 200
        mock_crud.assert_called_once()

def test_create_telemetry_component(client):
    tel_data = {
        "tractor": 1,
        "component": 1,
        "mounting_date": "2024-01-01",
        "current_sw_version": 1,
        "recommend_sw_version": 2
    }

    with patch('app.CRUDs.create_telemetry_component', return_value=tel_data) as mock_crud:
        response = client.post("/telemetry-components/", json=tel_data)

        assert response.status_code == 201
        mock_crud.assert_called_once()

def test_delete_telemetry_component(client):
    with patch('app.CRUDs.delete_telemetry_component', return_value=True) as mock_crud:
        response = client.delete("/telemetry-components/1")
        assert response.status_code == 204
        # ✅ Исправлено: используем ANY для первого аргумента (db)
        mock_crud.assert_called_once_with(ANY, 1)

def test_get_component_info(client):
    filters = {
        "trac_model": [],
        "type_comp": [],
        "model_comp": []
    }

    with patch('app.CRUDs.get_component_by_filters', return_value=[]) as mock_crud:
        response = client.post("/component-info", json=filters)
        assert response.status_code == 200
        mock_crud.assert_called_once()

def test_search_component(client):
    with patch('app.CRUDs.search_components', return_value=[]) as mock_crud:
        response = client.get("/search-component", params={"query": "engine"})
        assert response.status_code == 200
        mock_crud.assert_called_once()

def test_get_tractors_by_filters(client):
    filters = {
        "trac_model": ["K-7"],
        "status": [],
        "dealer": "",
        "date_assemle": None
    }

    with patch('app.CRUDs.get_tractors_by_filters', return_value=[]) as mock_crud:
        response = client.post("/tractor-info", json=filters)
        assert response.status_code == 200
        mock_crud.assert_called_once()

def test_search_tractor(client):
    with patch('app.CRUDs.search_tractors', return_value=[]) as mock_crud:
        response = client.get("/search-tractor", params={"request": "K-7"})
        assert response.status_code == 200
        mock_crud.assert_called_once()

def test_search_tractor_vin(client):
    with patch('app.CRUDs.get_tractor_by_vin', return_value=[]) as mock_crud:
        response = client.get("/search-tractor-vin", params={"request": "VIN1"})
        assert response.status_code == 200
        mock_crud.assert_called_once()


def test_assign_software_to_components(client):
    from io import BytesIO
    from fastapi import UploadFile

    file_content = b"fake binary content"
    file = UploadFile(filename="test.bin", file=BytesIO(file_content))

    # ✅ Возвращаем правильную модель
    return_data = {
        "id": 1,
        "name": "TestSW",
        "is_major": True,
        "inner_name": "Inner",
        "component_models": ["Model1"],
        "part_type": ["Type1"],
        "download_url": "/software/download/1"
    }

    with patch('app.CRUDs.assign_software_to_components', return_value=return_data) as mock_assign:
        response = client.post(
            "/software/assign",
            data={
                "name": "TestSW",
                "is_major": "true",
                "inner_name": "Inner",
                "component_models": "Model1",
                "part_type": "Type1"
            },
            files={"file": (file.filename, file.file, "application/octet-stream")}
        )

        assert response.status_code == 201

def test_download_software_file(client):
    from unittest.mock import mock_open
    import tempfile
    import os

    mock_metadata = Mock()
    mock_metadata.filename_for_download = "sw.bin"

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"fake file content")
        temp_path = tmp.name

    try:
        with patch('app.CRUDs.get_software_metadata', return_value=mock_metadata):
            with patch('app.CRUDs.get_software_file_path', return_value=temp_path):
                response = client.get("/software/download/1")
                assert response.status_code == 200
    finally:
        os.unlink(temp_path)


def test_search_tractors_value_error(client):
    with patch('app.CRUDs.search_tractors', side_effect=ValueError("Bad regex")):
        response = client.get("/search-tractor", params={"request": "***"})  # плохой regex

        assert response.status_code == 400
        assert "Bad regex" in response.json()["detail"]

def test_create_software_sqlalchemy_error(client):
    sw_data = {
        "path": "new.bin",
        "name": "NewSW",
        "inner_name": "NewInner",
        "release_date": "2024-01-01T00:00:00",
        "description": "A new software"
    }

    with patch('app.CRUDs.create_software', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/software/", json=sw_data)

        assert response.status_code == 500
        assert "Ошибка базы данных" in response.json()["detail"]

def test_get_tractors_sqlalchemy_error(client):
    with patch('app.CRUDs.get_tractors', side_effect=SQLAlchemyError("DB Error")):
        response = client.get("/tractors/")
        assert response.status_code == 500
        assert "Ошибка базы данных при получении тракторов" in response.json()["detail"]

def test_get_tractors_unknown_error(client):
    with patch('app.CRUDs.get_tractors', side_effect=Exception("Unknown Error")):
        response = client.get("/tractors/")
        assert response.status_code == 500
        assert "Неизвестная ошибка" in response.json()["detail"]

def test_create_tractor_sqlalchemy_error(client):
    tractor_data = {
        "model": "K-7",
        "vin": "TEST123",
        "oh_hour": 100,
        "region": "RU-MOS",
        "consumer": "Dealer A",
        "serv_center": "Center 1"
    }

    with patch('app.CRUDs.create_tractor', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/tractors/", json=tractor_data)
        assert response.status_code == 500
        assert "Ошибка базы данных при создании трактора" in response.json()["detail"]

def test_create_tractor_unknown_error(client):
    tractor_data = {
        "model": "K-7",
        "vin": "TEST123",
        "oh_hour": 100,
        "region": "RU-MOS",
        "consumer": "Dealer A",
        "serv_center": "Center 1"
    }

    with patch('app.CRUDs.create_tractor', side_effect=Exception("Unknown Error")):
        response = client.post("/tractors/", json=tractor_data)
        assert response.status_code == 500
        assert "Неизвестная ошибка" in response.json()["detail"]

def test_get_software_sqlalchemy_error(client):
    with patch('app.CRUDs.get_software', side_effect=SQLAlchemyError("DB Error")):
        response = client.get("/software/")
        assert response.status_code == 500
        assert "Ошибка базы данных при получении прошивок" in response.json()["detail"]

def test_create_software_sqlalchemy_error(client):
    sw_data = {
        "path": "new.bin",
        "name": "NewSW",
        "inner_name": "NewInner",
        "release_date": "2024-01-01T00:00:00",
        "description": "A new software"
    }

    with patch('app.CRUDs.create_software', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/software/", json=sw_data)
        assert response.status_code == 500
        assert "Ошибка базы данных при создании прошивки" in response.json()["detail"]

def test_get_component_parts_sqlalchemy_error(client):
    with patch('app.CRUDs.get_component_parts', side_effect=SQLAlchemyError("DB Error")):
        response = client.get("/component-parts/")
        assert response.status_code == 500
        assert "Ошибка базы данных при получении компонентов частей" in response.json()["detail"]

def test_create_component_part_sqlalchemy_error(client):
    part_data = {
        "component": 1,
        "part_type": "main"
    }

    with patch('app.CRUDs.create_component_part', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/component-parts/", json=part_data)
        assert response.status_code == 500
        assert "Ошибка базы данных при создании части компонента" in response.json()["detail"]

def test_get_software_component_links_sqlalchemy_error(client):
    with patch('app.CRUDs.get_software_component_parts', side_effect=SQLAlchemyError("DB Error")):
        response = client.get("/software-component-links/")
        assert response.status_code == 500
        assert "Ошибка базы данных при получении связей ПО и частей" in response.json()["detail"]

def test_create_software_component_link_sqlalchemy_error(client):
    link_data = {
        "component_part_id": 1,
        "software_id": 1,
        "is_major": False,
        "status": "s"
    }

    with patch('app.CRUDs.create_software_component_part', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/software-component-links/", json=link_data)
        assert response.status_code == 500
        assert "Ошибка базы данных при создании связи ПО и части" in response.json()["detail"]

def test_get_telemetry_components_sqlalchemy_error(client):
    with patch('app.CRUDs.get_telemetry_components', side_effect=SQLAlchemyError("DB Error")):
        response = client.get("/telemetry-components/")
        assert response.status_code == 500
        assert "Ошибка базы данных при получении телеметрии" in response.json()["detail"]

def test_create_telemetry_component_sqlalchemy_error(client):
    tel_data = {
        "tractor": 1,
        "component": 1,
        "mounting_date": "2024-01-01",
        "current_sw_version": 1,
        "recommend_sw_version": 2
    }

    with patch('app.CRUDs.create_telemetry_component', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/telemetry-components/", json=tel_data)
        assert response.status_code == 500
        assert "Ошибка базы данных при создании телеметрии" in response.json()["detail"]

def test_get_users_sqlalchemy_error(client):
    with patch('app.CRUDs.get_users', side_effect=SQLAlchemyError("DB Error")):
        response = client.get("/users/")
        assert response.status_code == 500
        assert "Ошибка базы данных при получении пользователей" in response.json()["detail"]

def test_search_tractors_value_error(client):
    with patch('app.CRUDs.search_tractors', side_effect=ValueError("Bad regex")):
        response = client.get("/search-tractor", params={"request": "***"})  # плохой regex
        assert response.status_code == 400
        assert "Bad regex" in response.json()["detail"]

def test_search_tractors_unknown_error(client):
    with patch('app.CRUDs.search_tractors', side_effect=Exception("Unknown Error")):
        response = client.get("/search-tractor", params={"request": "K-7"})
        assert response.status_code == 500
        assert "Unknown Error" in response.json()["detail"]

def test_get_components(client):
    with patch('app.CRUDs.get_components', return_value=[]) as mock_crud:
        response = client.get("/component/")
        assert response.status_code == 200
        mock_crud.assert_called_once()

def test_create_component(client):
    comp_data = {
        "type": "engine",
        "model": "Model1",
        "number_of_parts": 1,
        "producer_comp": "Producer1"
    }

    with patch('app.CRUDs.create_component', return_value=comp_data) as mock_crud:
        response = client.post("/component/", json=comp_data)

        assert response.status_code == 201
        mock_crud.assert_called_once()

def test_delete_component(client):
    with patch('app.CRUDs.delete_component', return_value=True) as mock_crud:
        response = client.delete("/component/1")
        assert response.status_code == 204
        mock_crud.assert_called_once_with(client.db, 1)

# --- Тесты для ошибок в routes.py ---

def test_get_components_sqlalchemy_error(client):
    with patch('app.CRUDs.get_components', side_effect=SQLAlchemyError("DB Error")):
        response = client.get("/component/")
        assert response.status_code == 500
        assert "Ошибка базы данных при получении компонентов тракторов" in response.json()["detail"]

def test_create_component_sqlalchemy_error(client):
    comp_data = {
        "type": "engine",
        "model": "Model1",
        "number_of_parts": 1,
        "producer_comp": "Producer1"
    }

    with patch('app.CRUDs.create_component', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/component/", json=comp_data)
        assert response.status_code == 500
        assert "Ошибка базы данных при создании компонента" in response.json()["detail"]

def test_delete_component_sqlalchemy_error(client):
    with patch('app.CRUDs.delete_component', side_effect=SQLAlchemyError("DB Error")):
        response = client.delete("/component/1")
        assert response.status_code == 500
        assert "Ошибка базы данных при удалении компонента" in response.json()["detail"]

def test_create_tractor_sqlalchemy_error(client):
    tractor_data = {
        "model": "K-7",
        "vin": "TEST123",
        "oh_hour": 100,
        "region": "RU-MOS",
        "consumer": "Dealer A",
        "serv_center": "Center 1"
    }

    with patch('app.CRUDs.create_tractor', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/tractors/", json=tractor_data)
        assert response.status_code == 500
        assert "Ошибка базы данных при создании трактора" in response.json()["detail"]

def test_create_software_sqlalchemy_error(client):
    sw_data = {
        "path": "new.bin",
        "name": "NewSW",
        "inner_name": "NewInner",
        "release_date": "2024-01-01T00:00:00",
        "description": "A new software"
    }

    with patch('app.CRUDs.create_software', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/software/", json=sw_data)
        assert response.status_code == 500
        assert "Ошибка базы данных при создании прошивки" in response.json()["detail"]

def test_create_component_part_sqlalchemy_error(client):
    part_data = {
        "component": 1,
        "part_type": "main"
    }

    with patch('app.CRUDs.create_component_part', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/component-parts/", json=part_data)
        assert response.status_code == 500
        assert "Ошибка базы данных при создании части компонента" in response.json()["detail"]

def test_create_software_component_link_sqlalchemy_error(client):
    link_data = {
        "component_part_id": 1,
        "software_id": 1,
        "is_major": False,
        "status": "s"
    }

    with patch('app.CRUDs.create_software_component_part', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/software-component-links/", json=link_data)
        assert response.status_code == 500
        assert "Ошибка базы данных при создании связи ПО и части" in response.json()["detail"]

def test_create_telemetry_component_sqlalchemy_error(client):
    tel_data = {
        "tractor": 1,
        "component": 1,
        "mounting_date": "2024-01-01",
        "current_sw_version": 1,
        "recommend_sw_version": 2
    }

    with patch('app.CRUDs.create_telemetry_component', side_effect=SQLAlchemyError("DB Error")):
        response = client.post("/telemetry-components/", json=tel_data)
        assert response.status_code == 500
        assert "Ошибка базы данных при создании телеметрии" in response.json()["detail"]