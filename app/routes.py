from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from . import CRUDs, schemas, config, models, authorization
from .config import settings 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Query
from typing import List
<<<<<<< Updated upstream
from .authorization import *
from sqlalchemy.ext.asyncio import AsyncSession
from .authorization import (
    get_current_user,
    require_role,
    create_access_token,
    authenticate_user,
    get_password_hash
)
=======
# from .authorization import get_password_hash
from .database import get_session
>>>>>>> Stashed changes

router = APIRouter()

# Авторизация
# @router.post("/register/")
# async def register_user(user_data: SUserRegister) -> dict:
#     user = await UsersDAO.find_one_or_none(email=user_data.email)
#     if user:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail='Пользователь уже существует'
#         )
#     user_dict = user_data.dict()
#     user_dict['password'] = get_password_hash(user_data.password)
#     await UsersDAO.add(**user_dict)
#     return {'message': 'Вы успешно зарегистрированы!'}

#Routes трактора
@router.get("/tractors/", response_model=list[schemas.TractorsSchema])
def get_tractors(db: Session = Depends(get_session)):
    try: 
        return CRUDs.get_tractors(db)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении тракторов: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.post("/tractors/", response_model=schemas.TractorsSchema, status_code=status.HTTP_201_CREATED)
def create_tractor(tractor: schemas.TractorsSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_tractor_by_terminal(db, tractor.id):
        raise HTTPException(status_code=400, detail="Tractor with this terminal_id already exists")
    return CRUDs.create_tractor(db, tractor)

@router.delete("/tractors/{tractor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tractor(tractor_id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_tractor(db, tractor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tractor not found")

#Routes компонентов трактора
@router.get("/component/", response_model=list[schemas.ComponentSchema])
def get_component(session: Session = Depends(get_session)):
    try:
        return CRUDs.get_component(session)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении компонентов тракторов: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.post("/component/", response_model=schemas.ComponentSchema, status_code=status.HTTP_201_CREATED)
def create_component(component: schemas.ComponentSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_component_by_terminal(db, component.id):
        raise HTTPException(status_code=400, detail="Tractor component with this terminal_id already exists")
    return    CRUDs.create_component(db, component)


@router.delete("/component/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_component(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_component(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Tractor component not found")


# #Routes for Telemetry components
@router.get("/telemetryComponents/", response_model=list[schemas.TelemetryComponentSchema])
def get_telemetry_components(session: Session = Depends(get_session)): 
    try:
        return CRUDs.get_telemetry_component(session)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении компонентов: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
    
@router.post("/telemetryComponent/", response_model=schemas.TelemetryComponentSchema, status_code=status.HTTP_201_CREATED)
def create_telemetry_component(telemetry_component: schemas.TelemetryComponentSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_telemetry_component_by_terminal(db, telemetry_component.id):
        raise HTTPException(status_code=400, detail="Telemetry with this id already exists")
    return    CRUDs.create_telemetry_component(db, telemetry_component)


@router.delete("/telemetryComponent/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_telemetry_component(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_telemetry_component(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Telemetry not found")


# #Routes Software
@router.get("/software/", response_model=list[schemas.SoftwareSchema])
def get_software(session: Session = Depends(get_session)):
    try:
        return CRUDs.get_software(session)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении прошивок: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )

@router.get("/software/download/{id}")
def download_software(id: int, db: Session = Depends(get_session)):
    fw = CRUDs.download_software(db, id)
    if not fw:
        return HTTPException(status_code=400, detail="Software with this id doesnt exist")
    return {"download_url": fw.path, "filename": f"{fw.name}.bin"}

@router.post("/software/", response_model=schemas.SoftwareSchema, status_code=status.HTTP_201_CREATED)
def create_software(software: schemas.SoftwareSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_software_by_terminal(db, software.id):
        raise HTTPException(status_code=400, detail="Firmware with this terminal_id already exists")
    return    CRUDs.create_software(db, software)

@router.delete("/software/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_software(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_software(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Firmware not found")
    
#routes for ComponentParts
@router.get("/componentParts/", response_model=list[schemas.ComponentPartSchema])
def get_components_parts(session: Session = Depends(get_session)): 
    try:
        return CRUDs.get_componentPart(session)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении компонентов: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
    
@router.post("/componentParts/", response_model=schemas.ComponentPartSchema, status_code=status.HTTP_201_CREATED)
def create_components_parts(component: schemas.ComponentPartSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_componentPart_by_terminal(db, component.id):
        raise HTTPException(status_code=400, detail="Relations with this id already exists")
    return    CRUDs.create_componentPart(db, component)


@router.delete("/componentParts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_componentPart(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_componentPart(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Relations not found")


#routes for ComponentsSoftware
@router.get("/software2components/", response_model=list[schemas.SoftwareComponentsSchema])
def get_Software2Components(session: Session = Depends(get_session)): 
    try:
        return CRUDs.get_software_componentParts(session)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении компонентов: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка: {str(e)}"
        )
    
@router.post("/software2components/", response_model=schemas.SoftwareComponentsSchema, status_code=status.HTTP_201_CREATED)
def create_Software2Components(software_component: schemas.SoftwareComponentsSchema, db: Session = Depends(get_session)):
    # Проверка на дубликат terminal_id
    if CRUDs.get_software_componentsParts_by_terminal(db, software_component.id):
        raise HTTPException(status_code=400, detail="Software_components with this id already exists")
    return    CRUDs.create_software_componentsParts(db, software_component)

@router.delete("/softwareComponents/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_Software2Components(id: int, db: Session = Depends(get_session)):
    success = CRUDs.delete_software_components(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Software_components not found")


#------------Routes для страниц-----------------

#3-я страница
#Поиск по фильтрам КОМПОНЕНТОВ
@router.post("/component-info")
def get_component_by_filters(filters: schemas.ComponentInfoRequest, db: Session = Depends(get_session)):
    data = CRUDs.get_component_by_filters(
        db,
        trac_model=filters.trac_model,
        type_comp=filters.type_comp,
        model_comp=filters.model_comp
    )
    return data

#Глобальный поиск Компонентов
@router.post("/search-component", response_model=List[schemas.ComponentSearchResponseItem])
def get_Search_Component(
    filters: schemas.ComponentSearchResponse,
    db: Session = Depends(get_session)
):
    data = CRUDs.search_components(filter=filters, db=db)
    return data

#4-я страница
#Поиск по фильтрам ТРАКТОРОВ
@router.post("/tractor-info")
def get_tractors_by_filters(filters: schemas.TractorInfoRequest, db: Session = Depends(get_session)):
    data = CRUDs.get_tractors_by_filters(
        db,
        trac_model=filters.trac_model, 
        status=filters.status,
        dealer=filters.dealer
    )
    return data

#Глобальный поиск тракторов
@router.post("/search-tractor", response_model=List[schemas.TractorSearchResponse])
def get_Search_Tractors(
    filters: schemas.SearchFilterTractors,
    db: Session = Depends(get_session)
):
    data = CRUDs.search_tractors(filters=filters, db=db)
    return data


#авторизация
# ✅ 1. Получение токена (OAuth2 стандарт)
@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.login},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ✅ 2. Регистрация (если нужно)
@router.post("/register", response_model=schemas.UserResponse, status_code=201)
async def register_user(
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_session)
):
    existing = await auth.get_user(db, user.login)
    if existing:
        raise HTTPException(400, "User already exists")
    hashed = get_password_hash(user.password)
    db_user = models.UserDB(
        login=user.login,
        password_hash=hashed,
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return schemas.UserResponse(login=db_user.login, role=db_user.role)

# ✅ 3. Текущий пользователь
@router.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: schemas.UserResponse = Depends(get_current_user)):
    return current_user

# ✅ 4. Только инженер
@router.get("/engineer-data")
async def engineer_only(
    current_user: schemas.UserResponse = Depends(require_role(UserRole.ENGINEER))
):
    return {"message": "Hello, Engineer!", "user": current_user}

# ✅ 5. Только дилер
@router.get("/dealer-data")
async def dealer_only(
    current_user: schemas.UserResponse = Depends(require_role(UserRole.DILLER))
):
    return {"message": "Hello, Dealer!", "user": current_user}

# ✅ 6. Только модератор
@router.get("/moderator-data")
async def moderator_only(
    current_user: schemas.UserResponse = Depends(require_role(UserRole.MODERATOR))
):
    return {"message": "Hello, Moderator!", "user": current_user}
