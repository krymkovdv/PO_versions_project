from pydantic import BaseModel, field_validator, Field
from datetime import datetime, date
from typing import Optional, List
import re
from sqlalchemy import or_

class UserSchema(BaseModel):
    id: int
    username: str
    password_hash: str
    role: str


def wildcard_to_psql_regex(pattern: str) -> str:
    if not pattern:
        return ".*"
    escaped = re.escape(pattern)
    # Заменяем wildcards
    regex = (
        escaped
        .replace(r'\*', '.*')
        .replace(r'\?', '.')
        .replace(r'\[', '[')
        .replace(r'\]', ']')
    )
    # Обрабатываем [!...] → [^...]
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
    model: int
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
    not_recom_sw: str
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
    is_major: bool = False
    is_minor: bool = False

class TractorInfoRequest(BaseModel):
    trac_model: List[str] = []
    status: List[str] = []
    dealer: str

class SearchFilterTractors(BaseModel):
    query: Optional[str] = None

class TractorSearchResponse(BaseModel):
    vin: str
    model: str
    consumer: str
    assembly_date: Optional[str] = None
    region: str
    oh_hour: str
    last_activity: Optional[str] = None
    sw_name: str
    componentParts_id: int
    component_id: int
    comp_model: str
    recommend_sw_version: str
    component_type: str  

class ComponentSearchResponseItem(BaseModel):
    download_link: str
    type_component: str
    release_date: Optional[str] = None
    inner_version: str
    producer_version: str
    is_maj: bool
    model_component: str
    id_Firmwares: int

class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=5, max_length=50)
    role: str

    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
        if v not in {'moderator', 'dealer', 'engineer'}:
            raise ValueError("Role must be one of: 'admin', 'user', 'engineer'")
        return v

    @field_validator('password', mode='before')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password too long (max 72 bytes in UTF-8)")
        return v