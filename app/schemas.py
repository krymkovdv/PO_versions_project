from pydantic import BaseModel, field_validator, Field, ConfigDict, computed_field
from datetime import datetime, date
from typing import Optional, List
import re
from pathlib import Path

# ============================================
# Вспомогательные функции для regex-поиска
# ============================================
def wildcard_to_psql_regex(pattern: str) -> str:
    """Преобразует wildcard-паттерн в PostgreSQL regex"""
    if not pattern:
        return ".*"
    
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
            processed.append('-')
        elif char == '\\' and i + 1 < len(pattern):
            next_char = pattern[i + 1]
            if next_char in '*?[]!~\\':
                processed.append(next_char)
                i += 1
            else:
                processed.append('\\')
                processed.append(next_char)
                i += 1
        else:
            processed.append(char)
        i += 1
    
    pattern_clean = ''.join(processed)
    escaped = re.escape(pattern_clean)
    regex = (
        escaped
        .replace(r'\*', '.*')
        .replace(r'\?', '.')
        .replace(r'\[', '[')
        .replace(r'\]', ']')
    )
    regex = re.sub(r'\[\\!', '[^', regex)
    return regex

def is_safe_regex(regex: str) -> bool:
    """Проверка безопасности regex"""
    if len(regex) > 200:
        return False
    if re.search(r'\([^)]*\)[+*{]|[{]\d+,\d+[}]|\.\*\.\*', regex):
        return False
    return True

# ============================================
# Пользователи
# ============================================
class UserSchema(BaseModel):
    id: int
    username: str
    role: str
    
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=5, max_length=50)
    role: str

    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
        ALLOWED_ROLES = {'moderator', 'dealer', 'engineer'}
        if v not in ALLOWED_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(ALLOWED_ROLES)}")
        return v

    @field_validator('password', mode='before')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password too long (max 72 bytes in UTF-8)")
        return v

# ============================================
# Тракторы
# ============================================
class TractorsSchema(BaseModel):
    id: Optional[int] = None
    model: str
    vin: str
    oh_hour: int = 0
    last_activity: Optional[datetime] = None
    assembly_date: Optional[datetime] = None
    region: str
    consumer: str
    dealer: str
    
    model_config = ConfigDict(from_attributes=True)

class TractorUpdate(BaseModel):
    model: Optional[str] = None
    oh_hour: Optional[int] = None
    last_activity: Optional[datetime] = None
    assembly_date: Optional[datetime] = None
    region: Optional[str] = None
    consumer: Optional[str] = None
    dealer: Optional[str] = None

# ============================================
# Компоненты
# ============================================
class ComponentSchema(BaseModel):
    id: Optional[int] = None
    type: str
    name: str 
    producer: str 
    
    model_config = ConfigDict(from_attributes=True)

    @field_validator('type', mode='before')
    @classmethod
    def validate_type(cls, v):
        ALLOWED_TYPES = {'DVS', 'KPP', 'RK', 'HR', 'BK'}
        if v not in ALLOWED_TYPES:
            raise ValueError(f"Component type must be one of: {', '.join(ALLOWED_TYPES)}")
        return v.upper()

