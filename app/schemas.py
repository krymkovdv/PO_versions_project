from pydantic import BaseModel, field_validator, Field
from datetime import datetime, date
from typing import Optional, List
import re
from sqlalchemy import or_



#Схема для авторизации
class UserSchema(BaseModel):
    id: int
    username: str
    password_hash: str
    role: str

#Схема для regex-поиска
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

#Схемы для базовых CRUD
class TractorsSchema(BaseModel):
    model: str
    vin: str
    oh_hour: int
    last_activity: Optional[datetime] = None
    assembly_date: Optional[datetime] = None
    region: str
    consumer: str
    serv_center: str
    id: Optional[int] = None

class ComponentSchema(BaseModel):
    type: str
    model: str
    number_of_parts: int
    producer_comp: str
    id: Optional[int] = None

class TelemetryComponentSchema(BaseModel):
    tractor: int
    component: int
    time_rec: Optional[datetime] = None
    comp_ser_num: Optional[str] = None
    mounting_date: date
    current_sw_version: int
    recommend_sw_version: int
    id: Optional[int] = None

class SoftwareSchema(BaseModel):
    path: str
    name: str
    inner_name: Optional[str] = None
    release_date: Optional[datetime] = None
    description: Optional[str] = None
    id: Optional[int] = None

class ComponentPartSchema(BaseModel):
    component: int
    part_type: str
    id: Optional[int] = None

class SoftwareComponentsSchema(BaseModel):
    component_part_id: int
    software_id: int
    is_major: bool
    status: str
    date_change_major: Optional[date] = None 
    not_recom: Optional[str] = None
    date_change_record: Optional[datetime] = None  
    previous_sw_version: Optional[int] = None 
    id: Optional[int] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in {'s', 't', 'b', 'o'}:
            raise ValueError("Status must be one of: 's', 't', 'b', 'o'")
        return v

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

#для ПОИСКА И ФИЛЬТРОВ
class ComponentInfoRequest(BaseModel):
    trac_model: List[str] = []
    type_comp: List[str] = []
    model_comp: List[str] = []

class TractorFilter(BaseModel):
    trac_model: List[str] = []
    status: List[str] = []
    dealer: str = ''
    date_assemle: Optional[str] = None
    is_major: Optional[bool] = None
    date_assemle: Optional[date] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    query: Optional[str] = None
    
    @field_validator('date_start', 'date_end')
    @classmethod
    def validate_date_logic(cls, v, info):
        field_name = info.field_name
        values = info.data
        if 'date_assemle' in values and values['date_assemle'] is not None:
            if field_name in ['date_start', 'date_end']:
                return None
        
        return v
    @field_validator('date_end')
    @classmethod
    def validate_date_range(cls, v, info):
        values = info.data
        date_start = values.get('date_start')
        if date_start and v and date_start > v:
            raise ValueError('date_end не может быть раньше date_start')
        return v

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
    description: Optional[str] = None
    componentParts_id: Optional[int] = None
    component_id: Optional[int] = None
    comp_model: Optional[str] = None
    current_sw_version: Optional[int] = None
    recommend_sw_version: Optional[str] = None
    component_type: Optional[str] = None

    class Config:
        from_attributes = True 

class ComponentSearchResponseItem(BaseModel):
    download_link: Optional[str] = None
    type_component: str
    release_date: Optional[datetime] = None
    inner_version: Optional[str] = None
    producer_version: Optional[str] = None
    is_maj: Optional[bool] = None
    model_component: str
    id_Firmwares: Optional[int] = None

    @field_validator('type_component', mode='before')
    @classmethod
    def normalize_component_types(cls, v):
        if v is None:
            return "unknown"
        if isinstance(v, str):
            return v.lower().strip()
        return str(v).lower().strip()

    class Config:
        from_attributes = True

class SoftwareBase(BaseModel):
    name: str
    inner_name: Optional[str] = None
    release_date: Optional[datetime] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class SoftwareCreate(SoftwareBase):
    pass

class SoftwareResponse(SoftwareBase):
    id: int
    download_url: str

class AssignSoftwareRequest(BaseModel):
    is_major: bool
    release_date: Optional[date] = None
    description: Optional[str] = None
    component_models: List[str] = Field(..., min_items=1)
    part_type: List[str] = Field(..., min_items=1)
    previous_sw_version: Optional[int] = None

class SoftwareMetadata(BaseModel):
    id: int
    name: str
    inner_name: Optional[str] = None
    filename_original: str
    filename_for_download: str

    class Config:
        from_attributes = True

class SoftwareFileLocation(BaseModel):
    full_path: str
    size_bytes: int
    exists: bool

class RequestModel(BaseModel):
    trac_model: List[str] = []

class TractorSearchResponse2(BaseModel):
    vin: str
    model: str
    consumer: str
    assembly_date: Optional[datetime] = None
    region: str
    oh_hour: Optional[str] = None
    last_activity: Optional[datetime] = None
    sw_name: Optional[str] = None
    description: Optional[str] = None
    componentParts_id: Optional[int] = None
    component_id: Optional[int] = None
    comp_model: Optional[str] = None
    current_sw_version: Optional[int] = None
    recommend_sw_version: Optional[str] = None
    component_type: Optional[str] = None

    class Config:
        from_attributes = True

class TractorComponentRequest(BaseModel):
    vins: List[str]

class TractorComponentResponse(BaseModel):
    vin: str
    component_type: str
    comp_model: str

class TractorUpdate(BaseModel):
    model: Optional[str] = None
    oh_hour: Optional[int] = None
    last_activity: Optional[datetime] = None
    assembly_date: Optional[datetime] = None
    region: Optional[str] = None
    consumer: Optional[str] = None
    serv_center: Optional[str] = None

class ComponentUpdate(BaseModel):
    type: Optional[str] = None
    model: Optional[str] = None
    number_of_parts: Optional[int] = None
    producer_comp: Optional[str] = None

class SoftwareUpdate(BaseModel):
    name: Optional[str] = None
    inner_name: Optional[str] = None
    release_date: Optional[datetime] = None
    description: Optional[str] = None
    is_major: Optional[bool] = None

class ComponentPartUpdate(BaseModel):
    component: Optional[int] = None
    part_type: Optional[str] = None

class SoftwareComponentLinkUpdate(BaseModel):
    component_part_id: Optional[int] = None
    software_id: Optional[int] = None
    is_major: Optional[bool] = None
    status: Optional[str] = None
    date_change_major: Optional[date] = None
    not_recom: Optional[str] = None
    date_change_record: Optional[datetime] = None
    previous_sw_version: Optional[int] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in {'s', 't', 'b', 'o'}:
            raise ValueError("Status must be one of: 's', 't', 'b', 'o'")
        return v