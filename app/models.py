from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean, Date, CHAR, Table, String, event
from datetime import datetime, timezone, date
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import get_history

class Base(DeclarativeBase): 
    pass

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="user")
 
class Tractors(Base):
    __tablename__ = "Tractors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model = Column(Text, nullable=False)
    vin = Column(Text, unique=True, nullable=False)
    oh_hour = Column(Integer, nullable=False)
    last_activity = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    assembly_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    region = Column(Text, nullable=False)
    consumer = Column(Text, nullable=False)
    serv_center = Column(Text, nullable=False)
    
    tel_trac = relationship('TelemetryComponents', back_populates='tractors')
    

class TelemetryComponents(Base):
    __tablename__ = 'TelemetryComponents'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tractor = Column(Integer, ForeignKey('Tractors.id'), nullable=False)
    component = Column(Integer, ForeignKey('Component.id'), nullable=False)
    time_rec = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    comp_ser_num = Column(Text, unique=True)
    mounting_date = Column(Date, nullable=False)
    current_sw_version = Column(Integer, ForeignKey('Software.id'), nullable=True)
    recommend_sw_version = Column(Integer, ForeignKey('Software.id'), nullable=True) 

    # Отношения
    components = relationship('Component', back_populates='tel_comp')
    tractors = relationship('Tractors', back_populates='tel_trac')
    current_soft = relationship('Software', foreign_keys=[current_sw_version], back_populates='current_telemetry_versions', uselist=False)
    recommended_soft = relationship('Software', foreign_keys=[recommend_sw_version], back_populates='recommended_telemetry_versions', uselist=False)

class Component(Base):
    __tablename__ = 'Component'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type = Column(Text, nullable=False)
    model = Column(Text, unique=True, nullable=False)
    number_of_parts = Column(Integer, nullable=False)
    producer_comp = Column(Text, nullable=False)
    
    parts = relationship("ComponentParts", back_populates="components")
    tel_comp = relationship('TelemetryComponents', back_populates='components')

class Software2ComponentPart(Base):
    __tablename__ = 'Software2ComponentPart'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    component_part_id = Column(Integer, ForeignKey('ComponentParts.id'), nullable=False)
    software_id = Column(Integer, ForeignKey('Software.id'), nullable=False)
    is_actual = Column(Boolean, default=False)  # флаг Major обновления
    status = Column(CHAR, nullable=False, default='serial')
    date_change_actual = Column(Date)  # дата изменения Major
    not_recom = Column(Text)
    date_change_record = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # дата изменения записи
    previous_sw_version = Column(Integer, ForeignKey('Software.id'))

    component_parts = relationship("ComponentParts", back_populates="software_link")
    software = relationship("Software", foreign_keys=[software_id], back_populates="components_links")
    previous_software = relationship('Software', foreign_keys=[previous_sw_version], back_populates='previous_in_links', uselist=False)

@event.listens_for(Software2ComponentPart, 'before_update')
def set_date_change_major_before_update(mapper, connection, target):
    if target.is_actual and hasattr(target, '_sa_instance_state'):
        attr_state = target._sa_instance_state
        hist = get_history(attr_state, 'is_actual')
        if hist.has_changes() and hist.deleted == [False] and hist.added == [True]:
            target.actual = date.today()

@event.listens_for(Software2ComponentPart, 'before_insert')
def set_date_change_major_before_insert(mapper, connection, target):
    if target.is_actual:
        target.date_change_actual = date.today()


class ComponentParts(Base):
    __tablename__ = 'ComponentParts'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    component = Column(Integer, ForeignKey('Component.id'), nullable=False)
    part_type = Column(Text, nullable=False)

    components = relationship("Component", back_populates="parts")
    software_link = relationship("Software2ComponentPart", back_populates="component_parts")

class Software(Base):
    __tablename__ = 'Software'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    path = Column(Text, unique=True, nullable=False)
    name = Column(Text, unique=True, nullable=False)
    inner_name = Column(Text, unique=True)
    release_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    description = Column(Text)
    producer = Column(Text, nullable=False)
    is_actual = Column(Boolean, default=True)
    status = Column(Text, nullable=True)
    tractor_id = Column(Integer, ForeignKey('Tractors.id'), nullable=True)  # Связь с трактором



    components_links = relationship("Software2ComponentPart", foreign_keys="[Software2ComponentPart.software_id]", back_populates="software")
    current_telemetry_versions = relationship('TelemetryComponents', foreign_keys="[TelemetryComponents.current_sw_version]", back_populates='current_soft')
    recommended_telemetry_versions = relationship('TelemetryComponents', foreign_keys="[TelemetryComponents.recommend_sw_version]", back_populates='recommended_soft')
    previous_in_links = relationship('Software2ComponentPart', foreign_keys="[Software2ComponentPart.previous_sw_version]", back_populates='previous_software')
    tractor = relationship("Tractors", foreign_keys=[tractor_id])