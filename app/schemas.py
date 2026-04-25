from pydantic import BaseModel, field_validator, Field, ConfigDict, computed_field
from datetime import datetime, date
from typing import Optional, List
import re
from pathlib import Path

# ============================================
# Вспомогательные функции для regex-поиска
# ============================================
def wildcard_to_psql_regex(pattern: str) -> str:
    """
    Преобразует wildcard-паттерн в PostgreSQL regex
    
    Args:
        pattern: шаблон с символами подстановки (*, ?, [])
        
    Returns:
        регулярное выражение в формате PostgreSQL
    """
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
    """
    Проверяет безопасность регулярного выражения (защита от ReDoS-атак)
    
    Args:
        regex: регулярное выражение для проверки
        
    Returns:
        True, если регулярное выражение безопасно
    """
    if len(regex) > 200:
        return False
    if re.search(r'\([^)]*\)[+*{]|[{]\d+,\d+[}]|\.\*\.\*', regex):
        return False
    return True

# ============================================
# Пользователи
# ============================================
class UserSchema(BaseModel):
    """Схема для представления информации о пользователе"""
    id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    """Схема для создания нового пользователя"""
    username: str
    password: str = Field(..., min_length=5, max_length=50)  # Пароль с ограничениями по длине
    role: str

    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
        """Валидатор роли пользователя"""
        ALLOWED_ROLES = {'moderator', 'dealer', 'engineer'}
        if v not in ALLOWED_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(ALLOWED_ROLES)}")
        return v

    @field_validator('password', mode='before')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """Валидатор длины пароля (ограничение в 72 байта для bcrypt)"""
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password too long (max 72 bytes in UTF-8)")
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = None
    
    class Config:
        from_attributes = True
    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
        """Валидатор роли пользователя"""
        if v is None:
            return v
        ALLOWED_ROLES = {'moderator', 'dealer', 'engineer'}
        if v not in ALLOWED_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(ALLOWED_ROLES)}")
        return v
        
# ============================================
# Тракторы
# ============================================
class TractorsSchema(BaseModel):
    """Схема для представления информации о тракторе"""
    id: Optional[int] = None  # ID может быть присвоен автоматически
    model: str  # Модель трактора
    vin: str  # VIN номер
    oh_hour: int = 0  # Моточасы (по умолчанию 0)
    last_activity: Optional[datetime] = None  # Время последней активности
    assembly_date: Optional[datetime] = None  # Дата сборки
    region: str  # Регион эксплуатации
    consumer: str  # Потребитель (владелец)
    dealer: str  # Дилер (обслуживающая организация)
    
    model_config = ConfigDict(from_attributes=True)

class TractorUpdate(BaseModel):
    """Схема для обновления информации о тракторе (все поля опциональны)"""
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
    """Схема для представления информации о компоненте трактора"""
    id: Optional[int] = None  # ID может быть присвоен автоматически
    type: str  # Тип компонента (DVS, KPP, RK, HR, BK, AUTOPILOT)
    name: str  # Название компонента
    producer: str  # Производитель
    
    model_config = ConfigDict(from_attributes=True)

    @field_validator('type', mode='before')
    @classmethod
    def validate_type(cls, v):
        """Валидатор типа компонента"""
        ALLOWED_TYPES = {'DVS', 'KPP', 'RK', 'HR', 'BK','AUTOPILOT'}
        if v not in ALLOWED_TYPES:
            raise ValueError(f"Component type must be one of: {', '.join(ALLOWED_TYPES)}")
        return v.upper()

class ComponentUpdate(BaseModel):
    """Схема для обновления информации о компоненте (все поля опциональны)"""
    type: Optional[str] = None
    name: Optional[str] = None
    producer: Optional[str] = None

# ============================================
# Программное обеспечение
# ============================================
class SoftwareSchema(BaseModel):
    """Схема для представления информации о программном обеспечении"""
    id: Optional[int] = None  # ID может быть присвоен автоматически
    path: Optional[str] = None  # Путь к файлу ПО
    release_date: Optional[datetime] = None  # Дата выпуска
    end_actuality: Optional[datetime] = None  # Дата окончания актуальности
    description: Optional[str] = None  # Описание ПО
    producer: Optional[str] = None  # Производитель
    is_actual: Optional[bool] = None  # Является ли ПО актуальным
    is_archive: Optional[bool] = None  # Находится ли ПО в архиве
    is_critical: Optional[bool] = None  # Является ли обновление критическим
    status: Optional[str] = None  # Статус ПО (serial, in operation, experienced)
    tractor_model: List[str] = Field(default_factory=list)  # Модели тракторов, для которых подходит ПО
    previous_sw_version: Optional[int] = None  # ID предыдущей версии ПО
    path_instruction: Optional[str] = None  # Путь к инструкции по установке
    
    model_config = ConfigDict(from_attributes=True)
    
    @computed_field
    @property
    def name(self) -> str:
        """Вычисляемое поле: извлекает имя файла из поля path"""
        if not self.path:
            return ""
        return Path(self.path).name
    
    @computed_field
    @property
    def filename(self) -> str:
        """Псевдоним для name (для совместимости)"""
        return self.name

