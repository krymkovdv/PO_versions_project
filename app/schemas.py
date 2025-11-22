from pydantic import BaseModel, field_validator, Field
from datetime import datetime, date
from typing import Optional, List
import re
from sqlalchemy import or_



# class Pagination(BaseModel):
#     page: int = 1
#     size: int = 50

class UserSchema(BaseModel):
    id: int
    username: str
    password_hash: str
    role: str


def wildcard_to_psql_regex(pattern: str) -> str:
    if not pattern:
        return ".*"
    
    # Шаг 1: обработка ~ → - внутри [...], и экранирование \
    processed = []
    in_brackets = False
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == '[':
            in_brackets = True
            processed.append(char)
        elif char == ']':
            in_brackets = False
            processed.append(char)
        elif char == '~' and in_brackets:
            processed.append('-')  # [0~9] → [0-9]
        elif char == '\\' and i + 1 < len(pattern):
            # Экранируем \*, \?, \[, \], \!, \~, \\
            next_char = pattern[i + 1]
            if next_char in '*?[]!~\\':
                processed.append(next_char)  # \* → *, но буквально
                i += 1  # пропускаем следующий символ
            else:
                processed.append('\\')
                processed.append(next_char)
                i += 1
        else:
            processed.append(char)
        i += 1
    
    pattern_clean = ''.join(processed)
    
    # Шаг 2: экранируем всё как regex, затем восстанавливаем wildcards
    escaped = re.escape(pattern_clean)
    regex = (
        escaped
        .replace(r'\*', '.*')   # * → .*
        .replace(r'\?', '.')    # ? → .
        .replace(r'\[', '[')    # [ → [
        .replace(r'\]', ']')    # ] → ]
    )
    # [!...] → [^...]
    regex = re.sub(r'\[\\!', '[^', regex)
    
    return regex

def is_safe_regex(regex: str) -> bool:
    # Простая защита
    if len(regex) > 200:
        return False
    # Запрещаем (a+)*, .{100,}, и повторяющиеся .*.*
    if re.search(r'\([^)]*\)[+*{]|[{]\d+,\d+[}]|\.\*\.\*', regex):
        return False
    return True

class TractorsSchema(BaseModel):
    id: int
    model: str
    vin: str
    oh_hour: int
    last_activity: Optional[datetime] = None
    assembly_date: Optional[datetime] = None
    region: str
    consumer: str
    serv_center: str
    
class ComponentSchema(BaseModel):
    id: int
    type: str
    model: str
    mounting_date: date
    comp_ser_num: str
    tractor_id: int
    number_of_parts: int
    producer_comp: str

class TelemetryComponentSchema(BaseModel):
    id: int
    software: int
    tractor: int
    component: int
    component_part_id: int
    time_rec: datetime

class SoftwareSchema(BaseModel):
    id: int
    path: str
    name: str
    inner_name: str
    release_date: datetime
    description: str

class ComponentPartSchema(BaseModel):
    id: int
    component: int
    part_number: str
    part_type: str
    current_sw_version: int
    recommend_sw_version: int
    is_major: bool
    not_recom: Optional[str] = None
    next_ver: str

class SoftwareComponentsSchema(BaseModel):
    id: int
    component_part_id: int
    software_id: int
    is_major: bool
    status: str
    date_change: datetime
    not_recom: str
    date_change_record: datetime

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in {'s', 't', 'b', 'o'}:
            raise ValueError("Status must be one of: 's', 't', 'b', 'o'")
        return v

# # Для фильтра СХЕМА
class ComponentInfoRequest(BaseModel):
    trac_model: List[str] = []
    type_comp: List[str] = []
    model_comp: str = ''

class TractorFilter(BaseModel):
    trac_model: List[str] = [] 
    status: List[str] = [] 
    dealer: str = ''
    date_assemle: Optional[date] = None


class TractorInfoRequest(BaseModel):
    trac_model: List[str] = []
    status: List[str] = []
    dealer: str


class TractorSearchResponse(BaseModel):
    vin: str
    model: str
    consumer: str
    assembly_date: Optional[datetime] = None
    region: str
    oh_hour: Optional[str] = None              
    last_activity: Optional[datetime] = None
    sw_name: Optional[str] = None               
    componentParts_id: Optional[int] = None   
    component_id: Optional[int] = None         
    comp_model: Optional[str] = None   
    current_sw_version: Optional[int] = None
    recommend_sw_version: Optional[str] = None
    component_type: Optional[str] = None

    class Config:
        orm_mode = True 

class ComponentSearchResponseItem(BaseModel):
    download_link: Optional[str] = None
    type_component: str
    release_date: Optional[datetime] = None
    inner_version: Optional[str] = None
    producer_version: Optional[str] = None
    is_maj: Optional[bool] = None       
    model_component: str
    id_Firmwares: Optional[int] = None  

    class Config:
        orm_mode = True  

class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=5, max_length=50)
    role: str

    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
        if v not in {'moderator', 'dealer', 'engineer'}:
            raise ValueError("Role must be one of: 'moderator', 'user', 'engineer'")
        return v

    @field_validator('password', mode='before')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password too long (max 72 bytes in UTF-8)")
        return v

# =============== Базовые модели (ORM-режим) ===============

class SoftwareBase(BaseModel):
    name: str
    inner_name: Optional[str] = None
    release_date: Optional[datetime] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True

class SoftwareCreate(SoftwareBase):
    """Данные для создания ПО без файла (файл обрабатывается отдельно)"""
    pass

class SoftwareResponse(SoftwareBase):
    id: int
    download_url: str  

# =============== Схемы для загрузки (с файлом) ===============

class AssignSoftwareRequest(BaseModel):
    name: str
    is_major: bool
    inner_name: Optional[str] = None
    release_date: Optional[date] = None
    description: Optional[str] = None
    not_recom: Optional[str] = None
    component_ids: List[int] = Field(..., min_items=1) 
    
class SoftwareMetadata(BaseModel):
    """Метаданные ПО для скачивания"""
    id: int
    name: str
    inner_name: Optional[str] = None
    filename_original: str  # оригинальное имя файла (например, "engine_v2.bin")
    filename_for_download: str  # имя при скачивании (например, "Engine_v2.1.bin")

    class Config:
        orm_mode = True

class SoftwareFileLocation(BaseModel):
    """Путь к файлу на сервере"""
    full_path: str
    size_bytes: int
    exists: bool
    