class ComponentUpdate(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
    producer: Optional[str] = None

# ============================================
# Программное обеспечение
# ============================================
class SoftwareSchema(BaseModel):
    id: Optional[int] = None
    path: str
    release_date: Optional[datetime] = None
    end_actuality: Optional[datetime] = None 
    description: Optional[str] = None
    producer: str
    is_actual: bool = True
    is_archive: bool = False 
    is_critical: bool = False 
    status: Optional[str] = None  
    tractor_model: List[str] = Field(default_factory=list) 
    previous_sw_version: Optional[int] = None
    path_instruction: Optional[str]  
    
    model_config = ConfigDict(from_attributes=True)
    @computed_field
    @property
    def name(self) -> str:
        """Извлекает имя файла из поля path (НЕ из БД!)"""
        if not self.path:
            return ""
        return Path(self.path).name
    
    @computed_field
    @property
    def filename(self) -> str:
        """Псевдоним для name (для совместимости)"""
        return self.name
    
class SoftwareCreate(BaseModel):
    path: str
    release_date: Optional[datetime] = None
    end_actuality: Optional[datetime] = None
    description: Optional[str] = None
    producer: str
    is_actual: bool = True
    is_archive: bool = False
    is_critical: bool = False 
    status: Optional[str] = None
    tractor_model: List[str] = Field(default_factory=list)
    previous_sw_version: Optional[int] = None
    path_instruction: str
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in {'serial', 'experienced', 'in operation'}:
            raise ValueError("Status must be one of: 'serial', 'experienced', 'in operation'")
        return v
    
class SoftwareUpdate(BaseModel):
    path: Optional[str] = None
    release_date: Optional[datetime] = None
    end_actuality: Optional[datetime] = None
    description: Optional[str] = None
    producer: Optional[str] = None
    is_actual: Optional[bool] = None
    is_archive: Optional[bool] = None
    is_critical: bool = False 
    status: Optional[str] = None
    tractor_model: List[str] = Field(default_factory=list)
    previous_sw_version: Optional[int] = None
    path_instruction: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in {'serial', 'experienced', 'in operation'}:
            raise ValueError("Status must be one of: 'serial', 'experienced', 'in operation'")
        return v
    
class SoftwareResponse(BaseModel):
    id: int
    release_date: Optional[datetime] = None
    description: Optional[str] = None
    producer: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================
# Связь ПО ↔ Компонент
# ============================================
class SoftwareComponentsSchema(BaseModel):
    id: Optional[int] = None
    component_id: int 
    software_id: int
    
    model_config = ConfigDict(from_attributes=True)

class SoftwareComponentLinkUpdate(BaseModel):
    component_id: Optional[int] = None
    software_id: Optional[int] = None

# ============================================
# Связь Трактор ↔ ПО ↔ Компонент
# ============================================
class TractorSoftwareComponentLinkSchema(BaseModel):
    id: Optional[int] = None
    is_recom: bool = True
    tractor_id: int
    soft_comp_link_id: int
    
    model_config = ConfigDict(from_attributes=True)

class TractorSoftwareComponentLinkCreate(BaseModel):
    """Схема для создания связи"""
    is_recom: bool = True
    tractor_id: int
    soft_comp_link_id: int

class TractorSoftwareComponentLinkUpdate(BaseModel):
    """Схема для обновления связи"""
    is_recom: Optional[bool] = None

class TractorSoftwareResponse(BaseModel):
    """Расширенный ответ с информацией о тракторе, ПО и компоненте"""
    id: int
    tractor_vin: str
    tractor_model: str
    software_id: int
    software_name: Optional[str] = None
    software_path: Optional[str] = None
    component_id: int
    component_type: str
    component_name: str
    is_recom: bool
    mounted_date: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# ============================================
# Поиск и фильтры
# ============================================
class ComponentInfoRequest(BaseModel):
    search: str = ''
    trac_model: List[str] = []
    type_comp: List[str] = []
    name_comp: List[str] = []
    producers: List[str] = []
    status: List[str] = []

class TractorFilter(BaseModel):
    component_type: Optional[str] = None  # 'DVS', 'KPP', 'RK', 'HR', 'BK'
    
    software_filter: Optional[str] = Field(None, pattern="^(actual|critical|old)$")
    is_actual: Optional[bool] = None
    trac_model: List[str] = []
    dealer: str = ''
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

class RequestModel(BaseModel):
    trac_model: List[str] = []
    type_comp: List[str] = []
    producers: List[str] = []
    status: List[str] = []

class ComponentFilterRequest(BaseModel):
    """Запрос для фильтрации производителей/моделей компонентов"""
    trac_model: List[str] = Field(default_factory=list)  # Модели тракторов
    type_comp: List[str] = Field(default_factory=list)   # Типы компонентов
    component_models: List[str] = Field(default_factory=list)  # Модели компонентов
    software_status: List[str] = Field(default_factory=list)   # Статусы ПО
    
    class Config:
        from_attributes = True


class TractorFilterRequest(BaseModel):
    """Запрос для фильтрации моделей тракторов"""
    component_types: List[str] = Field(default_factory=list)     # Типы компонентов
    component_models: List[str] = Field(default_factory=list)    # Модели компонентов
    component_producers: List[str] = Field(default_factory=list) # Производители компонентов
    software_status: List[str] = Field(default_factory=list)     # Статусы ПО
    
    class Config:
        from_attributes = True
        
class TractorComponentRequest(BaseModel):
    vins: List[str]

class TractorComponentResponse(BaseModel):
    vin: str
    component_type: str
    comp_model: str
    is_actual: bool
    is_critical: bool

    
# ============================================
# Ответы для поиска
# ============================================

class  ComponentSearchResponseItem(BaseModel):
    download_link: Optional[str] = None
    download_link_instruction: Optional[str] = None
    type_component: str
    release_date: Optional[datetime] = None
    is_actual: Optional[bool] = None
    is_archive: Optional[bool] = None
    is_critical: Optional[bool] = None 
    name_component: str
    id_Firmwares: Optional[int] = None
    id_Component: Optional[int] = None
    status: Optional[str] = None
    tractor_model: Optional[List[str]]

    @field_validator('type_component', mode='before')
    @classmethod
    def normalize_component_types(cls, v):
        if v is None:
            return "unknown"
        if isinstance(v, str):
            return v.lower().strip()
        return str(v).lower().strip()
    
    model_config = ConfigDict(from_attributes=True)

class SoftwareComponentInfoResponse(BaseModel):
    """Полная информация о ПО и компоненте по ID"""
    
    # Информация о ПО
    id_firmwares: int
    software_path: str
    software_release_date: Optional[datetime] = None
    software_description: Optional[str] = None
    software_producer: str
    software_is_actual: bool
    software_is_archive: bool
    software_is_critical:bool
    software_status: Optional[str] = None
    software_tractor_models: List[str] = Field(default_factory=list)
    software_previous_sw_version: Optional[int] = None
    software_path_instruction: Optional[str]
    
    # Информация о компоненте
    id_component: int
    component_type: str
    component_name: str
    component_producer: str
    
    # Информация о связи
    link_id: int
    is_recom: bool
    
    model_config = ConfigDict(from_attributes=True)
    
    @computed_field
    @property
    def name(self) -> str:
        """Извлекает имя файла из software_path (НЕ из БД!)"""
        if not self.software_path:
            return ""
        return Path(self.software_path).name
    
    @computed_field
    @property
    def filename(self) -> str:
        """Псевдоним для name (для совместимости)"""
        return self.name

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


    class Config:
        from_attributes = True 

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
# ============================================
# Загрузка ПО
# ============================================
class AssignSoftwareRequest(BaseModel):
      # Поля ПО
    software_release_date: Optional[datetime] = None
    software_description: Optional[str] = None
    software_is_actual: bool = True
    software_is_archive: bool = False
    software_is_critical: bool = False
    software_status: str
    software_tractor_models: List[str] = Field(..., min_length=1)  # Массив моделей тракторов
    software_producer: str = Field(..., min_length=1)
    software_previous_version: Optional[int] = None
    
    # Информация о компоненте
    component_models: List[str] = Field(..., min_length=1)
    component_types: List[str] = Field(..., min_length=1)
    component_producers: List[str] = Field(..., min_length=1)

class SoftwareMetadata(BaseModel):
    id: int
    name: str
    inner_name: Optional[str] = None
    filename_original: str
    filename_for_download: str
    has_instruction: bool = False  # ← Добавлено
    instruction_filename: Optional[str] = None  # ← Добавлено
    release_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SoftwareFileLocation(BaseModel):
    full_path: str
    size_bytes: int
    exists: bool


class SoftwareInstructionLocation(BaseModel):
    full_path: str
    size_bytes: int
    exists: bool
    filename: str


class UploadInstructionResponse(BaseModel):
    id: int
    instruction_path: str
    filename: str
    size_bytes: int
    message: str
    
    class Config:
        from_attributes = True


class ArchiveChangeRequest(BaseModel):
    is_archive: bool


# Поддержка

class ReplyRequest(BaseModel):
    message_id: int
    content: str = Field(..., min_length=1, max_length=1000)

class ConversationMessage(BaseModel):
    id: int
    content: str
    created_at: datetime
    sender: str  # "user" или "moderator"
    sender_name: str
    is_read: Optional[bool] = None
    read_by_moderators: Optional[List[dict]] = None
    is_reply_to: Optional[int] = None

class ConversationResponse(BaseModel):
    user: dict
    moderator: dict
    messages: List[ConversationMessage]

class UserForModerator(BaseModel):
    user_id: int
    username: str
    role: str
    last_message: datetime
    unread_count: int

class UsersForModeratorResponse(BaseModel):
    users: List[UserForModerator]