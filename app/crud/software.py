from sqlalchemy.orm import Session
from .. import models, schemas, config
from sqlalchemy import select
from fastapi import HTTPException, status, Depends, Form, File, UploadFile
import uuid
import re
import os
from datetime import datetime, date
import logging
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from typing import Optional
import json
import csv
from ..crud.notifications import create_notifications_for_software_update  # добавьте импорт

logger = logging.getLogger(__name__)
# Ограничение глубины распаковки обёрток (кавычки/скобки) для защиты от зацикливания на битых данных.
MAX_MODEL_NAME_CLEANUP_ITERATIONS = 5

#Software
def _serialize_tractor_models(models_list: list) -> str:
    """Сериализует список моделей в JSON-строку"""
    return json.dumps(models_list, ensure_ascii=False)

def normalize_tractor_model(raw: str) -> str:
    """
    Приводит поле tractor_model к стандартному JSON-списку.
    Обрабатывает:
      - валидный JSON (оставляет как есть)
      - строки вида "{K-7}" -> ["K-7"]
      - строки вида "{K-525,K-7,K-742МСТ}" -> ["K-525","K-7","K-742МСТ"]
      - многократно экранированные JSON (как ранее)
    """
    if not raw:
        return "[]"
    
    # Многократная попытка распарсить JSON
    current = raw
    for _ in range(5):
        try:
            parsed = json.loads(current)
            if isinstance(parsed, list):
                # Рекурсивно разбираем элементы (на случай склеек внутри)
                new_list = []
                for item in parsed:
                    if isinstance(item, str) and item.startswith('{') and item.endswith('}'):
                        # Разбираем внутренность фигурных скобок
                        inner = item[1:-1]
                        parts = [p.strip() for p in inner.split(',') if p.strip()]
                        new_list.extend(parts)
                    else:
                        new_list.append(item)
                return json.dumps(new_list, ensure_ascii=False)
            current = parsed
        except (json.JSONDecodeError, TypeError):
            break
    
    # Если не JSON, но похоже на "{...}"
    if isinstance(raw, str) and raw.startswith('{') and raw.endswith('}'):
        inner = raw[1:-1]
        parts = [p.strip() for p in inner.split(',') if p.strip()]
        return json.dumps(parts, ensure_ascii=False)
    
    # Если ничего не помогло – одиночная модель
    return json.dumps([raw], ensure_ascii=False)

def _deserialize_tractor_models(models_str: str) -> list:
    """Десериализует JSON-строку в список моделей"""
    if not models_str:
        return []

    def _clean_model_name(value: str) -> str:
        cleaned = value.strip()
        for _ in range(MAX_MODEL_NAME_CLEANUP_ITERATIONS):
            prev = cleaned
            if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
                cleaned = cleaned[1:-1].strip()
            if len(cleaned) >= 2 and cleaned[0] == "(" and cleaned[-1] == ")":
                cleaned = cleaned[1:-1].strip()
            if cleaned == prev:
                break
        return cleaned

    def _parse_pg_array(raw_value: str) -> list[str]:
        if not (isinstance(raw_value, str) and raw_value.startswith("{") and raw_value.endswith("}")):
            raise ValueError("Invalid PostgreSQL array literal format")
        inner = raw_value[1:-1].strip()
        if not inner:
            return []
        pg_array_values = next(csv.reader([inner], delimiter=",", quotechar='"', escapechar="\\"))
        return [v for v in pg_array_values if v]

    def _prepare_list(values: list) -> list[str]:
        result = []
        for item in values:
            if isinstance(item, str):
                normalized_item = item.strip()
                if normalized_item.startswith("{") and normalized_item.endswith("}"):
                    try:
                        result.extend(_prepare_list(_parse_pg_array(normalized_item)))
                        continue
                    except (csv.Error, ValueError, TypeError) as exc:
                        logger.debug("[_deserialize_tractor_models] parse nested PG array failed: %s", exc)
                normalized = _clean_model_name(normalized_item)
                if normalized:
                    result.append(normalized)
            elif item is not None:
                normalized = _clean_model_name(str(item))
                if normalized:
                    result.append(normalized)
        return result

    if isinstance(models_str, str):
        raw = models_str.strip()
        if raw.startswith("{") and raw.endswith("}"):
            try:
                return _prepare_list(_parse_pg_array(raw))
            except (csv.Error, ValueError, TypeError) as exc:
                logger.debug("[_deserialize_tractor_models] parse PG array failed: %s", exc)

    try:
        loaded = json.loads(models_str)
        if isinstance(loaded, list):
            return _prepare_list(loaded)
        if isinstance(loaded, str):
            loaded = loaded.strip()
            if loaded.startswith("{") and loaded.endswith("}"):
                try:
                    return _prepare_list(_parse_pg_array(loaded))
                except (csv.Error, ValueError, TypeError) as exc:
                    logger.debug("[_deserialize_tractor_models] parse PG array from JSON string failed: %s", exc)
            cleaned = _clean_model_name(loaded)
            return [cleaned] if cleaned else []
        return []
    except (json.JSONDecodeError, TypeError):
        # Для обратной совместимости - если старая строка
        cleaned = _clean_model_name(models_str)
        return [cleaned] if cleaned else []

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

