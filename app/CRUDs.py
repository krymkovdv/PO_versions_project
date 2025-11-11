from sqlalchemy.orm import Session
from . import models, schemas
from sqlalchemy import or_, cast, String, select
from fastapi import HTTPException, status, Depends
from datetime import datetime
from typing import List
from .authorization import *
from .models import *
from datetime import timedelta
# from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

# # Авторизация
# def verify_password(plain_password: str, hashed_password: str):
#     return pwd_context.verify(plain_password, hashed_password)

# def get_password_hash(password: str):
#     return pwd_context.hash(password)

# def create_access_token(data: dict, expires_delta: timedelta = None):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# async def get_user(db: AsyncSession, username: str):
#     result = await db.execute(select(UserDB).where(UserDB.username == username))
#     return result.scalars().first()


# async def authenticate_user(db: AsyncSession, username: str, password: str):
#     user = await get_user(db, username)
#     if not user or not verify_password(password, user.password_hash):
#         return False
#     return user

# async def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: AsyncSession = Depends(get_db)
# ):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#     user = await get_user(db, username)
#     if user is None:
#         raise credentials_exception
#     return User(username=user.username, role=user.role)

# def require_role(required_role: str):
#     def role_checker(current_user: User = Depends(get_current_user)):
#         if current_user.role != required_role:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Insufficient permissions"
#             )
#         return current_user
#     return role_checker


#----------БАЗОВЫЕ CRUDS----------
#Cruds for Tractor
def get_tractors(db: Session):
    stmt = select(models.Tractors)
    result = db.execute(stmt).scalars().all()
    return result

def create_tractor(db: Session, tractor: schemas.TractorsSchema):
    db_tractor = models.Tractors(
        id = tractor.id,
        model=tractor.model,
        vin =tractor.vin,
        oh_hour = tractor.oh_hour,
        last_activity=tractor.last_activity,
        assembly_date=tractor.assembly_date,
        region = tractor.region,
        consumer = tractor.consumer,
        serv_center = tractor.serv_center
    )
    db.add(db_tractor)
    db.commit()
    db.refresh(db_tractor)
    return db_tractor

def get_tractor_by_terminal(db: Session, id: int):
    return db.query(models.Tractors).filter(models.Tractors.id == id).first()

def delete_tractor(db: Session, id: int):
    tractor = db.query(models.Tractors).filter(models.Tractors.id == id).first()
    if tractor is None:
        return False
    db.delete(tractor)
    db.commit()
    return True

# #Cruds for Component
def get_component(db: Session):
    stmt = select(models.Component)
    result = db.execute(stmt).scalars().all()
    return result

def get_component_by_terminal(db: Session, id: str):
    return db.query(models.Component).filter(models.Component.id == id).first()

def create_component(db: Session, component: schemas.ComponentSchema):
    db_component = models.Component(
        id = component.id,
        type = component.type,
        model = component.model,
        mounting_date = component.mounting_date,
        comp_ser_num = component.comp_ser_num,
        tractor_id = component.tractor_id,
        number_of_parts = component.number_of_parts,
        producer_comp = component.producer_comp
    )
    db.add(db_component)
    db.commit()
    db.refresh(db_component)
    return db_component

def delete_component(db: Session, id: int):
    component = db.query(models.Component).filter(models.Component.id == id).first()
    if component is None:
        return False
    db.delete(component)
    db.commit()
    return True

#CRUDs for TelemetryComponent
def get_telemetry_component(db: Session):
    stmt = select(models.TelemetryComponents)
    result = db.execute(stmt).scalars().all()
    return result

def get_telemetry_component_by_terminal(db: Session, id: str):
    return db.query(models.TelemetryComponents).filter(models.TelemetryComponents.id == id).first()

def create_telemetry_component(db: Session, telemetry_component: schemas.TelemetryComponentSchema):
    db_telemetry_component = models.TelemetryComponents(
        id= telemetry_component.id,
        software = telemetry_component.software,
        tractor = telemetry_component.tractor,
        component = telemetry_component.component,
        component_part_id = telemetry_component.component_part_id,
        time_rec = telemetry_component.time_rec
    )
    db.add(db_telemetry_component)
    db.commit()
    db.refresh(db_telemetry_component)
    return db_telemetry_component

def delete_telemetry_component(db: Session, id: int):
    telemetry_component = db.query(models.TelemetryComponents).filter(models.TelemetryComponents.id == id).first()
    if telemetry_component is None:
        return False
    db.delete(telemetry_component)
    db.commit()
    return True

