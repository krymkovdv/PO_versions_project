from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import  Column, Integer, Text, DateTime, ForeignKey, Boolean, Date, CHAR, Table, String
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class Base(DeclarativeBase): pass



class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="user")
 
class Tractors(Base):
    __tablename__ = 'Tractors'

    id = Column(Integer, primary_key=True, index = True)
    model = Column(Text, nullable= False)
    vin = Column(Text, unique=True, nullable = False)
    oh_hour = Column(Integer, nullable= False)
    last_activity = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable= False)
    assembly_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable= False)
    region = Column(Text, nullable = False)
    consumer = Column(Text, nullable = False)
    serv_center = Column(Text, nullable = False)
    
    tel_trac = relationship('TelemetryComponents', back_populates='tractors')
    components = relationship('Component', back_populates='tractors')

class TelemetryComponents(Base):
    __tablename__ = 'TelemetryComponents'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    software = Column(Integer, ForeignKey('Software.id'), nullable=False)
    tractor = Column(Integer, ForeignKey('Tractors.id'), nullable=False)
    component = Column(Integer, ForeignKey('Component.id'), nullable=False)
    component_part_id = Column(Integer, ForeignKey('ComponentParts.id'), nullable=True)
    time_rec = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    components = relationship('Component', back_populates='tel_comp')
    tractors = relationship('Tractors', back_populates='tel_trac')
    softwares = relationship('Software', back_populates='telemetry')
    component_part = relationship("ComponentParts", back_populates="telemetry_records")

class Component(Base):
    __tablename__='Component'

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Text, nullable=False)
    model = Column(Text, unique = True, nullable=False)
    comp_ser_num = Column(Text, unique = True)
    mounting_date = Column(Date, nullable=False)
    tractor_id = Column(Integer, ForeignKey('Tractors.id'), nullable=False)
    number_of_parts = Column(Integer, nullable=False)
    producer_comp = Column(Text, nullable=False)
    
    parts = relationship("ComponentParts", back_populates="components")
    tel_comp= relationship('TelemetryComponents', back_populates='components')
    tractors = relationship('Tractors', back_populates='components')
                 
class Software2ComponentPart(Base):
    __tablename__ = 'Software2ComponentPart'

    id = Column(Integer, primary_key=True)
    component_part_id = Column(Integer, ForeignKey('ComponentParts.id'), nullable=False)
    software_id = Column(Integer, ForeignKey('Software.id'), nullable=False)
    is_major = Column(Boolean, default=False)
    status = Column(CHAR, nullable=False, default='S')
    date_change = Column(Date)
    not_recom = Column(Text)
    date_change_record = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    component_parts = relationship("ComponentParts", back_populates="software_link")
    software = relationship("Software", back_populates="components_links")


class ComponentParts(Base):
    __tablename__='ComponentParts'

    id = Column(Integer, primary_key=True, index=True)
    component = Column(Integer, ForeignKey('Component.id'), nullable=False)
    part_number = Column(Text, unique = True, nullable=False)
    part_type = Column(Text, nullable=False)
    current_sw_version = Column(Integer, ForeignKey('Software.id'), nullable=False)
    recommend_sw_version = Column(Integer, ForeignKey ('Software.id'), nullable=False)
    is_major = Column(Boolean, default=False)
    not_recom_sw = Column(Text)
    next_ver = Column(Text)


    components = relationship("Component", back_populates="parts")
    software_link = relationship("Software2ComponentPart", back_populates="component_parts")
    telemetry_records = relationship("TelemetryComponents", back_populates="component_part")
    current_soft = relationship('Software', back_populates='current_vers', foreign_keys=[current_sw_version], uselist= False)
    recommended_soft = relationship('Software', back_populates='recommended_vers', foreign_keys=[recommend_sw_version], uselist= False)
                 
class Software(Base):
    __tablename__ = 'Software'

    id = Column(Integer, primary_key=True, index=True)
    path= Column(Text, unique = True, nullable=False)
    name = Column(Text, unique = True, nullable=False)
    inner_name = Column(Text, unique = True)
    release_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    description = Column(Text)

    components_links = relationship("Software2ComponentPart", back_populates="software")
    telemetry = relationship('TelemetryComponents', back_populates='softwares')
    current_vers = relationship('ComponentParts', back_populates='current_soft', foreign_keys="[ComponentParts.current_sw_version]")
    recommended_vers = relationship('ComponentParts', back_populates='recommended_soft', foreign_keys="[ComponentParts.recommend_sw_version]")