def delete_software_component_link_by_ids(
    db: Session, 
    component_id: int, 
    software_id: int
) -> bool:
    """
    Удаляет связь ПО-компонент и все зависимые записи в tractor_software_and_component_links
    """
    link = db.query(models.Software_Component_Link).filter(
        models.Software_Component_Link.component_id == component_id,
        models.Software_Component_Link.software_id == software_id
    ).first()
    
    if not link:
        return False
    
    dependent_links = db.query(models.Tractor_Software_And_Component_Link).filter(
        models.Tractor_Software_And_Component_Link.soft_comp_link_id == link.id
    ).all()
    
    for dep_link in dependent_links:
        db.delete(dep_link)

    db.delete(link)
    db.commit()
    return True

# app/crud/software.py

def delete_all_software_component_links(db: Session, software_id: int) -> int:
    """
    Удаляет ВСЕ связи указанного ПО с компонентами и все зависимые записи
    
    Returns:
        int: количество удалённых связей
    """
    # 1. Находим все связи ПО с компонентами
    links = db.query(models.Software_Component_Link).filter(
        models.Software_Component_Link.software_id == software_id
    ).all()
    
    deleted_count = 0
    
    for link in links:
        # 2. Удаляем зависимые записи в tractor_software_and_component_links
        db.query(models.Tractor_Software_And_Component_Link).filter(
            models.Tractor_Software_And_Component_Link.soft_comp_link_id == link.id
        ).delete(synchronize_session=False)
        
        # 3. Удаляем саму связь
        db.delete(link)
        deleted_count += 1
    
    db.commit()
    return deleted_count

def delete_software_with_links(db: Session, software_id: int) -> bool:
    """
    Полное удаление ПО:
    1. Удаляет все связи с компонентами
    2. Очищает ссылки previous_sw_version у других записей ПО
    3. Удаляет файлы ПО с диска
    4. Удаляет запись ПО из БД
    """
    # 1. Получаем ПО для удаления файлов
    software = db.query(models.Software).filter(
        models.Software.id == software_id
    ).first()
    
    if not software:
        return False
    
    # 2. Удаляем все связи ПО с компонентами
    delete_all_software_component_links(db, software_id)
    
    # 3. Очищаем ссылки previous_sw_version у других записей ПО
    #    которые ссылаются на удаляемое ПО
    dependent_softwares = db.query(models.Software).filter(
        models.Software.previous_sw_version == software_id
    ).all()
    
    for dep_sw in dependent_softwares:
        dep_sw.previous_sw_version = None  # Разрываем ссылку
        logger.info(f"[delete_software] очищена ссылка previous_sw_version у ПО {dep_sw.id}")
    
    # 4. Удаляем файл ПО с диска (если есть)
    if software.path:
        file_path = os.path.join(config.UPLOAD_DIR, software.path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"[delete_software] удалён файл: {software.path}")
            except OSError as e:
                logger.error(f"[delete_software] ошибка удаления файла: {e}")
    
    # 5. Удаляем инструкцию (если есть)
    if software.path_instruction:
        instr_path = os.path.join(config.UPLOAD_DIR, software.path_instruction)
        if os.path.exists(instr_path):
            try:
                os.remove(instr_path)
                logger.info(f"[delete_software] удалена инструкция: {software.path_instruction}")
            except OSError as e:
                logger.error(f"[delete_software] ошибка удаления инструкции: {e}")
    
    # 6. Удаляем запись ПО из БД
    db.delete(software)
    db.commit()  # commit после всех операций
    
    logger.info(f"[delete_software] ПО {software_id} полностью удалено")
    return True