#CRUDs for Software
def download_software(db: Session, id: int):
    """
    Получить информацию о прошивке для скачивания
    """
    fw = db.query(models.Software).filter(models.Software.id == id).first()
    if not fw:
        return None
    return fw


def get_software(db: Session):
    stmt = select(models.Software)
    result = db.execute(stmt).scalars().all()
    return result

def get_software_by_terminal(db: Session, id: str):
    return db.query(models.Software).filter(models.Software.id == id).first()

def create_software(db: Session, software: schemas.SoftwareSchema):
    db_software = models.Software(
        id = software.id,
        path = software.path,
        name = software.name,
        inner_name = software.inner_name,
        release_date = software.release_date,
        description = software.description
    )
    db.add(db_software)
    db.commit()
    db.refresh(db_software)
    return db_software

def delete_software(db: Session, id: int):
    software = db.query(models.Software).filter(models.Software.id == id).first()
    if software is None:
        return False
    db.delete(software)
    db.commit()
    return True

# #CRUDs for ComponentsPart
def get_componentPart(db: Session):
    stmt = select(models.ComponentParts)
    result = db.execute(stmt).scalars().all()
    return result

def get_componentPart_by_terminal(db: Session, id: str):
    return db.query(models.ComponentParts).filter(models.ComponentParts.id == id).first()

def create_componentPart(db: Session, part: schemas.ComponentPartSchema):
        db_part = models.ComponentParts(
            id = part.id,
            component = part.component,
            part_number = part.part_number,
            part_type = part.part_type,
            current_sw_version = part.current_sw_version,
            recommend_sw_version = part.recommend_sw_version,
            is_major = part.is_major,
            not_recom_sw = part.not_recom_sw,
            next_ver = part.next_ver
        )        
        db.add(db_part)
        db.commit()
        db.refresh(db_part)
        return db_part

def delete_componentPart(db: Session, id: int):
    component = db.query(models.ComponentParts).filter(models.ComponentParts.id == id).first()
    if component is None:
        return False
    db.delete(component)
    db.commit()
    return True

#CRUDs for Software2ComponentParts
def get_software_componentParts(db: Session):
    stmt = select(models.Software2ComponentPart)
    result = db.execute(stmt).scalars().all()
    return result

def get_software_componentsParts_by_terminal(db: Session, id: str):
    return db.query(models.Software2ComponentPart).filter(models.Software2ComponentPart.id == id).first()

def create_software_componentsParts(db: Session, software_components: schemas.SoftwareComponentsSchema):

    db_software_components = models.Software2ComponentPart(
        id = software_components.id,
        component_part_id = software_components.component_part_id,
        software_id = software_components.software_id,
        is_major = software_components.is_major,
        status = software_components.status,
        date_change = software_components.date_change,
        not_recom = software_components.not_recom,
        date_change_record = software_components.date_change_record
        )
    db.add(db_software_components)
    db.commit()
    db.refresh(db_software_components)
    return db_software_components

def delete_software_components(db: Session, id: int):
    db.delete(db.query(models.Software2ComponentPart).filter(models.Software2ComponentPart.id == id).first())
    db.commit()



#CRUD'ы для страницы 3

#ПО фильтрам Компоненты
def get_component_by_filters (db: Session, trac_model: List[str], type_comp: List[str], model_comp: str):
    query = db.query(models.Software.id, 
                    models.Software.path.label("download_link"),
                    models.Software.name.label("producer_version"),
                    models.Software.inner_name.label("inner_version"),
                    models.Software.release_date,
                    models.Software.id.label("id_Firmwares"),
                    models.Component.type.label("type_component"),
                    models.Component.model.label("model_component"),
                    models.Software2ComponentPart.is_major.label("is_maj")
                        ).select_from(models.Component)
    query = query.join(models.Tractors, models.Component.tractor_id == models.Tractors.id)
    query = query.join(models.ComponentParts, models.Component.id == models.ComponentParts.component)
    query = query.join(models.Software, models.ComponentParts.current_sw_version == models.Software.id)
    query = query.join(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id) 
    
    if trac_model:
        query = query.filter(models.Tractors.model.in_(trac_model))
    if type_comp:
        query = query.filter(models.Component.type.in_(type_comp))
    if model_comp:
        query = query.filter(models.Component.model == model_comp)

    query = query.order_by(models.Software.release_date.desc())

    results = query.all()

    return [
        {
            "download_link": r.download_link,
            "type_component": r.type_component,
            "release_date": r.release_date.isoformat() if r.release_date else None,
            "inner_version": r.inner_version,
            "producer_version": r.producer_version,
            "is_maj": r.is_maj,
            "model_component": r.model_component,
            "id_Firmwares": r.id_Firmwares
        }
        for r in results
    ]

