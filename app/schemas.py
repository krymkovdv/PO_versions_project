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
class ComponentInfoRequest(BaseModel):
    trac_model: List[str] = []
    type_comp: List[str] = []
    model_comp: str = ''

class TractorInfoRequest(BaseModel):
    trac_model: List[str] = []
    status: List[str] = []
    dealer: str

class SearchFilterTractors(BaseModel):
    vin: str = ''
    model: str = ''
    date_release: str = ''
    region: str = ''
    oh_hour: str = ''
    last_activity: str = ''

    vin_regex: bool = False 
    model_regex: bool = False
    region_regex: bool = False

class TractorSearchResponse(BaseModel):
    vin: str
    model: str
    consumer: str
    assembly_date: Optional[str] = None
    region: str
    oh_hour: str
    last_activity: Optional[str] = None
    sw_name: str
    recommend_sw_version: str
    type: str  

class ComponentSearchResponse(BaseModel):
    trac_model: str 
    type_comp: str
    model_comp: str

    trac_regex: bool = False 
    type_regex: bool = False
    model_regex: bool = False

class ComponentSearchResponseItem(BaseModel):
    download_link: str
    type_component: str
    release_date: Optional[str] = None
    inner_version: str
    producer_version: str
    is_maj: bool
    model_component: str
    id_Firmwares: int