from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean, Date, CHAR, Table, String, event,CheckConstraint
from datetime import datetime, timezone, date
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.attributes import get_history

class Base(DeclarativeBase): 
    pass

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="dealer", nullable=False)

    sent_messages = relationship("SupportMessage", foreign_keys="SupportMessage.sender_id", back_populates="sender")
    message_read_status = relationship("MessageReadStatus", foreign_keys="MessageReadStatus.moderator_id", back_populates="moderator")
    
    __table_args__ = (
            CheckConstraint(
                "role IN ('engineer', 'dealer', 'moderator')",
                name="check_user_role"
            ),
        )
    
class Tractor(Base):
    __tablename__ = "tractors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model = Column(Text, nullable=False)
    vin = Column(Text, unique=True, nullable=False)
    oh_hour = Column(Integer, default=0)
    last_activity = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    assembly_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    region = Column(Text, nullable=False)
    consumer = Column(Text, nullable=False)
    dealer = Column(Text, nullable=False)
    
    tractor2SoftAndComp = relationship('Tractor_Software_And_Component_Link', back_populates= 'tractor')
    

class Component(Base):
    __tablename__ = 'components'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type = Column(Text, nullable=False)
    name = Column(Text, unique=True, nullable=False)
    producer = Column(Text, nullable=False)

    component2Soft = relationship('Software_Component_Link', back_populates='component')

    __table_args__ = (
            CheckConstraint(
                "type IN ('DVS', 'KPP', 'RK', 'HR', 'BK')",
                name="check_component_type"
            ),
        )

class Software(Base):
    __tablename__ = 'softwares'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    path = Column(Text, unique=True, nullable=False)
    release_date = Column(DateTime)
    end_actuality = Column(DateTime)
    description = Column(Text)
    producer = Column(Text, nullable=False)
    is_actual = Column(Boolean, default=True)
    is_archive = Column(Boolean, default=False)
    is_critical = Column(Boolean, default=False)
    status = Column(Text, nullable=True)
    tractor_model = Column(Text, nullable=False) 
    previous_sw_version = Column(Integer, ForeignKey('softwares.id'))
    path_instruction = Column(Text, unique=True, nullable=True)

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

class Software_Component_Link(Base):
    __tablename__ = 'software_component_links'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    component_id = Column(Integer, ForeignKey('components.id'), nullable=False, index= True)
    software_id = Column(Integer, ForeignKey('softwares.id'), nullable=False, index= True)

    component = relationship("Component", foreign_keys=[component_id], back_populates="component2Soft")
    software = relationship("Software", foreign_keys=[software_id], back_populates="soft2Component")
    soft_comp_to_tractor = relationship("Tractor_Software_And_Component_Link", back_populates="software_component_link")

class Tractor_Software_And_Component_Link(Base):
    __tablename__ = 'tractor_software_and_component_links'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    is_recom = Column(Boolean, default=True)
    tractor_id = Column(Integer, ForeignKey('tractors.id'), nullable=False, index= True)
    soft_comp_link_id = Column(Integer, ForeignKey('software_component_links.id'), nullable=False, index= True)

    software_component_link = relationship("Software_Component_Link", foreign_keys=[soft_comp_link_id], back_populates="soft_comp_to_tractor")
    tractor = relationship("Tractor", foreign_keys=[tractor_id], back_populates="tractor2SoftAndComp")



#Обратная свзяь 

class SupportMessage(Base):
    __tablename__ = "support_message"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_read = Column(Boolean, default=False)
    is_closed = Column(Boolean, default = False)
    sender_id = Column(Integer, ForeignKey('users.id'))
    parent_message_id = Column(Integer, ForeignKey('support_message.id'), nullable=True, index=True)

    sender = relationship("UserDB", foreign_keys=[sender_id], back_populates="sent_messages")

    replies = relationship("SupportMessage", 
                          backref=backref("parent", remote_side=[id]),
                          cascade="all, delete-orphan")


class MessageReadStatus(Base):
    __tablename__ = "message_read_status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey('support_message.id'), nullable=False, index=True)
    moderator_id = Column(Integer, ForeignKey('users.id'),nullable=False, index=True)
    is_read = Column(Boolean,default=False)
    read_at = Column(DateTime, nullable=True)

    message = relationship("SupportMessage", foreign_keys=[message_id])
    moderator = relationship("UserDB", foreign_keys=[moderator_id])
