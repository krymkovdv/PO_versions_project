from app.models import Tractors, UserDB, Software, ComponentParts, Software2ComponentPart, TelemetryComponents
from fastapi import HTTPException
import pytest
from unittest.mock import MagicMock, Mock
from app.CRUDs import get_tractors, create_tractor, delete_tractor, get_users, create_user
from app.models import Tractors, UserDB
from fastapi import HTTPException
import pytest
from unittest.mock import MagicMock, Mock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.CRUDs import (
    get_tractors, create_tractor, delete_tractor, get_users, create_user,
    get_software, create_software, delete_software,
    get_component_parts, create_component_part, delete_component_part,
    get_software_component_parts, create_software_component_part, delete_software_component_part,
    get_telemetry_components, create_telemetry_component, delete_telemetry_component,
    get_component_by_filters, search_components,
    get_tractors_by_filters, search_tractors, get_tractor_by_vin
)
from app.models import Tractors, UserDB, Software, ComponentParts, Software2ComponentPart, TelemetryComponents
from fastapi import HTTPException

def test_get_tractors():
    mock_db = MagicMock()
    tractor1 = Tractors(id=1, model="K-7", vin="VIN001", oh_hour=100)
    tractor2 = Tractors(id=2, model="K-5", vin="VIN002", oh_hour=200)

    # Мокаем db.execute(...).scalars().all()
    mock_scalars = Mock()
    mock_scalars.all.return_value = [tractor1, tractor2]
    mock_execute_result = Mock()
    mock_execute_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_execute_result

    result = get_tractors(mock_db)

    assert len(result) == 2
    assert result[0].model == "K-7"
    assert result[1].model == "K-5"

def test_get_users():
    mock_db = MagicMock()
    user1 = UserDB(id=1, username="user1", password_hash="hash1", role="user")
    user2 = UserDB(id=2, username="user2", password_hash="hash2", role="moderator")

    # Мокаем db.execute(...).scalars().all()
    mock_scalars = Mock()
    mock_scalars.all.return_value = [user1, user2]
    mock_execute_result = Mock()
    mock_execute_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_execute_result

    result = get_users(mock_db)

    assert len(result) == 2
    assert result[0].username == "user1"
    assert result[1].username == "user2"

