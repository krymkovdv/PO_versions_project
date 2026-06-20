from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean, Date, CHAR, Table, String, event, CheckConstraint
from datetime import datetime, timezone, date
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.attributes import get_history
from typing import Optional

# Базовый класс для всех моделей SQLAlchemy
class Base(DeclarativeBase): 
    pass

# Модель пользователя
# Хранит информацию о зарегистрированных пользователях системы
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)  # Уникальное имя пользователя
    password_hash = Column(String, nullable=False)  # Хэш пароля (не сам пароль!)
    role = Column(String, default="dealer", nullable=False)  # Роль пользователя (engineer, dealer, moderator)

    notifications = relationship("DealerNotification", back_populates="dealer")

    # Отношения: пользователь может отправлять сообщения и иметь статусы прочтения
    sent_messages = relationship("SupportMessage", foreign_keys="SupportMessage.sender_id", back_populates="sender")
    message_read_status = relationship("MessageReadStatus", foreign_keys="MessageReadStatus.moderator_id", back_populates="moderator")
    notifications = relationship("DealerNotification", foreign_keys="DealerNotification.dealer_id", back_populates="dealer")
    
    __table_args__ = (
            CheckConstraint(
                "role IN ('engineer', 'dealer', 'moderator')",
                name="check_user_role"
            ),
        )
    
# Модель трактора
# Хранит информацию о тракторах в системе
class Tractor(Base):
    __tablename__ = "tractors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model = Column(Text, nullable=False)  # Модель трактора
    vin = Column(Text, unique=True, nullable=False)  # VIN номер (уникальный)
    oh_hour = Column(Integer, default=0)  # Моточасы (часы работы двигателя)
    last_activity = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)  # Последняя активность
    assembly_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)  # Дата сборки
    region = Column(Text, nullable=False)  # Регион эксплуатации
    consumer = Column(Text, nullable=False)  # Потребитель (владелец)
    dealer = Column(Text, nullable=False)  # Дилер (поставщик/обслуживающий)
    
    # Отношение к связям трактор-ПО-компонент
    tractor2SoftAndComp = relationship('Tractor_Software_And_Component_Link', back_populates= 'tractor')
    

# Модель компонента
# Хранит информацию о компонентах трактора (двигатель, коробка передач и т.д.)
class Component(Base):
    __tablename__ = 'components'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type = Column(Text, nullable=False)  # Тип компонента (DVS, KPP, RK, HR, BK, AUTOPILOT)
    name = Column(Text, unique=True, nullable=False)  # Название компонента
    producer = Column(Text, nullable=False)  # Производитель компонента

    # Отношение к связям компонент-ПО
    component2Soft = relationship('Software_Component_Link', back_populates='component')

    __table_args__ = (
            CheckConstraint(
                "type IN ('DVS', 'KPP', 'RK', 'HR', 'BK','AUTOPILOT')",
                name="check_component_type"
            ),
        )

# Модель программного обеспечения
# Хранит информацию о версиях ПО для компонентов тракторов
class Software(Base):
    __tablename__ = 'softwares'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(Text, nullable=False)  # Название ПО (вычисляемое поле в схеме)
    path = Column(Text, unique=True, nullable=True)  # Путь к файлу ПО
    release_date = Column(DateTime)  # Дата выпуска
    end_actuality = Column(DateTime)  # Дата окончания актуальности
    description = Column(Text)  # Описание ПО
    producer = Column(Text, nullable=False)  # Производитель ПО
    is_actual = Column(Boolean, default=True)  # Является ли ПО актуальным
    is_archive = Column(Boolean, default=False)  # Находится ли ПО в архиве
    is_critical = Column(Boolean, default=False)  # Является ли обновление критическим
    status = Column(Text, nullable=True)  # Статус ПО (serial, in operation, experienced)
    tractor_model = Column(Text, nullable=False)  # Модель трактора, для которой предназначено ПО
    previous_sw_version = Column(Integer, ForeignKey('softwares.id'))  # Предыдущая версия ПО
    path_instruction = Column(Text, unique=True, nullable=True)  # Путь к инструкции по установке

    # Отношения
    soft2Component = relationship('Software_Component_Link', back_populates='software')
    previous_version = relationship(
        'Software', 
        remote_side=[id],
        foreign_keys=[previous_sw_version]
    )

    __table_args__ = (
            CheckConstraint(
                "status IN ('serial', 'in operation', 'experienced')",
                name="check_software_status"
            ),
        )

