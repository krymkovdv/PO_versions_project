from sqlalchemy.orm import Session
from .. import models, schemas, config
from sqlalchemy import select
from fastapi import HTTPException, status, Depends, Form, File, UploadFile
import uuid
import re
import os
from datetime import datetime, date
import logging
import magic
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import random
import json

logger = logging.getLogger(__name__)

#Software
def _serialize_tractor_models(models_list: list) -> str:
    """Сериализует список моделей в JSON-строку"""
    return json.dumps(models_list, ensure_ascii=False)

def _deserialize_tractor_models(models_str: str) -> list:
    """Десериализует JSON-строку в список моделей"""
    if not models_str:
        return []
    try:
        return json.loads(models_str)
    except (json.JSONDecodeError, TypeError):
        # Для обратной совместимости - если старая строка
        return [models_str] if models_str else []

def get_software(db: Session):
    """Получение всего ПО с десериализацией моделей"""
    stmt = select(models.Software)
    result = db.execute(stmt).scalars().all()
    
    # Десериализуем tractor_models для каждого результата
    for software in result:
        software.tractor_model = _deserialize_tractor_models(software.tractor_model)
    
    return result

def get_software_by_id(db: Session, id: int):
    return db.query(models.Software).filter(models.Software.id == id).first()

def create_software(db: Session, software: schemas.SoftwareSchema):
    tractor_models_json = _serialize_tractor_models(software.tractor_model)

    db_software = models.Software(
        path=software.path,
        release_date=software.release_date,
        end_actuality=software.end_actuality,
        description=software.description,
        producer=software.producer,
        is_actual=software.is_actual,
        is_archive=software.is_archive,
        is_critical=software.is_critical,
        status=software.status,
        tractor_model=tractor_models_json,
        previous_sw_version=software.previous_sw_version,
        path_instruction=software.path_instruction
    )
    db.add(db_software)
    db.commit()
    db.refresh(db_software)

    db_software.tractor_model = _deserialize_tractor_models(db_software.tractor_model)
    return db_software

def delete_software(db: Session, id: int):
    software = db.query(models.Software).filter(models.Software.id == id).first()
    if software is None:
        return False
    db.delete(software)
    db.commit()
    return True

def update_software(db: Session, sw_id: int, software_update: schemas.SoftwareUpdate):
    db_sw = db.query(models.Software).filter(models.Software.id == sw_id).first()
    if not db_sw:
        raise HTTPException(status_code=404, detail="Software not found")
    for field, value in software_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(db_sw, field, value)
    try:
        db.commit()
        db.refresh(db_sw)
        return db_sw
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Update failed due to integrity constraint")
    
def secure_filename(filename: str) -> str:
    """Очищает имя файла от опасных символов"""
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    return filename.strip("._")


