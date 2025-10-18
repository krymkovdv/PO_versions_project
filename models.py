from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import  Column, Integer, String, Text, DateTime, Double, ForeignKey
from datetime import datetime, timezone
from sqlalchemy.orm import relationship

class Base(DeclarativeBase): pass
 
class Tractors(Base):
    __tablename__ = 'tractors'

    terminal_id = Column(Integer, primary_key=True, index = True)
    model = Column(Text)
    region = Column(String)
    owner_name = Column(String)
    assembly_date = Column(DateTime, default = datetime.now)
    comp_list = relationship('TractorComponent', back_populates='tractors')


class TractorComponent(Base):
    __tablename__='tractor_component'

    row_id = Column(Integer, primary_key=True,index=True)
    time_comp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    tractor = Column(Integer, ForeignKey('tractors.terminal_id'), nullable=False)

    tractors = relationship('Tractors', back_populates='comp_list')



class Archiv_FW(Base):
    __tablename__ = 'arkhiv_fw'

    id = Column(Integer, primary_key=True, index=True)
    inner_version = Column(Text)
    producer_version = Column(Text)

    # comp_id = Column(Integer, ForeignKey('components.id'), unique=True)
    # comp_list = relationship('Components', back_populates='archive_list')


#класс компонентов
class Components(Base):
    __tablename__ = 'Components'

    id_comp = Column(Integer, primary_key=True, index=True)
    fact_num_comp = Column(Text, nullable=False)
    type_comp = Column(String(255), nullable=False)
    model_comp = Column(Text, nullable=False)
    year_comp = Column(DateTime)  
    current_version = Column(Double(precision=53))  
    recommended_version = Column(Double(precision=53))
    maj_Min = Column(String(255))
    time_cur = Column(DateTime)
    time_rec = Column(DateTime)
    time_m = Column(DateTime)

    # Связь с Firmwares: один компонент может иметь одну рекомендованную прошивку
    firmware_recommended = relationship("Firmwares", back_populates="component_recommended",
                                        foreign_keys="Firmwares.id_Firmwares")

    # Связь с Firmwares: один компонент может иметь текущую прошивку
    firmware_current = relationship("Firmwares", back_populates="component_current",
                                    foreign_keys="Firmwares.id_Firmwares")


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

   # Обратная связь с компонентами
   component_recommended = relationship("Component", back_populates="firmware_recommended",
                                         foreign_keys="Components.recommended_version")
   component_current = relationship("Component", back_populates="firmware_current",
                                     foreign_keys="Components.current_version")