def test_create_tractor():
    mock_db = MagicMock()
    from app.schemas import TractorsSchema
    # ✅ Добавлены обязательные поля
    tractor_data = TractorsSchema(
        model="K-7",
        vin="VIN123",
        oh_hour=100,
        region="RU-MOS",
        consumer="Dealer A",
        serv_center="Center 1"
    )

    db_tractor = Tractors(**tractor_data.model_dump())

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(return_value=None)

    from app.CRUDs import create_tractor
    result = create_tractor(mock_db, tractor_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_delete_tractor_found():
    mock_db = MagicMock()
    tractor = Tractors(id=1, model="K-7", vin="VIN001", oh_hour=100)
    mock_db.query.return_value.filter.return_value.first.return_value = tractor
    mock_db.delete = Mock()
    mock_db.commit = Mock()

    result = delete_tractor(mock_db, 1)

    assert result is True
    mock_db.delete.assert_called_once_with(tractor)
    mock_db.commit.assert_called_once()

def test_delete_tractor_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = delete_tractor(mock_db, 999)

    assert result is False

# tests/unit/test_cruds.py
def test_create_user_success():
    mock_db = MagicMock()
    from app.schemas import UserCreate
    user_data = UserCreate(username="newuser", password="password123", role="moderator")

    mock_db.query.return_value.filter.return_value.first.return_value = None

    mock_db.add = Mock()
    mock_db.commit = Mock()  # ✅ Убедитесь, что commit не бросает исключение
    mock_db.refresh = Mock()

    from app.CRUDs import create_user
    result = create_user(mock_db, user_data)

    assert "username" in result  # ✅ Теперь result — словарь
    assert result["username"] == "newuser"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_create_user_duplicate():
    mock_db = MagicMock()
    from app.schemas import UserCreate
    # ✅ Правильная роль: 'moderator'
    user_data = UserCreate(username="existing", password="password123", role="moderator")

    # Проверяем, что пользователь существует
    existing_user = UserDB(id=1, username="existing", password_hash="hash", role="moderator")
    mock_db.query.return_value.filter.return_value.first.return_value = existing_user

    from app.CRUDs import create_user
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        create_user(mock_db, user_data)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail


    # tests/unit/test_cruds.py
import pytest
from unittest.mock import MagicMock, Mock
from app.CRUDs import (
    get_tractors, create_tractor, delete_tractor, get_users, create_user,
    get_software, create_software, delete_software,
    get_component_parts, create_component_part, delete_component_part,
    get_software_component_parts, create_software_component_part, delete_software_component_part,
    get_telemetry_components, create_telemetry_component, delete_telemetry_component,
    get_component_by_filters, search_components,
    get_tractors_by_filters, search_tractors, get_tractor_by_vin
)


# ... существующие тесты ...

# --- Новые тесты для CRUDs ---

def test_get_software():
    mock_db = MagicMock()
    sw1 = Software(id=1, path="sw1.bin", name="SW1", inner_name="Inner1", release_date=None, description="")
    sw2 = Software(id=2, path="sw2.bin", name="SW2", inner_name="Inner2", release_date=None, description="")

    mock_scalars = Mock()
    mock_scalars.all.return_value = [sw1, sw2]
    mock_execute_result = Mock()
    mock_execute_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_execute_result

    result = get_software(mock_db)

    assert len(result) == 2
    assert result[0].name == "SW1"
    assert result[1].name == "SW2"

def test_create_software():
    mock_db = MagicMock()
    from app.schemas import SoftwareSchema
    sw_data = SoftwareSchema(path="new.bin", name="NewSW", inner_name="NewInner", release_date=None, description="")

    db_sw = Software(**sw_data.model_dump())

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(return_value=None)

    from app.CRUDs import create_software
    result = create_software(mock_db, sw_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_delete_software_found():
    mock_db = MagicMock()
    sw = Software(id=1, path="del.bin", name="DelSW", inner_name="DelInner", release_date=None, description="")
    mock_db.query.return_value.filter.return_value.first.return_value = sw
    mock_db.delete = Mock()
    mock_db.commit = Mock()

    result = delete_software(mock_db, 1)

    assert result is True
    mock_db.delete.assert_called_once_with(sw)
    mock_db.commit.assert_called_once()

def test_delete_software_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = delete_software(mock_db, 999)

    assert result is False

def test_get_component_parts():
    mock_db = MagicMock()
    part1 = ComponentParts(id=1, component=1, part_type="main")
    part2 = ComponentParts(id=2, component=1, part_type="aux")

    mock_scalars = Mock()
    mock_scalars.all.return_value = [part1, part2]
    mock_execute_result = Mock()
    mock_execute_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_execute_result

    result = get_component_parts(mock_db)

    assert len(result) == 2
    assert result[0].part_type == "main"
    assert result[1].part_type == "aux"

def test_create_component_part():
    mock_db = MagicMock()
    from app.schemas import ComponentPartSchema
    part_data = ComponentPartSchema(component=1, part_type="main")

    db_part = ComponentParts(**part_data.model_dump())

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(return_value=None)

    from app.CRUDs import create_component_part
    result = create_component_part(mock_db, part_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_delete_component_part_found():
    mock_db = MagicMock()
    part = ComponentParts(id=1, component=1, part_type="main")
    mock_db.query.return_value.filter.return_value.first.return_value = part
    mock_db.delete = Mock()
    mock_db.commit = Mock()

    result = delete_component_part(mock_db, 1)

    assert result is True
    mock_db.delete.assert_called_once_with(part)
    mock_db.commit.assert_called_once()

def test_delete_component_part_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = delete_component_part(mock_db, 999)

    assert result is False

def test_get_software_component_parts():
    mock_db = MagicMock()
    link1 = Software2ComponentPart(id=1, component_part_id=1, software_id=1, is_major=False, status='s')
    link2 = Software2ComponentPart(id=2, component_part_id=2, software_id=2, is_major=True, status='t')

    mock_scalars = Mock()
    mock_scalars.all.return_value = [link1, link2]
    mock_execute_result = Mock()
    mock_execute_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_execute_result

    result = get_software_component_parts(mock_db)

    assert len(result) == 2
    assert result[0].is_major is False
    assert result[1].is_major is True

def test_create_software_component_part():
    mock_db = MagicMock()
    from app.schemas import SoftwareComponentsSchema
    link_data = SoftwareComponentsSchema(component_part_id=1, software_id=1, is_major=False, status='s')

    db_link = Software2ComponentPart(**link_data.model_dump())

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(return_value=None)

    from app.CRUDs import create_software_component_part
    result = create_software_component_part(mock_db, link_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_delete_software_component_part_found():
    mock_db = MagicMock()
    link = Software2ComponentPart(id=1, component_part_id=1, software_id=1, is_major=False, status='s')
    mock_db.query.return_value.filter.return_value.first.return_value = link
    mock_db.delete = Mock()
    mock_db.commit = Mock()

    result = delete_software_component_part(mock_db, 1)

    assert result is True
    mock_db.delete.assert_called_once_with(link)
    mock_db.commit.assert_called_once()

def test_delete_software_component_part_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = delete_software_component_part(mock_db, 999)

    assert result is False

def test_get_telemetry_components():
    mock_db = MagicMock()
    tel1 = TelemetryComponents(id=1, tractor=1, component=1, mounting_date=None, current_sw_version=1, recommend_sw_version=2)
    tel2 = TelemetryComponents(id=2, tractor=2, component=2, mounting_date=None, current_sw_version=2, recommend_sw_version=3)

    mock_scalars = Mock()
    mock_scalars.all.return_value = [tel1, tel2]
    mock_execute_result = Mock()
    mock_execute_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_execute_result

    result = get_telemetry_components(mock_db)

    assert len(result) == 2
    assert result[0].current_sw_version == 1
    assert result[1].current_sw_version == 2

def test_create_telemetry_component():
    mock_db = MagicMock()
    from app.schemas import TelemetryComponentSchema
    tel_data = TelemetryComponentSchema(tractor=1, component=1, mounting_date="2024-01-01", current_sw_version=1, recommend_sw_version=2)

    db_tel = TelemetryComponents(**tel_data.model_dump())

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(return_value=None)

    from app.CRUDs import create_telemetry_component
    result = create_telemetry_component(mock_db, tel_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_delete_telemetry_component_found():
    mock_db = MagicMock()
    tel = TelemetryComponents(id=1, tractor=1, component=1, mounting_date=None, current_sw_version=1, recommend_sw_version=2)
    mock_db.query.return_value.filter.return_value.first.return_value = tel
    mock_db.delete = Mock()
    mock_db.commit = Mock()

    result = delete_telemetry_component(mock_db, 1)

    assert result is True
    mock_db.delete.assert_called_once_with(tel)
    mock_db.commit.assert_called_once()

def test_delete_telemetry_component_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = delete_telemetry_component(mock_db, 999)

    assert result is False

def test_get_component_by_filters():
    mock_db = MagicMock()

    # Мокаем сложный запрос
    mock_query = Mock()
    mock_query.select_from.return_value = mock_query
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.distinct.return_value = mock_query

    mock_query.all.return_value = [
        Mock(download_link="link1", type_component="engine", release_date=None, inner_version="v1", producer_version="pv1", is_maj=False, model_component="mc1", id_Firmwares=1),
        Mock(download_link="link2", type_component="transmission", release_date=None, inner_version="v2", producer_version="pv2", is_maj=True, model_component="mc2", id_Firmwares=2)
    ]

    mock_db.query.return_value = mock_query

    result = get_component_by_filters(mock_db, trac_model=[], type_comp=[], model_comp=[])

    assert len(result) == 2
    assert result[0]["producer_version"] == "pv1"
    assert result[1]["is_maj"] is True

def test_search_components():
    mock_db = MagicMock()

    mock_query = Mock()
    mock_query.select_from.return_value = mock_query
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.distinct.return_value = mock_query

    mock_query.all.return_value = [
        Mock(download_link="link1", type_component="engine", release_date=None, inner_version="v1", producer_version="pv1", is_maj=False, model_component="mc1", id_Firmwares=1)
    ]

    mock_db.query.return_value = mock_query

    result = search_components(mock_db, model_comp="engine")

    assert len(result) == 1
    assert result[0]["type_component"] == "engine"

def test_get_tractors_by_filters():
    mock_db = MagicMock()

    mock_query = Mock()
    mock_query.select_from.return_value = mock_query
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.distinct.return_value = mock_query

    mock_query.all.return_value = [
        Mock(vin="VIN1", model="K-7", consumer="Dealer A", assembly_date=None, region="RU-MOS", oh_hour="100", last_activity=None, sw_name="SW1", componentParts_id=1, component_id=1, comp_model="Comp1", recommend_sw_version="1", component_type="engine")
    ]

    mock_db.query.return_value = mock_query

    from app.schemas import TractorFilter
    filters = TractorFilter(trac_model=["K-7"], status=[], dealer="", date_assemle=None)

    result = get_tractors_by_filters(mock_db, filters)

    assert len(result) == 1
    assert result[0]["model"] == "K-7"

def test_search_tractors():
    mock_db = MagicMock()

    mock_query = Mock()
    mock_query.select_from.return_value = mock_query
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.distinct.return_value = mock_query

    mock_query.all.return_value = [
        Mock(vin="VIN1", model="K-7", consumer="Dealer A", assembly_date=None, region="RU-MOS", oh_hour="100", last_activity=None, sw_name="SW1", componentParts_id=1, component_id=1, comp_model="Comp1", recommend_sw_version="1", component_type="engine")
    ]

    mock_db.query.return_value = mock_query

    result = search_tractors(mock_db, request="K-7")

    assert len(result) == 1
    assert result[0]["model"] == "K-7"

def test_get_tractor_by_vin():
    mock_db = MagicMock()

    mock_query = Mock()
    mock_query.select_from.return_value = mock_query
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.distinct.return_value = mock_query

    mock_query.all.return_value = [
        Mock(vin="VIN1", model="K-7", consumer="Dealer A", assembly_date=None, region="RU-MOS", oh_hour="100", last_activity=None, sw_name="SW1", description=None, componentParts_id=1, component_id=1, comp_model="Comp1", current_sw_version=1, recommend_sw_version="1", component_type="engine")
    ]

    mock_db.query.return_value = mock_query

    result = get_tractor_by_vin(mock_db, vin="VIN1")

    assert len(result) == 1
    assert result[0]["vin"] == "VIN1"

# tests/unit/test_cruds.py
def test_create_user_integrity_error():
    mock_db = MagicMock()
    from app.schemas import UserCreate
    user_data = UserCreate(username="newuser", password="password123", role="moderator")

    mock_db.add = Mock()
    mock_db.commit = Mock(side_effect=IntegrityError("Constraint Error", {}, None))
    mock_db.rollback = Mock() # Мокаем rollback

    from app.CRUDs import create_user
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        create_user(mock_db, user_data)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail
    mock_db.rollback.assert_called_once() 

def test_get_components():
    mock_db = MagicMock()
    comp1 = Component(id=1, type="engine", model="Model1", number_of_parts=1, producer_comp="Producer1")
    comp2 = Component(id=2, type="transmission", model="Model2", number_of_parts=1, producer_comp="Producer2")

    mock_scalars = Mock()
    mock_scalars.all.return_value = [comp1, comp2]
    mock_execute_result = Mock()
    mock_execute_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_execute_result

    result = get_components(mock_db)

    assert len(result) == 2
    assert result[0].type == "engine"
    assert result[1].type == "transmission"

def test_create_component():
    mock_db = MagicMock()
    from app.schemas import ComponentSchema
    comp_data = ComponentSchema(type="engine", model="Model1", number_of_parts=1, producer_comp="Producer1")

    db_comp = Component(**comp_data.model_dump())

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(return_value=None)

    from app.CRUDs import create_component
    result = create_component(mock_db, comp_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_delete_component_found():
    mock_db = MagicMock()
    comp = Component(id=1, type="engine", model="Model1", number_of_parts=1, producer_comp="Producer1")
    mock_db.query.return_value.filter.return_value.first.return_value = comp
    mock_db.delete = Mock()
    mock_db.commit = Mock()

    result = delete_component(mock_db, 1)

    assert result is True
    mock_db.delete.assert_called_once_with(comp)
    mock_db.commit.assert_called_once()

def test_delete_component_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = delete_component(mock_db, 999)

    assert result is False

# --- Тесты для оставшихся строк в CRUDs.py (охват строк 42-44, 49-54, 80, 92-94, 97, 100-109, 112-117, 126, 158, 188, 215, 269, 271, 273, 319, 321-324, 375, 377, 396, 401-413, 416-429, 488, 497-498, 540, 597-609, 619-620, 623-633, 640-658, 665-742, 745-757, 760-764, 773-774, 777-778, 785-795) ---

def test_get_tractors_empty():
    mock_db = MagicMock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = []
    mock_execute_result = Mock()
    mock_execute_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_execute_result

    result = get_tractors(mock_db)

    assert len(result) == 0

def test_create_tractor_missing_optional_fields():
    mock_db = MagicMock()
    from app.schemas import TractorsSchema
    # Только обязательные поля
    tractor_data = TractorsSchema(
        model="K-7",
        vin="TEST123",
        oh_hour=100,
        region="RU-MOS",
        consumer="Dealer A",
        serv_center="Center 1",
        last_activity=None,
        assembly_date=None
    )

    db_tractor = Tractors(**tractor_data.model_dump())

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(return_value=None)

    from app.CRUDs import create_tractor
    result = create_tractor(mock_db, tractor_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_get_software_empty():
    mock_db = MagicMock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = []
    mock_execute_result = Mock()
    mock_execute_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_execute_result

    result = get_software(mock_db)

    assert len(result) == 0

def test_create_software_with_optional_fields():
    mock_db = MagicMock()
    from app.schemas import SoftwareSchema
    sw_data = SoftwareSchema(
        path="new.bin",
        name="NewSW",
        inner_name="Inner",
        release_date="2024-01-01T00:00:00",
        description="A new software"
    )

    db_sw = Software(**sw_data.model_dump())

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(return_value=None)

    from app.CRUDs import create_software
    result = create_software(mock_db, sw_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_get_component_parts_empty():
    mock_db = MagicMock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = []
    mock_execute_result = Mock()
    mock_execute_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_execute_result

    result = get_component_parts(mock_db)

    assert len(result) == 0

def test_create_component_part_with_optional_fields():
    mock_db = MagicMock()
    from app.schemas import ComponentPartSchema
    part_data = ComponentPartSchema(component=1, part_type="main")

    db_part = ComponentParts(**part_data.model_dump())

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(return_value=None)

    from app.CRUDs import create_component_part
    result = create_component_part(mock_db, part_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_get_software_component_parts_empty():
    mock_db = MagicMock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = []
    mock_execute_result = Mock()
    mock_execute_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_execute_result

    result = get_software_component_parts(mock_db)

    assert len(result) == 0

def test_create_software_component_part_with_optional_fields():
    mock_db = MagicMock()
    from app.schemas import SoftwareComponentsSchema
    link_data = SoftwareComponentsSchema(
        component_part_id=1,
        software_id=1,
        is_major=False,
        status='s',
        date_change_major=None,
        not_recom=None,
        date_change_record=None,
        previous_sw_version=None
    )

    db_link = Software2ComponentPart(**link_data.model_dump())

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(return_value=None)

    from app.CRUDs import create_software_component_part
    result = create_software_component_part(mock_db, link_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_get_telemetry_components_empty():
    mock_db = MagicMock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = []
    mock_execute_result = Mock()
    mock_execute_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_execute_result

    result = get_telemetry_components(mock_db)

    assert len(result) == 0

def test_create_telemetry_component_with_optional_fields():
    mock_db = MagicMock()
    from app.schemas import TelemetryComponentSchema
    tel_data = TelemetryComponentSchema(
        tractor=1,
        component=1,
        mounting_date="2024-01-01",
        current_sw_version=1,
        recommend_sw_version=2,
        time_rec=None,
        comp_ser_num=None
    )

    db_tel = TelemetryComponents(**tel_data.model_dump())

    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock(return_value=None)

    from app.CRUDs import create_telemetry_component
    result = create_telemetry_component(mock_db, tel_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

def test_get_component_by_filters_empty():
    mock_db = MagicMock()

    mock_query = Mock()
    mock_query.select_from.return_value = mock_query
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.distinct.return_value = mock_query

    mock_query.all.return_value = []

    mock_db.query.return_value = mock_query

    result = get_component_by_filters(mock_db, trac_model=[], type_comp=[], model_comp=[])

    assert len(result) == 0

def test_search_components_empty():
    mock_db = MagicMock()

    mock_query = Mock()
    mock_query.select_from.return_value = mock_query
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.distinct.return_value = mock_query

    mock_query.all.return_value = []

    mock_db.query.return_value = mock_query

    result = search_components(mock_db, model_comp="engine")

    assert len(result) == 0

def test_get_tractors_by_filters_empty():
    mock_db = MagicMock()

    mock_query = Mock()
    mock_query.select_from.return_value = mock_query
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.distinct.return_value = mock_query

    mock_query.all.return_value = []

    mock_db.query.return_value = mock_query

    from app.schemas import TractorFilter
    filters = TractorFilter(trac_model=[], status=[], dealer="", date_assemle=None)

    result = get_tractors_by_filters(mock_db, filters)

    assert len(result) == 0

def test_search_tractors_empty():
    mock_db = MagicMock()

    mock_query = Mock()
    mock_query.select_from.return_value = mock_query
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.distinct.return_value = mock_query

    mock_query.all.return_value = []

    mock_db.query.return_value = mock_query

    result = search_tractors(mock_db, request="K-7")

    assert len(result) == 0

def test_get_tractor_by_vin_empty():
    mock_db = MagicMock()

    mock_query = Mock()
    mock_query.select_from.return_value = mock_query
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.distinct.return_value = mock_query

    mock_query.all.return_value = []

    mock_db.query.return_value = mock_query

    result = get_tractor_by_vin(mock_db, vin="VIN1")

    assert len(result) == 0

# --- Тесты для ошибок в CRUDs.py ---

def test_create_user_integrity_error():
    mock_db = MagicMock()
    from app.schemas import UserCreate
    user_data = UserCreate(username="newuser", password="password123", role="moderator")

    mock_db.add = Mock()
    mock_db.commit = Mock(side_effect=IntegrityError("Constraint Error", {}, None))
    mock_db.rollback = Mock()

    from app.CRUDs import create_user
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        create_user(mock_db, user_data)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail
    mock_db.rollback.assert_called_once()

def test_create_tractor_sqlalchemy_error():
    mock_db = MagicMock()
    from app.schemas import TractorsSchema
    tractor_data = TractorsSchema(
        model="K-7",
        vin="TEST123",
        oh_hour=100,
        region="RU-MOS",
        consumer="Dealer A",
        serv_center="Center 1"
    )

    from app.CRUDs import create_tractor
    from sqlalchemy.exc import SQLAlchemyError

    with pytest.raises(SQLAlchemyError):
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=SQLAlchemyError("DB Error"))
        create_tractor(mock_db, tractor_data)

def test_create_software_sqlalchemy_error():
    mock_db = MagicMock()
    from app.schemas import SoftwareSchema
    sw_data = SoftwareSchema(path="new.bin", name="NewSW", inner_name="NewInner", release_date=None, description="A new software")

    from app.CRUDs import create_software
    from sqlalchemy.exc import SQLAlchemyError

    with pytest.raises(SQLAlchemyError):
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=SQLAlchemyError("DB Error"))
        create_software(mock_db, sw_data)

def test_create_component_part_sqlalchemy_error():
    mock_db = MagicMock()
    from app.schemas import ComponentPartSchema
    part_data = ComponentPartSchema(component=1, part_type="main")

    from app.CRUDs import create_component_part
    from sqlalchemy.exc import SQLAlchemyError

    with pytest.raises(SQLAlchemyError):
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=SQLAlchemyError("DB Error"))
        create_component_part(mock_db, part_data)

def test_create_software_component_part_sqlalchemy_error():
    mock_db = MagicMock()
    from app.schemas import SoftwareComponentsSchema
    link_data = SoftwareComponentsSchema(component_part_id=1, software_id=1, is_major=False, status='s')

    from app.CRUDs import create_software_component_part
    from sqlalchemy.exc import SQLAlchemyError

    with pytest.raises(SQLAlchemyError):
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=SQLAlchemyError("DB Error"))
        create_software_component_part(mock_db, link_data)

def test_create_telemetry_component_sqlalchemy_error():
    mock_db = MagicMock()
    from app.schemas import TelemetryComponentSchema
    tel_data = TelemetryComponentSchema(tractor=1, component=1, mounting_date="2024-01-01", current_sw_version=1, recommend_sw_version=2)

    from app.CRUDs import create_telemetry_component
    from sqlalchemy.exc import SQLAlchemyError

    with pytest.raises(SQLAlchemyError):
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=SQLAlchemyError("DB Error"))
        create_telemetry_component(mock_db, tel_data)

def test_create_component_sqlalchemy_error():
    mock_db = MagicMock()
    from app.schemas import ComponentSchema
    comp_data = ComponentSchema(type="engine", model="Model1", number_of_parts=1, producer_comp="Producer1")

    from app.CRUDs import create_component
    from sqlalchemy.exc import SQLAlchemyError

    with pytest.raises(SQLAlchemyError):
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=SQLAlchemyError("DB Error"))
        create_component(mock_db, comp_data)
    