def save_uploaded_file(file, filename: str) -> str:
    """Сохраняет файл с уникальным именем"""
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex}_{secure_filename(filename)}"
    file_path = os.path.join(config.UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as f:
        if hasattr(file, 'read'):  # UploadFile
            while chunk := file.file.read(8192):
                f.write(chunk)
        else:  # bytes
            f.write(file)
    
    return safe_filename


def check_file_size(file: UploadFile, max_size: int) -> int:
    """Проверяет размер файла"""
    size = 0
    chunk_size = 8192
    original_pos = file.file.tell()
    file.file.seek(0)
    
    while True:
        chunk = file.file.read(chunk_size)
        if not chunk:
            break
        size += len(chunk)
        if size > max_size:
            file.file.seek(original_pos)
            raise HTTPException(
                status_code=413,
                detail=f"File size too large: {size + len(chunk)} bytes > {max_size} bytes"
            )
    
    file.file.seek(original_pos)
    return size


def assign_software_to_components(
    db: Session,
    file: UploadFile,
    instruction_file: UploadFile,
    software_data: schemas.AssignSoftwareRequest,
    base_name: str
) -> schemas.SoftwareResponse:
    """
    Назначает ПО нескольким компонентам и тракторам
    
    Args:
        db: Сессия базы данных
        file: Файл ПО
        software_data: Данные ПО из схемы
        filename: Оригинальное имя файла
        base_name: Базовое имя для name/inner_name
    
    Returns:
        schemas.SoftwareResponse: Данные созданного ПО
    """
    check_file_size(file, config.MAX_FILE_SIZE)
    check_file_size(instruction_file, config.MAX_FILE_SIZE)
    
    saved_filename = None
    saved_instruction_filename = None
    
    try:
        # 1. Сохраняем файл
        saved_filename = save_uploaded_file(file, file.filename)
        logger.info(f"[assign_software] Сохранён файл ПО: {saved_filename}")
        
        # Сохраняем интструкции
        saved_instruction_filename = save_uploaded_file(instruction_file, instruction_file.filename)
        logger.info(f"[assign_software] Сохранён файл инструкции: {saved_instruction_filename}")

        # 2. Валидация массивов компонентов
        n_models = len(software_data.component_models)
        n_types = len(software_data.component_types)
        n_producers = len(software_data.component_producers)
        
        if not (n_models == n_types == n_producers):
            raise HTTPException(
                400,
                f"Несоответствие длин массивов: component_models={n_models}, "
                f"component_types={n_types}, component_producers={n_producers}"
            )
        
        if n_models == 0:
            raise HTTPException(400, "Должен быть указан хотя бы один компонент")
        
        # 3. Создаём ПО
        fw = models.Software(
            path=saved_filename,
            release_date=software_data.software_release_date,
            description=software_data.software_description,
            is_actual=software_data.software_is_actual,
            is_archive=software_data.software_is_archive,
            is_critical=software_data.software_is_critical,
            status=software_data.software_status,
            tractor_model=json.dumps(software_data.software_tractor_models),  # Сохраняем как JSON
            producer=software_data.software_producer,
            previous_sw_version=software_data.software_previous_version,
            path_instruction=saved_instruction_filename
        )
        db.add(fw)
        db.flush()  # Получаем fw.id
        
        logger.info(f"[assign_software] Создано ПО id={fw.id}, producer={fw.producer}")
        
        # 4. Создаём связи с компонентами
        for i in range(n_models):
            comp_model = software_data.component_models[i]
            comp_type = software_data.component_types[i]
            comp_producer = software_data.component_producers[i]
            
            # Ищем или создаём компонент
            component = db.query(models.Component).filter(
                models.Component.name == comp_model,
                models.Component.type == comp_type,
                models.Component.producer == comp_producer
            ).first()
            
            if not component:
                component = models.Component(
                    type=comp_type,
                    name=comp_model,
                    producer=comp_producer
                )
                db.add(component)
                db.flush()
                logger.info(f"[assign_software] Создан компонент id={component.id}, name={comp_model}")
            
            # Создаём связь ПО-Компонент
            link = models.Software_Component_Link(
                component_id=component.id,
                software_id=fw.id
            )
            db.add(link)
            db.flush()
            
            logger.info(f"[assign_software] Создана связь ПО-Компонент link_id={link.id}")
        # 5. Коммитим все изменения
        db.commit()
        db.refresh(fw)
        
        logger.info(f"[assign_software] Успешно завершено для ПО id={fw.id}")
        
        # 6. Возвращаем ответ
        return schemas.SoftwareResponse(
            id=fw.id,
            name=fw.producer,  # Используем producer как name для совместимости
            inner_name=base_name,  # Базовое имя файла
            release_date=fw.release_date,
            description=fw.description,
            producer=fw.producer
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[assign_software] Ошибка: {str(e)}", exc_info=True)
        
        # Удаляем файл при ошибке
        if saved_filename:
            path = os.path.join(config.UPLOAD_DIR, saved_filename)
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"[assign_software] Удалён файл {saved_filename} при откате")
        
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при сохранении ПО: {str(e)}"
        )

# def update_software_instruction(
#     db: Session,
#     software_id: int,
#     instruction_file: UploadFile
# ) -> schemas.SoftwareMetadata:
#     """
#     Обновляет файл инструкции для существующего ПО
    
#     Args:
#         db: Сессия базы данных
#         software_id: ID ПО
#         instruction_file: Новый файл инструкции
    
#     Returns:
#         schemas.SoftwareMetadata: Метаданные ПО
#     """
#     fw = db.query(models.Software).filter(models.Software.id == software_id).first()
#     if not fw:
#         raise HTTPException(404, f"Software with id {software_id} not found")
    
#     # Удаляем старую инструкцию если есть
#     if fw.path_instruction:
#         old_path = os.path.join(config.UPLOAD_DIR, fw.path_instruction)
#         if os.path.exists(old_path):
#             try:
#                 os.remove(old_path)
#                 logger.info(f"[update_instruction] Удалена старая инструкция: {old_path}")
#             except Exception as e:
#                 logger.warning(f"[update_instruction] Не удалось удалить старую инструкцию: {str(e)}")
    
#     # Сохраняем новую инструкцию
#     check_file_size(instruction_file, config.MAX_FILE_SIZE)
#     saved_instruction_filename = save_uploaded_file(instruction_file, instruction_file.filename)
    
#     # Обновляем путь в БД
#     fw.path_instruction = saved_instruction_filename
#     db.commit()
#     db.refresh(fw)
    
#     logger.info(f"[update_instruction] Обновлена инструкция для ПО id={software_id}")
    