def update_software(db: Session, sw_id: int, software_update: schemas.SoftwareUpdate):
    db_sw = db.query(models.Software).filter(models.Software.id == sw_id).first()
    if not db_sw:
        raise HTTPException(status_code=404, detail="Software not found")
    
    update_data = software_update.model_dump(exclude_unset=True)
    
    # Особое поле: tractor_model
    if "tractor_model" in update_data:
        raw_value = update_data["tractor_model"]
        # Если пришёл список – сериализуем
        if isinstance(raw_value, list):
            update_data["tractor_model"] = _serialize_tractor_models(raw_value)
        # Если пришла строка – возможно, это уже JSON, но проверим на двойную сериализацию
        elif isinstance(raw_value, str):
            # Попробуем десериализовать и снова сериализовать для нормализации
            try:
                as_list = json.loads(raw_value)
                if isinstance(as_list, list):
                    update_data["tractor_model"] = _serialize_tractor_models(as_list)
            except:
                # Не JSON – возможно, ошибочная строка, лучше сохранить как есть?
                # Но для чистоты обернём в список
                update_data["tractor_model"] = _serialize_tractor_models([raw_value])
    
    for field, value in update_data.items():
        setattr(db_sw, field, value)
    
    db.commit()
    db.refresh(db_sw)

     # 👇 НОВЫЙ КОД: создаём уведомления для дилеров после успешного обновления
    create_notifications_for_software_update(db, sw_id, db_sw)
    # Для ответа десериализуем
    db_sw.tractor_model = _deserialize_tractor_models(db_sw.tractor_model)
    return db_sw
    
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
    software_data: schemas.AssignSoftwareRequest,
    instruction_file: Optional[UploadFile] = None
) -> schemas.SoftwareResponse:
    """
    Назначает ПО нескольким компонентам и тракторам
    """
    # 1. Проверка размера файла ПО
    check_file_size(file, config.MAX_FILE_SIZE)
    
    # 2. Проверка размера файла инструкции (если передан)
    if instruction_file and instruction_file.filename:
        check_file_size(instruction_file, config.MAX_FILE_SIZE)
    
    saved_filename = None
    saved_instruction_filename = None
    
    try:
        # 3. Сохраняем файл ПО
        saved_filename = save_uploaded_file(file, file.filename)
        logger.info(f"[assign_software] Сохранён файл ПО: {saved_filename}")
        
        # 4. Сохраняем инструкцию ТОЛЬКО если файл передан
        if instruction_file and instruction_file.filename:
            saved_instruction_filename = save_uploaded_file(instruction_file, instruction_file.filename)
            logger.info(f"[assign_software] Сохранён файл инструкции: {saved_instruction_filename}")
        
        # 5. Валидация массивов компонентов
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
        
        # 6. Формируем name из сохранённого имени файла БЕЗ расширения
        name_without_extension = os.path.splitext(saved_filename)[0]

        if len(name_without_extension) > 33:
            name_without_extension = name_without_extension[33:]
            logger.info(f"[assign_software] Обрезан name, удалены первые 33 символа: {name_without_extension}")
        else:
            # Если имя короче 33 символов, можно либо оставить как есть, либо установить пустую строку
            # По умолчанию оставляем как есть
            logger.warning(f"[assign_software] Длина name меньше 33 символов ({len(name_without_extension)}), обрезка не выполнена")
        
        # 7. Создаём ПО
        fw = models.Software(
            name=name_without_extension,  # <-- name = путь без расширения
            path=saved_filename,           # <-- path = полный путь с расширением
            release_date=software_data.software_release_date,
            description=software_data.software_description,
            is_actual=software_data.software_is_actual,
            is_archive=software_data.software_is_archive,
            is_critical=software_data.software_is_critical,
            status=software_data.software_status,
            tractor_model=_serialize_tractor_models(software_data.software_tractor_models),
            producer=software_data.software_producer,
            previous_sw_version=software_data.software_previous_version,
            path_instruction=saved_instruction_filename 
        )
        db.add(fw)
        db.flush()
        
        logger.info(f"[assign_software] Created software id={fw.id}, name={fw.name}, path={fw.path}")
        
        # 8. Создаём связи с компонентами
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
                    producer=comp_producer,
                )
                db.add(component)
                db.flush()
                logger.info(f"[assign_software] Created component id={component.id}, model={comp_model}")
            
            # Создаём связь ПО-Компонент
            link = models.Software_Component_Link(
                component_id=component.id,
                software_id=fw.id
            )
            db.add(link)
            db.flush()
            
            logger.info(f"[assign_software] Created software-component link link_id={link.id}")
        
        # 9. Деактивируем старые версии ПО
        previous_sw_version_past = fw.previous_sw_version
        while previous_sw_version_past != None:
            prev_fw = db.query(models.Software).filter(models.Software.id == previous_sw_version_past).first()
            if prev_fw:
                prev_fw.is_actual = False
                prev_fw.end_actuality = datetime.utcnow()
                previous_sw_version_past = prev_fw.previous_sw_version
                logger.info(f"[assign_software] Deactivated old software version id={prev_fw.id}")
            else:
                logger.warning(f"[assign_software] Previous software version {previous_sw_version_past} not found")
                break
        
        # 10. Коммитим все изменения
        db.commit()
        db.refresh(fw)
        
        logger.info(f"[assign_software] Successfully completed for software id={fw.id}")
        
        # 11. Возвращаем ответ
        # Получаем оригинальное имя файла без расширения для inner_name
        original_name_without_ext = os.path.splitext(file.filename)[0] if file.filename else "unknown"
        
        return schemas.SoftwareResponse(
            id=fw.id,
            name=fw.name,  # путь без расширения
            inner_name=original_name_without_ext,  # оригинальное имя файла без расширения
            release_date=fw.release_date,
            description=fw.description,
            download_url=f"/software/download/{fw.id}"
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[assign_software] Ошибка: {str(e)}", exc_info=True)
        
        # Удаляем файлы при ошибке
        if saved_filename:
            path = os.path.join(config.UPLOAD_DIR, saved_filename)
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"[assign_software] Удалён файл {saved_filename} при откате")
        
        if saved_instruction_filename:
            path = os.path.join(config.UPLOAD_DIR, saved_instruction_filename)
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"[assign_software] Удалена инструкция {saved_instruction_filename} при откате")
        
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при сохранении ПО: {str(e)}"
        )
    