# Модель связи между программным обеспечением и компонентами
# Реализует многие-ко-многим связь между ПО и компонентами
class Software_Component_Link(Base):
    __tablename__ = 'software_component_links'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    component_id = Column(Integer, ForeignKey('components.id'), nullable=False, index= True)  # ID компонента
    software_id = Column(Integer, ForeignKey('softwares.id'), nullable=False, index= True)  # ID ПО

    # Отношения к компоненту и ПО
    component = relationship("Component", foreign_keys=[component_id], back_populates="component2Soft")
    software = relationship("Software", foreign_keys=[software_id], back_populates="soft2Component")
    soft_comp_to_tractor = relationship("Tractor_Software_And_Component_Link", back_populates="software_component_link")

# Модель связи между трактором, ПО и компонентом
# Хранит информацию о том, какое ПО установлено на какие компоненты каких тракторов
class Tractor_Software_And_Component_Link(Base):
    __tablename__ = 'tractor_software_and_component_links'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    is_recom = Column(Boolean, default=True)  # Является ли установка рекомендованной
    tractor_id = Column(Integer, ForeignKey('tractors.id'), nullable=False, index= True)  # ID трактора
    soft_comp_link_id = Column(Integer, ForeignKey('software_component_links.id'), nullable=False, index= True)  # ID связи ПО-компонент

    # Отношения
    software_component_link = relationship("Software_Component_Link", foreign_keys=[soft_comp_link_id], back_populates="soft_comp_to_tractor")
    tractor = relationship("Tractor", foreign_keys=[tractor_id], back_populates="tractor2SoftAndComp")


# Модель сообщений поддержки
# Хранит сообщения пользователей в системе поддержки
class SupportMessage(Base):
    __tablename__ = "support_message"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(Text, nullable=False)  # Текст сообщения
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)  # Время создания
    is_read = Column(Boolean, default=False)  # Отметка о прочтении
    is_closed = Column(Boolean, default = False)  # Отметка о закрытии обращения
    sender_id = Column(Integer, ForeignKey('users.id'))  # ID отправителя
    parent_message_id = Column(Integer, ForeignKey('support_message.id'), nullable=True, index=True)  # ID родительского сообщения (для цепочек)

    # Отношения
    sender = relationship("UserDB", foreign_keys=[sender_id], back_populates="sent_messages")

    # Отношения для ответов на сообщения
    replies = relationship("SupportMessage", 
                          backref=backref("parent", remote_side=[id]),
                          cascade="all, delete-orphan")


# Модель статуса прочтения сообщений
# Отслеживает, кто и когда прочитал сообщения
class MessageReadStatus(Base):
    __tablename__ = "message_read_status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey('support_message.id'), nullable=False, index=True)  # ID сообщения
    moderator_id = Column(Integer, ForeignKey('users.id'),nullable=False, index=True)  # ID модератора, который прочитал
    is_read = Column(Boolean,default=False)  # Статус прочтения
    read_at = Column(DateTime, nullable=True)  # Время прочтения

    # Отношения
    message = relationship("SupportMessage", foreign_keys=[message_id])
    moderator = relationship("UserDB", foreign_keys=[moderator_id])


class DealerNotification(Base):
    __tablename__ = "dealer_notifications"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Связь с дилером (пользователем с ролью 'dealer')
    dealer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Связь с трактором (опционально)
    tractor_id = Column(Integer, ForeignKey("tractors.id"), nullable=True, index=True)
    tractor_vin = Column(String(17), nullable=True, index=True)  # Денормализация для быстрого поиска
    
    # Информация о ПО
    software_id = Column(Integer, ForeignKey("softwares.id"), nullable=False)
    software_name = Column(String(255), nullable=False)
    software_version = Column(String(50), nullable=False)
    
    # Текст уведомления
    message = Column(Text, nullable=True)
    
    # Статус прочтения
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Отношения
    dealer = relationship("UserDB", foreign_keys=[dealer_id], back_populates="notifications")
    # tractor = relationship("Tractor", foreign_keys=[tractor_id], back_populates="dealer_notifications")  # опционально

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type = Column(String(255), nullable=False)
    path = Column(Text, unique=True, nullable=False)