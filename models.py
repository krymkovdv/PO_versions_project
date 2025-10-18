from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from datetime import datetime, timezone


class Base(DeclarativeBase): pass


class Tractors(Base):
    __tablename__ = 'tractors'

    row_id = Column(Integer, primary_key=True, index = True)
    model = Column(Text)
    terminal_id = Column(Integer)
    region = Column(String)
    owner_name = Column(String)
    assembly_date = Column(DateTime, default = datetime.now)
    comp_list = relationship('TractorComponent', back_populates='tractors')


class TractorComponent(Base):
    __tablename__='tractor_component'

    row_id = Column(Integer, primary_key=True,index=True)
    time_comp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    tractor = Column(Integer, ForeignKey('tractors.row_id'))

    tractors = relationship('Tractors', back_populates='comp_list')


class Components(Base):
    __tablename__ = 'components'

    id = Column(Integer, primary_key=True, index=True)
    Fact_num_comp = Column(Text)
    Type_comp = Column(Text)
    
    archive_list = relationship('Archiv_FW', back_populates='comp_list', uselist=False)




class Archiv_FW(Base):
    __tablename__ = 'arkhiv_fw'

    id = Column(Integer, primary_key=True, index=True)
    inner_version = Column(Text)
    producer_version = Column(Text)

    comp_id = Column(Integer, ForeignKey('components.id'), unique=True)
    comp_list = relationship('Components', back_populates='archive_list')

