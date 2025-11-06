from pydantic import BaseModel, field_validator
from datetime import datetime, date
from typing import Optional, List


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
class FirmwareInfo(BaseModel):
    inner_version: str
    producer_version: str
    download_link: str
    release_date: Optional[str] = None
    maj_to: Optional[str] = None
    min_to: Optional[str] = None

class ComponentInfo(BaseModel):
    type_component: str
    model_component: str
    year_component: Optional[str]  # или date, но вы используете str в ответе
    current_version_id: int  # ID софта из Software
    is_maj: bool
    firmware: FirmwareInfo

class TractorSoftwareResponse(BaseModel):
    vin: str
    model: str
    assembly_date: Optional[str]
    components: List[ComponentInfo]

    class Config:
        from_attributes = True  # позволяет использовать ORM-объекты напрямую

class TractorFilter(BaseModel):
    models: List[str] = []
    release_date_from: Optional[str] = None  # "YYYY-MM-DD"
    release_date_to: Optional[str] = None
    requires_maj: bool = False  # True → только is_major=True
    requires_min: bool = False  # True → только is_major=False