def get_software_full(db: Session, software_id: int):
    """Получает ПО и проверяет существование файла"""
    fw = db.query(models.Software).filter(models.Software.id == software_id).first()
    if not fw:
        raise HTTPException(404, "Software not found")
    
    full_path = os.path.join(config.UPLOAD_DIR, fw.path)
    if not os.path.exists(full_path):
        raise HTTPException(404, f"File '{fw.path}' not found on disk")
    
    return fw, full_path

def extract_original_filename(stored_name: str) -> str:
    """Срезает первые 33 символа (32 UUID + 1 подчеркивание)"""
    if not stored_name:
        return ""
    
    # Если длина строки больше 33 символов и есть подчеркивание на 33-й позиции
    if len(stored_name) > 33 and stored_name[32] == '_':
        return stored_name[33:]  # Возвращаем всё после 33-го символа
    
    # Иначе возвращаем как есть
    return stored_name

def download_software_file(db: Session, software_id: int):
    """Подготавливает файл ПО для скачивания с оригинальным именем"""
    fw, file_path = get_software_full(db, software_id)
    
    # Извлекаем оригинальное имя файла (с расширением)
    original_filename = extract_original_filename(os.path.basename(fw.path))
    
    return {
        "file_path": file_path,
        "filename": original_filename,  # ← оригинальное имя, например "firmware_v2.bin"
        "software_id": fw.id
    }
    