class SoftwareCreate(BaseModel):
    """Схема для создания нового программного обеспечения"""
    path: str  # Путь к файлу ПО
    release_date: Optional[datetime] = None
    end_actuality: Optional[datetime] = None
    description: Optional[str] = None
    producer: str  # Производитель обязательно
    is_actual: bool = True  # По умолчанию ПО считается актуальным
    is_archive: bool = False  # По умолчанию ПО не в архиве
    is_critical: bool = False  # По умолчанию обновление не критическое
    status: Optional[str] = None  # Статус ПО (serial, in operation, experienced)
    tractor_model: List[str] = Field(default_factory=list)  # Модели тракторов
    previous_sw_version: Optional[int] = None  # ID предыдущей версии
    path_instruction: str  # Путь к инструкции (обязательный параметр)
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Валидатор статуса ПО"""
        if v not in {'serial', 'experienced', 'in operation'}:
            raise ValueError("Status must be one of: 'serial', 'experienced', 'in operation'")
        return v

class SoftwareUpdate(BaseModel):
    """Схема для обновления информации о программном обеспечении"""
    path: Optional[str] = None
    release_date: Optional[datetime] = None
    end_actuality: Optional[datetime] = None
    description: Optional[str] = None
    producer: Optional[str] = None
    is_actual: Optional[bool] = None
    is_archive: Optional[bool] = None
    is_critical: Optional[bool] = None
    status: Optional[str] = None
    tractor_model: List[str] = Field(default_factory=list)
    previous_sw_version: Optional[int] = None
    path_instruction: Optional[str] = None
    # component_type:Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Валидатор статуса ПО"""
        if v not in {'serial', 'experienced', 'in operation'}:
            raise ValueError("Status must be one of: 'serial', 'experienced', 'in operation'")
        return v

class SoftwareResponse(BaseModel):
    """Упрощенная схема для ответа с информацией о ПО"""
    id: int  # ID обязательно
    release_date: Optional[datetime] = None
    description: Optional[str] = None
    producer: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================
# Связь ПО ↔ Компонент
# ============================================
class SoftwareComponentsSchema(BaseModel):
    """Схема для связи программного обеспечения и компонента"""
    id: Optional[int] = None
    component_id: int  # ID компонента
    software_id: int  # ID программного обеспечения
    
    model_config = ConfigDict(from_attributes=True)

class SoftwareComponentLinkUpdate(BaseModel):
    """Схема для обновления связи между ПО и компонентом"""
    component_id: Optional[int] = None
    software_id: Optional[int] = None

# ============================================
# Связь Трактор ↔ ПО ↔ Компонент
# ============================================
class TractorSoftwareComponentLinkSchema(BaseModel):
    """Схема для связи трактора с ПО и компонентом"""
    id: Optional[int] = None
    is_recom: bool = True  # Является ли установка рекомендованной
    tractor_id: int  # ID трактора
    soft_comp_link_id: int  # ID связи ПО и компонента
    
    model_config = ConfigDict(from_attributes=True)

class TractorSoftwareComponentLinkCreate(BaseModel):
    """Схема для создания связи трактора с ПО и компонентом"""
    is_recom: bool = True  # По умолчанию установка рекомендована
    tractor_id: int  # ID трактора
    soft_comp_link_id: int  # ID связи ПО и компонента

class TractorSoftwareComponentLinkUpdate(BaseModel):
    """Схема для обновления связи трактора с ПО и компонентом"""
    is_recom: Optional[bool] = None  # Поле опционально

