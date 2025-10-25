from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List


class TractorsSchema(BaseModel):
    id: int
    model: str
    vin: str
    oh_hour: int
    last_activity: Optional[datetime] = None
    assembly_date: Optional[datetime] = None

class ComponentSchema(BaseModel):
    id: int
    type: str
    model: int
    date_create: date

class TelemetryComponentSchema(BaseModel):
    id: int
    software: int
    tractor: int
    component: int
    time_record: datetime
    serial_number: str

class SoftwareSchema(BaseModel):
    id: int
    path: str
    name: str
    inner_name: str
    prev_version = Optional[int]
    next_version = Optional[int]
    release_date: datetime

class ComponentSoftwareSchema(BaseModel):
    id: int
    software: int
    tractor: int
    component: int
    time_record: datetime
    serial_number: str

class relation(BaseModel):
    
    id = int
    software1 = int
    software2 = int

# Для фильтра СХЕМА
class TractorFilter(BaseModel):
    models: List[str] = []  # например: ["K-742MCT", "K-735"]
    release_date_from: Optional[str] = None  # "2025-01-01"
    release_date_to: Optional[str] = None    # "2025-12-31"
    requires_maj: bool = False
    requires_min: bool = False

class FirmwareInfo(BaseModel):
    inner_version: str
    producer_version: str
    download_link: str
    release_date: Optional[str] = None
    maj_to: str
    min_to: str
class ComponentInfo(BaseModel):
    type_component: str
    model_component: str
    year_component: str  # или Optional[str]
    current_version: int
    is_maj: bool
    firmware: FirmwareInfo

class TractorSoftwareResponse(BaseModel):
    vin: str
    model: str
    assembly_date: str
    region: str

    dvс: str
    kpp: str
    pk: str
    bk: str
    components: List[ComponentInfo]

    class Config:
        from_attributes = True