def download_instruction_file(db: Session, software_id: int):
    """Подготавливает файл инструкции для скачивания с оригинальным именем"""
    fw = db.query(models.Software).filter(models.Software.id == software_id).first()
    if not fw:
        raise HTTPException(404, "Software not found")
    
    if not fw.path_instruction:
        raise HTTPException(404, "Instruction file not found for this software")
    
    full_path = os.path.join(config.UPLOAD_DIR, fw.path_instruction)
    if not os.path.exists(full_path):
        raise HTTPException(404, f"Instruction file not found on disk")
    
    # Извлекаем оригинальное имя инструкции
    original_filename = extract_original_filename(os.path.basename(fw.path_instruction))
    
    return {
        "file_path": full_path,
        "filename": original_filename,  # ← оригинальное имя, например "manual.pdf"
        "software_id": fw.id
    }

def get_software_metadata(db: Session, software_id: int) -> schemas.SoftwareMetadata:
    """Получает метаданные ПО с оригинальными именами файлов"""
    fw, _ = get_software_full(db, software_id)
    
    # Оригинальное имя файла ПО
    original_filename = extract_original_filename(os.path.basename(fw.path))
    
    has_instruction = bool(fw.path_instruction)
    instruction_filename = None
    if has_instruction:
        instruction_filename = extract_original_filename(os.path.basename(fw.path_instruction))
    
    return schemas.SoftwareMetadata(
        id=fw.id,
        name=fw.producer,  # producer как name для совместимости
        inner_name=None,
        filename_original=original_filename,  # ← оригинальное имя
        filename_for_download=original_filename,  # ← для скачивания
        has_instruction=has_instruction,
        instruction_filename=instruction_filename,
        release_date=fw.release_date
    )

def update_software_file(
    db: Session,
    software_id: int,
    file: UploadFile
) -> schemas.SoftwareMetadata:
    """
    Updates the main file for an existing software entry
    """
    from .. import config
    
    # 1. Find the software
    software_item = get_software_by_id(db, software_id)
    if not software_item:
        raise HTTPException(status_code=404, detail="Software not found")
    
    # 2. Validate file size
    check_file_size(file, config.MAX_FILE_SIZE)
    
    # 3. Save the new file
    saved_filename = save_uploaded_file(file, file.filename)
    logger.info(f"[update_software_file] Saved new software file: {saved_filename}")
    
    # 4. Remove the old file if it exists
    if software_item.path:
        old_path = os.path.join(config.UPLOAD_DIR, software_item.path)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
                logger.info(f"[update_software_file] Removed old software file: {software_item.path}")
            except OSError as e:
                logger.error(f"[update_software_file] Error removing old file: {e}")
    
    # 5. Update the database record
    software_item.path = saved_filename
    
    # 👇 ДОБАВИТЬ ЭТУ ЛОГИКУ - обновляем name из path без расширения
    name_without_extension = os.path.splitext(saved_filename)[0]
    if len(name_without_extension) > 33:
        name_without_extension = name_without_extension[33:]  # Удаляем первые 33 символа
        logger.info(f"[update_software_file] Trimmed name, removed first 33 chars: {name_without_extension}")
    else:
        logger.warning(f"[update_software_file] Name length ({len(name_without_extension)}) <= 33, no trim applied")
    
    software_item.name = name_without_extension
    
    db.commit()
    db.refresh(software_item)
    
    # 6. Return metadata
    original_filename = extract_original_filename(saved_filename)
    
    return schemas.SoftwareMetadata(
        id=software_item.id,
        name=software_item.name,  # Теперь здесь будет name без расширения
        inner_name=None,
        filename_original=original_filename,
        filename_for_download=original_filename,
        has_instruction=bool(software_item.path_instruction),
        instruction_filename=extract_original_filename(os.path.basename(software_item.path_instruction)) if software_item.path_instruction else None,
        release_date=software_item.release_date
    )

