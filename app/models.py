from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import  Column, Integer, Text, DateTime, ForeignKey, Boolean, Date, CHAR, Table
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class Base(DeclarativeBase): pass
 
class Tractors(Base):
    __tablename__ = 'Tractors'

    id = Column(Integer, primary_key=True, index = True)
    model = Column(Text, unique = True)
    vin = Column(Text, unique=True, nullable = False)
    oh_hour = Column(Integer)
    last_activity = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    assembly_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    tel_trac = relationship('TelemetryComponents', back_populates='tractors')

class TelemetryComponents(Base):
    __tablename__ = 'TelemetryComponents'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    software = Column(Integer, ForeignKey('Software.id'), nullable=False)
    tractor = Column(Integer, ForeignKey('Tractors.id'), unique=True, nullable=False)
    component = Column(Integer, ForeignKey('Component.id'), unique=True, nullable=False)
    time_rec = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    serial_number = Column(Text, unique=True) 

    components = relationship('Component', back_populates='tel_comp')
    tractors = relationship('Tractors', back_populates='tel_trac')
    softwares = relationship('Software', back_populates='telemetry')

SoftwareComponents = Table('SoftwareComponents',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('ComponentId', Integer, ForeignKey('Component.id'), nullable = False),
    Column('SoftwareId', Integer, ForeignKey('Software.id'), nullable = False),
    Column('Is_major', Boolean),
    Column('Status', CHAR, nullable=False, default='S'),
    Column('Date_change', Date))  

class Component(Base):
    __tablename__='Component'

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Text, nullable=False)
    model = Column(Text, unique = True, nullable=False)
    date_create = Column(Date, nullable=False)

    tel_comp= relationship('TelemetryComponents', back_populates='components')
    comp_soft = relationship('Software', secondary = SoftwareComponents, back_populates='soft_comp')
                 
class Software(Base):
    __tablename__ = 'Software'

    id = Column(Integer, primary_key=True, index=True)
    path= Column(Text, unique = True, nullable=False)
    name = Column(Text, unique = True, nullable=False)
    inner_name = Column(Text, unique = True)
    prev_version = Column(Integer, ForeignKey('Software.id'))
    next_version = Column(Integer, ForeignKey('Software.id'))
    release_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    soft_comp = relationship('Component', secondary = SoftwareComponents, back_populates='comp_soft')
    telemetry = relationship('TelemetryComponents', back_populates='softwares')
    # Связи, где этот Software — software1
    as_software1 = relationship(
        'Relations',
        foreign_keys='Relations.software1',
        back_populates='sw1'
    )
    # Связи, где этот Software — software2
    as_software2 = relationship(
        'Relations',
        foreign_keys='Relations.software2',
        back_populates='sw2'
    )

class Relations(Base):
    __tablename__ = 'Relations'

    id = Column(Integer, primary_key=True, index=True)
    software1 = Column(Integer, ForeignKey('Software.id'), nullable=False)
    software2 = Column(Integer, ForeignKey('Software.id'), nullable=False)

    sw1 = relationship('Software', foreign_keys=[software1], back_populates='as_software1')
    sw2 = relationship('Software', foreign_keys=[software2], back_populates='as_software2')