class TractorSoftwareResponse(BaseModel):
    """Расширенный ответ с информацией о тракторе, ПО и компоненте"""
    id: int  # ID связи
    tractor_vin: str  # VIN трактора
    tractor_model: str  # Модель трактора
    software_id: int  # ID программного обеспечения
    software_name: Optional[str] = None  # Имя файла ПО
    software_path: Optional[str] = None  # Путь к файлу ПО
    component_id: int  # ID компонента
    component_type: str  # Тип компонента
    component_name: str  # Имя компонента
    is_recom: Optional[bool] = None  # Является ли установка рекомендованной
    mounted_date: Optional[datetime] = None  # Дата установки
    
    model_config = ConfigDict(from_attributes=True)

# ============================================
# Поиск и фильтры
# ============================================
class ComponentInfoRequest(BaseModel):
    """Запрос для получения информации о компонентах с фильтрами"""
    search: str = ''  # Поисковый запрос
    trac_model: List[str] = []  # Фильтр по моделям тракторов
    type_comp: List[str] = []  # Фильтр по типам компонентов
    name_comp: List[str] = []  # Фильтр по именам компонентов
    producers: List[str] = []  # Фильтр по производителям
    status: List[str] = []  # Фильтр по статусу ПО
    # Для фильтрации по состоянию ПО (когда фронт готов - раскомментировать)
    soft_state: List[str] = []

class TractorFilter(BaseModel):
    """Фильтр для поиска тракторов"""
    component_type: Optional[str] = None  # Тип компонента (DVS, KPP, RK, HR, BK)
    
    software_filter: Optional[str] = Field(None, pattern="^(actual|critical|old)$")  # Фильтр по типу ПО
    is_actual: Optional[bool] = None  # Флаг актуальности ПО
    trac_model: List[str] = []  # Модели тракторов
    dealer: str = ''  # Дилер
    date_assemle: Optional[date] = None  # Дата сборки
    date_start: Optional[date] = None  # Начальная дата
    date_end: Optional[date] = None  # Конечная дата
    query: Optional[str] = None  # Общий поисковый запрос
    
    @field_validator('date_start', 'date_end')
    @classmethod
    def validate_date_logic(cls, v, info):
        """Валидатор логики дат (если задана дата сборки, игнорируем диапазоны)"""
        field_name = info.field_name
        values = info.data
        if 'date_assemle' in values and values['date_assemle'] is not None:
            if field_name in ['date_start', 'date_end']:
                return None
        return v
    
    @field_validator('date_end')
    @classmethod
    def validate_date_range(cls, v, info):
        """Валидатор диапазона дат (конечная дата не должна быть раньше начальной)"""
        values = info.data
        date_start = values.get('date_start')
        if date_start and v and date_start > v:
            raise ValueError('date_end не может быть раньше date_start')
        return v

class TractorInfoRequest(BaseModel):
    """Запрос информации о тракторах с фильтрами"""
    trac_model: List[str] = []  # Модели тракторов
    status: List[str] = []  # Статусы ПО
    dealer: str  # Дилер

class RequestModel(BaseModel):
    """Общий запрос модели для фильтрации"""
    trac_model: List[str] = []  # Модели тракторов
    type_comp: List[str] = []  # Типы компонентов
    producers: List[str] = []  # Производители
    status: List[str] = []  # Статусы ПО

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
    """Запрос компонентов для указанных VIN тракторов"""
    vins: List[str]  # Список VIN номеров

class ComponentInfo(BaseModel):
    """Информация об одном компоненте"""
    component_type: str
    comp_model: str
    is_actual: Optional[bool] = None
    is_critical: Optional[bool] = None
    software_id: Optional[int] = None
    software_name: Optional[str] = None
    software_path: Optional[str] = None

class TractorComponentResponse(BaseModel):
    vin: str
    components: List[ComponentInfo]

# ============================================
# Ответы для поиска
# ============================================

class  ComponentSearchResponseItem(BaseModel):
    """Элемент ответа поиска компонентов"""
    name : str = None  # Имя файла ПО
    download_link: Optional[str] = None  # Ссылка для скачивания ПО
    download_link_instruction: Optional[str] = None  # Ссылка для скачивания инструкции
    type_component: str  # Тип компонента
    release_date: Optional[datetime] = None  # Дата выпуска ПО
    end_actuality: Optional[datetime] = None  # Дата окончания актуальности
    is_actual: Optional[bool] = None  # Актуальность ПО
    is_archive: Optional[bool] = None  # Находится ли в архиве
    is_critical: Optional[bool] = None  # Критичность обновления
    name_component: str  # Имя компонента
    id_Firmwares: Optional[int] = None  # ID прошивки
    id_Component: Optional[int] = None  # ID компонента
    status: Optional[str] = None  # Статус ПО
    tractor_model: Optional[List[str]]  # Модели тракторов
    description: Optional[str] = None  # Описание

    @field_validator('type_component', mode='before')
    @classmethod
    def normalize_component_types(cls, v):
        """Нормализатор типов компонентов"""
        if v is None:
            return "unknown"
        if isinstance(v, str):
            return v.lower().strip()
        return str(v).lower().strip()
    
    model_config = ConfigDict(from_attributes=True)

