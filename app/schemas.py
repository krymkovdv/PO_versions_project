from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class TractorsSchema(BaseModel):
    terminal_id: int
    model: str
    region: str
    owner_name: str
    assembly_date: datetime

    class Config:
        from_attributes = True  # ← позволяет читать из ORM-объекта


# Для фильтрации
class TractorFilter(BaseModel):
    models: List[str] = []           # ['K-742MCT', 'K-735']
    release_date_from: Optional[str] = None  # "2025-01-01"
    release_date_to: Optional[str] = None
    component_types: Optional[List[str]] = None   # ['Серийное', 'Опытное']
    requires_maj: bool = False
    requires_min: bool = False
    search_query: Optional[str] = None  # для умного поиска

# Для ответа — строка таблицы
class FirmwareInfo(BaseModel):
    inner_version: str
    producer_version: str
    download_link: str
    release_date: Optional[str]
    maj_to: str
    min_to: str

class ComponentInfo(BaseModel):
    type_component: str
    model_component: str
    year_component: str
    current_version: int
    is_maj: bool
    firmware: FirmwareInfo

class TractorSoftwareResponse(BaseModel):
    vin: str
    model: str
    assembly_date: str
    region: str
    motocycles: int
    last_activity: str
    dvс: str  # Номер ПО / необходимость обновления
    kpp: str
    pk: str
    bk: str
    components: List[ComponentInfo]

    class Config:
        from_attributes = True