def update_software_instruction(
    db: Session,
    software_id: int,
    instruction_file: UploadFile
) -> schemas.SoftwareMetadata:
    """
    Обновляет файл инструкции для существующего ПО
    """
    from .. import config
    
    # 1. Находим ПО
    software_item = get_software_by_id(db, software_id)
    if not software_item:
        raise HTTPException(status_code=404, detail="Software not found")
    
    # 2. Проверяем размер файла
    check_file_size(instruction_file, config.MAX_FILE_SIZE)
    
    # 3. Удаляем старую инструкцию, если она есть
    if software_item.path_instruction:
        old_path = os.path.join(config.UPLOAD_DIR, software_item.path_instruction)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
                logger.info(f"[update_software_instruction] удалена старая инструкция: {software_item.path_instruction}")
            except OSError as e:
                logger.error(f"[update_software_instruction] ошибка удаления: {e}")
    
    # 4. Сохраняем новую инструкцию
    saved_filename = save_uploaded_file(instruction_file, instruction_file.filename)
    logger.info(f"[update_software_instruction] сохранена новая инструкция: {saved_filename}")
    
    # 5. Обновляем запись в БД
    software_item.path_instruction = saved_filename
    db.commit()
    db.refresh(software_item)
    
    # 6. Возвращаем метаданные в правильном формате
    original_filename = extract_original_filename(saved_filename)
    
    return schemas.SoftwareMetadata(
        id=software_item.id,
        name=software_item.producer,  # обязательное поле
        inner_name=None,
        filename_original=original_filename,  # обязательное поле
        filename_for_download=original_filename,  # обязательное поле
        has_instruction=True,
        instruction_filename=original_filename,
        release_date=software_item.release_date
    )

def get_software_file_info(db: Session, software_id: int):
    """Get information about a software file without returning the file itself"""
    from sqlalchemy import func
    from .. import config
    import os
    
    software = db.query(models.Software).filter(models.Software.id == software_id).first()
    if not software:
        raise HTTPException(404, "Software not found")
    
    full_path = os.path.join(config.UPLOAD_DIR, software.path)
    exists = os.path.exists(full_path)
    
    if exists:
        size_bytes = os.path.getsize(full_path)
    else:
        size_bytes = 0
    
    # Create a simple object to return file info
    class FileInfo:
        def __init__(self, exists, size_bytes, full_path):
            self.exists = exists
            self.size_bytes = size_bytes
            self.full_path = full_path
    
    return FileInfo(exists, size_bytes, full_path)


def get_instruction_file_info(db: Session, software_id: int):
    """Get information about a software instruction file"""
    from sqlalchemy import func
    from .. import config
    import os
    
    software = db.query(models.Software).filter(models.Software.id == software_id).first()
    if not software or not software.path_instruction:
        raise HTTPException(404, "Software or instruction file not found")
    
    full_path = os.path.join(config.UPLOAD_DIR, software.path_instruction)
    exists = os.path.exists(full_path)
    
    if exists:
        size_bytes = os.path.getsize(full_path)
    else:
        size_bytes = 0
    
    class FileInfo:
        def __init__(self, exists, size_bytes, full_path, filename):
            self.exists = exists
            self.size_bytes = size_bytes
            self.full_path = full_path
            self.filename = filename
    
    return FileInfo(exists, size_bytes, full_path, os.path.basename(software.path_instruction))

  # backend/utils/validators.py (новый файл

def validate_tractor_models(models: list[str]) -> None:
    """
    Проверяет список моделей тракторов:
    - не пустые строки
    - длина не более 10 символов
    - только разрешённые символы: буквы (русские/английские), цифры, дефис, подчёркивание
    """
    allowed_pattern = re.compile(r'^[A-Za-zА-Яа-я0-9_-]+$')
    
    for model in models:
        if not model or not model.strip():
            raise HTTPException(400, f"Модель трактора не может быть пустой: '{model}'")
        if len(model) > 10:
            raise HTTPException(400, f"Модель трактора '{model}' превышает максимальную длину 10 символов")
        if not allowed_pattern.match(model):
            raise HTTPException(400, f"Модель трактора '{model}' содержит недопустимые символы. Разрешены: буквы, цифры, дефис, подчёркивание")