class SoftwareComponentInfoResponse(BaseModel):
    """Полная информация о ПО и компоненте по ID"""
    
    # Информация о ПО
    id_firmwares: int  # ID прошивки
    software_name: str  # 👈 ДОБАВИТЬ ЭТО ПОЛЕ - название ПО из БД
    software_path: Optional[str] = None  # Путь к файлу ПО
    software_release_date: Optional[datetime] = None  # Дата выпуска ПО
    software_end_actuality: Optional[datetime] = None  # Дата окончания актуальности
    software_description: Optional[str] = None  # Описание ПО
    software_producer: str  # Производитель ПО
    software_is_actual: Optional[bool] = None  # Актуальность ПО
    software_is_archive: Optional[bool] = None  # Находится ли ПО в архиве
    software_is_critical: Optional[bool] = None  # Критичность обновления
    software_status: Optional[str] = None  # Статус ПО
    software_tractor_models: List[str] = Field(default_factory=list)  # Модели тракторов для ПО
    software_previous_sw_version: Optional[int] = None  # ID предыдущей версии ПО
    software_path_instruction: Optional[str] = None  # Путь к инструкции по установке
    
    # Информация о компоненте
    id_component: int  # ID компонента
    component_type: str  # Тип компонента
    component_name: str  # Имя компонента
    component_producer: str  # Производитель компонента
    
    model_config = ConfigDict(from_attributes=True)
    
    # Оставляем computed_field для имени файла (из пути)
    @computed_field
    @property
    def filename(self) -> str:
        """Имя файла из пути"""
        if not self.software_path:
            return ""
        return Path(self.software_path).name
class TractorSearchResponse(BaseModel):
    """Ответ поиска тракторов"""
    vin: str  # VIN трактора
    model: str  # Модель трактора
    consumer: str  # Потребитель
    dealer: str  # Дилер
    assembly_date: Optional[datetime] = None  # Дата сборки
    region: str  # Регион
    oh_hour: Optional[str] = None  # Моточасы
    last_activity: Optional[datetime] = None  # Время последней активности
    sw_name: Optional[str] = None  # Имя текущего ПО
    description: Optional[str] = None  # Описание


    class Config:
        from_attributes = True 

class TractorSearchResponse2(BaseModel):
    """Расширенный ответ поиска тракторов"""
    vin: str  # VIN трактора
    model: str  # Модель трактора
    consumer: str  # Потребитель
    assembly_date: Optional[datetime] = None  # Дата сборки
    region: str  # Регион
    oh_hour: Optional[str] = None  # Моточасы
    last_activity: Optional[datetime] = None  # Время последней активности
    # sw_name: Optional[str] = None  # Имя текущего ПО
    description: Optional[str] = None  # Описание
    componentParts_id: Optional[int] = None  # ID компонента
    component_id: Optional[int] = None  # ID компонента
    comp_model: Optional[str] = None  # Модель компонента
    current_sw_version: Optional[int] = None  # Текущая версия ПО
    recommend_sw_version: Optional[str] = None  # Рекомендуемая версия ПО
    component_type: Optional[str] = None  # Тип компонента
    software_name:Optional[str] = None

    class Config:
        from_attributes = True
# ============================================
# Загрузка ПО
# ============================================
class AssignSoftwareRequest(BaseModel):
    """Запрос на назначение программного обеспечения"""
    # Поля ПО
    software_release_date: Optional[datetime] = None  # Дата выпуска
    software_description: Optional[str] = None  # Описание
    software_is_actual: Optional[bool] = None  # Актуальность
    software_is_archive: Optional[bool] = None  # Архивность
    software_is_critical: Optional[bool] = None  # Критичность
    software_status: Optional[str] = None  # Статус
    software_tractor_models: List[str] = Field(..., min_length=1)  # Массив моделей тракторов (обязательное поле)
    software_producer: str = Field(..., min_length=1)  # Производитель (обязательное поле)
    software_previous_version: Optional[int] = None  # Предыдущая версия
    
    # Информация о компоненте
    component_models: List[str] = Field(..., min_length=1)  # Модели компонентов (обязательное поле)
    component_types: List[str] = Field(..., min_length=1)  # Типы компонентов (обязательное поле)
    component_producers: List[str] = Field(..., min_length=1)  # Производители компонентов (обязательное поле)

