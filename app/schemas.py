from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class TractorsSchema(BaseModel):
    terminal_id: int
    model: str
    region: str
    owner_name: str
    assembly_date: datetime

class TractorsComponentSchema(BaseModel):
    row_id: int
    time_comp: datetime
    tractor: int
    comp_id: int

class TrueComponentSchema(BaseModel):
    id: int
    Type_component: str
    Model_component: str
    Year_component: datetime

class FirmwareSchema(BaseModel):
    id_Firmwares: int
    inner_version: str
    producer_version: str
    download_link: str
    release_date: Optional[datetime] = None
    maj_to: str
    min_to: str
    maj_for_c_model: str
    min_for_c_model: str
    time_Maj: Optional[datetime] = None
    time_Min: Optional[datetime] = None

class TelemetryComponentSchema(BaseModel):
    id_telemetry: int
    true_comp: int
    current_version: int
    is_maj: bool

# Для фильтра СХЕМА
