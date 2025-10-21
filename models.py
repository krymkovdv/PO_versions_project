from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import  Column, Integer, String, Text, DateTime, Double, ForeignKey, Boolean, Date
from datetime import datetime, timezone
from sqlalchemy.orm import relationship

class Base(DeclarativeBase): pass
 
class Tractors(Base):
    __tablename__ = 'Tractors'

    terminal_id = Column(Integer, primary_key=True, index = True)
    model = Column(Text)
    region = Column(String)
    owner_name = Column(String)
    assembly_date = Column(DateTime, default = datetime.now)
    
    comp_list = relationship('TractorComponent', back_populates='tractors')


class TractorComponent(Base):
    __tablename__='TractorComponent'

    row_id = Column(Integer, primary_key=True,index=True)
    time_comp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    tractor = Column(Integer, ForeignKey('Tractors.terminal_id'), nullable=False)
    comp_id = Column(Integer, ForeignKey('TelemetryComponents.id_telemetry'), unique=True)

    tractors = relationship('Tractors', back_populates='comp_list')
    comp_rel = relationship('TelemetryComponents', back_populates='trac_comp_rel')

0# class Archive_FW(Base):
#     __tablename__ = 'Archive_fw'

#     id = Column(Integer, primary_key=True, index=True)
#     inner_version = Column(Text)
#     producer_version = Column(Text)
#     components = Column(Integer,ForeignKey('Components.id_comp'), unique=True)

#     comp_list = relationship('Components', back_populates='archive_list')




class TrueComponents(Base):
    __tablename__='TrueComponents'

    id = Column(Integer, primary_key=True, index=True)
    Type_component = Column(Text, nullable=False)
    Model_component = Column(Text, nullable=False)
    Year_component = Column(Date, nullable=False)

    telemetry_rel = relationship('TelemetryComponents', back_populates='true_rel')

class TelemetryComponents(Base):
    __tablename__ = 'TelemetryComponents'

    id_telemetry = Column(Integer, primary_key=True, index=True,autoincrement=True)
    true_comp = Column(Integer, ForeignKey('TrueComponents.id'), nullable=False)
    current_version = Column(Integer, ForeignKey('Firmwares.id_Firmwares'), unique=True, nullable=False)
    is_maj = Column(Boolean, nullable=False)

    firmware_rel = relationship('Firmwares', back_populates='telemetry')
    trac_comp_rel = relationship('TractorComponent', back_populates='comp_rel', uselist=False)
    true_rel = relationship('TrueComponents', back_populates='telemetry_rel')




#класс прошивок
class Firmwares(Base):
    __tablename__ = 'Firmwares'

    id_Firmwares = Column(Integer, primary_key=True, index=True)
    inner_version = Column(Text, nullable=False)
    producer_version = Column(Text, nullable=False)
    download_link = Column(Text, nullable=False)
    release_date = Column(DateTime)
    maj_to = Column(String(255))  
    min_to = Column(String(255))
    maj_for_c_model = Column(String(255))  
    min_for_c_model = Column(String(255))
    time_Maj = Column(DateTime)
    time_Min = Column(DateTime)
   
    telemetry = relationship('TelemetryComponents', back_populates='firmware_rel', 
                                    uselist=False)





