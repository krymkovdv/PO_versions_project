from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List

class TractorsSchema(BaseModel):
    terminal_id: int
    model: str
    region: str
    owner_name: str
    assembly_date: datetime

    class Config:
        from_attributes = True

class TractorsComponentSchema(BaseModel):
    row_id: int
    time_comp: datetime
    tractor: int
    comp_id: int

    class Config:
        from_attributes = True

class TrueComponentSchema(BaseModel):
    id: int
    Type_component: str
    Model_component: str
    Year_component: date

    class Config:
        from_attributes = True

class FirmwareSchema(BaseModel):
    id_Firmwares: int
    inner_version: str
    producer_version: str
    download_link: str
    release_date: Optional[datetime] = None
    maj_to: Optional[str] = None
    min_to: Optional[str] = None
    maj_for_c_model: Optional[str] = None
    min_for_c_model: Optional[str] = None
    time_Maj: Optional[datetime] = None
    time_Min: Optional[datetime] = None

    class Config:
        from_attributes = True

class TelemetryComponentSchema(BaseModel):
    id_telemetry: int
    true_comp: int
    current_version: int
    is_maj: bool

    class Config:
        from_attributes = True

# Для фильтра
class TractorFilter(BaseModel):
    models: List[str] = []
    release_date_from: Optional[str] = None
    release_date_to: Optional[str] = None
    requires_maj: bool = False
    requires_min: bool = False

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
    year_component: str
    current_version: int
    is_maj: bool
    firmware: FirmwareInfo

class TractorSoftwareResponse(BaseModel):
    terminal_id: int  # Изменил vin на terminal_id
    model: str
    assembly_date: str
    region: str
    owner_name: str  # Добавил
    components: List[ComponentInfo]  # Убрал отдельные поля dvс, kpp и т.д.

    class Config:
        from_attributes = True



# New

class ComponentInfoRequest(BaseModel):
    trac_model: List[str] = []
    type_comp: List[str] = []
    model_comp: str = ''