#     return get_software_metadata(db, software_id)

# def get_software_full(db: Session, software_id: int):
#     """Получает ПО и проверяет существование файла"""
#     fw = db.query(models.Software).filter(models.Software.id == software_id).first()
#     if not fw:
#         raise HTTPException(404, "Software not found")
    
#     full_path = os.path.join(config.UPLOAD_DIR, fw.path)
#     if not os.path.exists(full_path):
#         raise HTTPException(404, f"File '{fw.path}' not found on disk")
    
#     return fw, full_path


# def get_software_metadata(db: Session, software_id: int) -> schemas.SoftwareMetadata:
#     """Получает метаданные ПО включая информацию об инструкции"""
#     fw, _ = get_software_full(db, software_id)
    
#     # ← ИСПРАВЛЕНО: используем producer вместо name
#     safe_name = re.sub(r'[<>:"/\\|?*]', '_', fw.producer) if fw.producer else fw.path
#     download_name = f"{safe_name}.bin"
    
#     has_instruction = bool(fw.path_instruction)
#     instruction_filename = None
#     if has_instruction:
#         instruction_filename = os.path.basename(fw.path_instruction)
    
#     return schemas.SoftwareMetadata(
#         id=fw.id,
#         name=fw.producer,
#         filename_original=fw.path,
#         filename_for_download=download_name,
#         has_instruction=has_instruction,
#         instruction_filename=instruction_filename
#     )


# def get_software_file_path(db: Session, software_id: int) -> str:
#     """Получает полный путь к файлу ПО"""
#     _, file_path = get_software_full(db, software_id)
#     return file_path


# def get_software_file_info(db: Session, software_id: int) -> schemas.SoftwareFileLocation:
#     """Получает информацию о файле ПО"""
#     _, file_path = get_software_full(db, software_id)
    
#     return schemas.SoftwareFileLocation(
#         full_path=file_path,
#         size_bytes=os.path.getsize(file_path),
#         exists=True
#     )


# def get_instruction_file_path(db: Session, software_id: int) -> str:
#     """Получает полный путь к файлу инструкции"""
#     fw = db.query(models.Software).filter(models.Software.id == software_id).first()
#     if not fw:
#         raise HTTPException(404, "Software not found")
    
#     if not fw.path_instruction:
#         raise HTTPException(404, "Instruction file not found for this software")
    
#     full_path = os.path.join(config.UPLOAD_DIR, fw.path_instruction)
#     if not os.path.exists(full_path):
#         raise HTTPException(404, f"Instruction file '{fw.path_instruction}' not found on disk")
    
#     return full_path


# def get_instruction_file_info(db: Session, software_id: int) -> schemas.SoftwareInstructionLocation:
#     """Получает информацию о файле инструкции"""
#     fw = db.query(models.Software).filter(models.Software.id == software_id).first()
#     if not fw:
#         raise HTTPException(404, "Software not found")
    
#     if not fw.path_instruction:
#         raise HTTPException(404, "Instruction file not found for this software")
    
#     full_path = os.path.join(config.UPLOAD_DIR, fw.path_instruction)
#     if not os.path.exists(full_path):
#         raise HTTPException(404, f"Instruction file '{fw.path_instruction}' not found on disk")
    
#     return schemas.SoftwareInstructionLocation(
#         full_path=full_path,
#         size_bytes=os.path.getsize(full_path),
#         exists=True,
#         filename=os.path.basename(fw.path_instruction)
#     )


# def download_software_file(db: Session, software_id: int):
#     """Подготавливает файл ПО для скачивания"""
#     fw, file_path = get_software_full(db, software_id)
    
#     safe_name = re.sub(r'[<>:"/\\|?*]', '_', fw.name) if fw.name else fw.path
#     download_name = f"{safe_name}.bin" if fw.name else fw.path
    
#     return {
#         "file_path": file_path,
#         "filename": download_name,
#         "software_id": fw.id
#     }


# def download_instruction_file(db: Session, software_id: int):
#     """Подготавливает файл инструкции для скачивания"""
#     fw = db.query(models.Software).filter(models.Software.id == software_id).first()
#     if not fw:
#         raise HTTPException(404, "Software not found")
    
#     if not fw.path_instruction:
#         raise HTTPException(404, "Instruction file not found for this software")
    
#     full_path = os.path.join(config.UPLOAD_DIR, fw.path_instruction)
#     if not os.path.exists(full_path):
#         raise HTTPException(404, f"Instruction file not found on disk")
    
#     download_name = os.path.basename(fw.path_instruction)
    
#     return {
#         "file_path": full_path,
#         "filename": download_name,
#         "software_id": fw.id
#     }