#Глобальный поиск компонентов
#CRUD'ы для страницы 4

#ПО фильтрам Трактора
def get_tractors_by_filters(db: Session, trac_model: List[str], status: List[str], dealer: str):
    query = db.query(models.Tractors.vin,
                     models.Tractors.model,
                     models.Tractors.consumer,
                     models.Tractors.assembly_date,
                     models.Tractors.region,
                     models.Tractors.oh_hour,
                     models.Tractors.last_activity,
                     models.Software.name,
                     models.ComponentParts.recommend_sw_version,
                     models.Component.type
                     ).select_from(models.Tractors)
    query = query.join(models.Component, models.Component.tractor_id == models.Tractors.id)
    query = query.join(models.ComponentParts, models.Component.id == models.ComponentParts.component)
    query = query.join(models.Software, models.ComponentParts.current_sw_version == models.Software.id)
    query = query.join(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)
    
    if trac_model:
        query = query.filter(models.Tractors.model.in_(trac_model))
    if status:
        query = query.filter(models.Software2ComponentPart.status.in_(status))
    if dealer:
        query = query.filter(models.Tractors.consumer == dealer)

    query = query.order_by(models.Software.release_date.desc())

    results = query.all()

    return [
        {
            "vin": r.vin,
            "model": r.model,
            "consumer": r.consumer,
            "assembly_date": r.assembly_date.isoformat() if r.assembly_date else None,
            "region": r.region,
            "oh_hour": str(r.oh_hour) if r.oh_hour is not None else "",
            "last_activity": r.last_activity.isoformat() if r.last_activity else None,
            "sw_name": r.name,
            "recommend_sw_version": str(r.recommend_sw_version) if r.recommend_sw_version is not None else "",
            "type": r.type
        }
        for r in results
    ]
     
#Глобальный поиск ТРАКТОРОВ
def search_tractors(db: Session, filters: schemas.SearchFilterTractors):
    query = db.query(models.Tractors.vin,
                    models.Tractors.model,
                    models.Tractors.consumer,
                    models.Tractors.assembly_date,
                    models.Tractors.region,
                    models.Tractors.oh_hour,
                    models.Tractors.last_activity,
                    models.Software.name,
                    models.ComponentParts.recommend_sw_version,
                    models.Component.type
                    ).select_from(models.Tractors) 
    query = query.join(models.Component, models.Component.tractor_id == models.Tractors.id)
    query = query.join(models.ComponentParts, models.Component.id == models.ComponentParts.component)
    query = query.join(models.Software, models.ComponentParts.current_sw_version == models.Software.id)
    query = query.join(models.Software2ComponentPart, models.Software2ComponentPart.software_id == models.Software.id)
    
    if filters.vin:
        query = query.filter(models.Tractors.vin == filters.vin)
    elif filters.model:
        query =query.filter(models.Tractors.model == filters.model)
    elif filters.date_release:
        query =query.filter(models.Software.release_date == filters.date_release)
        try:
            date_val = datetime.strptime(filters.date_release, "%Y-%m-%d").date()
            query = query.filter(models.Software.release_date == date_val)
        except ValueError:
            pass
    elif filters.region:
        query =query.filter(models.Tractors.region == filters.region)
    elif filters.oh_hour:
        try:
            oh_val = int(filters.oh_hour)
            query = query.filter(models.Tractors.oh_hour == oh_val)
        except ValueError:
            pass
    elif filters.last_activity:
        try:
            dt = datetime.fromisoformat(filters.last_activity)
            query = query.filter(models.Tractors.last_activity == dt)
        except ValueError:
            pass
    

    results = query.all()

    return [
        {
            "vin": r.vin,
            "model": r.model,
            "consumer": r.consumer,
            "assembly_date": r.assembly_date.isoformat() if r.assembly_date else None,
            "region": r.region,
            "oh_hour": str(r.oh_hour) if r.oh_hour is not None else "",
            "last_activity": r.last_activity.isoformat() if r.last_activity else None,
            "sw_name": r.name,
            "recommend_sw_version": str(r.recommend_sw_version) if r.recommend_sw_version is not None else "",
            "type": r.type
        }
        for r in results
    ]