class SoftwareMetadata(BaseModel):
    """Метаданные программного обеспечения"""
    id: int  # ID ПО
    name: str  # Имя файла
    inner_name: Optional[str] = None  # Внутреннее имя
    filename_original: str  # Оригинальное имя файла
    filename_for_download: str  # Имя файла для скачивания
    has_instruction: bool = False  # Есть ли инструкция
    instruction_filename: Optional[str] = None  # Имя файла инструкции
    release_date: Optional[datetime] = None  # Дата выпуска
    
    class Config:
        from_attributes = True


class SoftwareFileLocation(BaseModel):
    """Информация о местоположении файла ПО"""
    full_path: str  # Полный путь к файлу
    size_bytes: int  # Размер файла в байтах
    exists: bool  # Существует ли файл


class SoftwareInstructionLocation(BaseModel):
    """Информация о местоположении файла инструкции"""
    full_path: str  # Полный путь к файлу инструкции
    size_bytes: int  # Размер файла в байтах
    exists: bool  # Существует ли файл
    filename: str  # Имя файла


class UploadInstructionResponse(BaseModel):
    """Ответ на загрузку инструкции"""
    id: int  # ID инструкции
    instruction_path: str  # Путь к инструкции
    filename: str  # Имя файла
    size_bytes: int  # Размер в байтах
    message: str  # Сообщение
    
    class Config:
        from_attributes = True


class ArchiveChangeRequest(BaseModel):
    """Запрос на изменение архивности элемента"""
    is_archive: Optional[bool] = None  # Новое значение архивности


# Поддержка
class SupportMessageCreate(BaseModel):
    """Создание сообщения поддержки"""
    content: str = Field(..., min_length=1, max_length=2000)  # Содержание сообщения (обязательное поле)
    
    class Config:
        extra = "forbid"

class SupportReplyRequest(BaseModel):
    """Запрос ответа на сообщение"""
    message_id: int  # ID сообщения
    content: str = Field(..., min_length=1, max_length=2000)  # Содержание ответа

class SupportMessageDeleteRequest(BaseModel):
    """Запрос на удаление сообщения"""
    reason: Optional[str] = Field(None, max_length=500, description="Причина удаления")  # Причина удаления

class SupportMessageDeleteResponse(BaseModel):
    """Ответ после удаления сообщения"""
    status: str  # Статус операции
    message_id: int  # ID удаленного сообщения
    deleted_at: datetime  # Время удаления
    deleted_by: str  # Кем удалено
    cascade_deleted: int = 0  # Кол-во каскадно удаленных сообщений
    
    class Config:
        from_attributes = True

class SupportMessageResponse(BaseModel):
    """Ответ с сообщением поддержки"""
    id: int  # ID сообщения
    content: str  # Содержание сообщения
    created_at: datetime  # Время создания
    status: str  # Статус сообщения
    
    class Config:
        from_attributes = True


class UnreadRepliesCountResponse(BaseModel):
    """Ответ с количеством непрочитанных ответов"""
    unread_count: int  # Количество непрочитанных ответов

    class Config:
        from_attributes = True

class DealerNotificationCreate(BaseModel):
    """Схема для создания нового уведомления"""
    dealer_id: int = Field(..., gt=0, description="ID дилера")
    tractor_id: int = Field(..., gt=0, description="ID трактора")
    software_id: int = Field(..., gt=0, description="ID добавленного ПО")
    software_name: str = Field(..., max_length=255, description="Название ПО")
    software_version: str = Field(..., max_length=50, description="Версия ПО")
    message: Optional[str] = Field(None, max_length=500, description="Доп. сообщение")

    class Config:
        from_attributes = True

class DealerNotificationResponse(BaseModel):
    """Схема ответа с данными уведомления"""
    id: int
    dealer_id: int
    tractor_vin: Optional[str] = None
    software_name: str
    software_version: str
    message: Optional[str] = None
    is_read: bool = False
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class NotificationStatusUpdate(BaseModel):
    """Схема для обновления статуса прочтения"""
    is_read: bool = Field(..., description="Новый статус прочтения")