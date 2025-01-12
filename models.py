from typing import Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()



# Database Model
class MessageCreate(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_index = Column(
        String, nullable=True
    )  # this is the index stored on the modem
    message_type = Column(String, nullable=False)
    message_originating_address = Column(String, nullable=True)
    message_destination_address = Column(String, nullable=True)
    message_date = Column(String, nullable=False)
    message_time = Column(String, nullable=False)
    message_contents = Column(String, nullable=False)
    partial_key = Column(String, nullable=True)
    partial_count = Column(Integer, nullable=True)
    partial_index = Column(Integer, nullable=True)
    is_partial = Column(Boolean, nullable=False)
    in_sim_memory = Column(Boolean, nullable=True)
    is_sent = Column(Boolean, nullable=True)

class Messages(BaseModel):
    id: Optional[int] = None
    message_index: Optional[str] = None
    message_type: str
    message_originating_address: Optional[str] = None
    message_destination_address: Optional[str] = None
    message_date: str
    message_time: str
    message_contents: str
    partial_key: Optional[str] = None
    partial_count: Optional[int] = None
    partial_index: Optional[int] = None
    is_partial: bool
    in_sim_memory: bool
    is_sent: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class InfoResponse(BaseModel):
    hostname: str
    uname: str
    date: str
    arch: str


class StatusResponse(BaseModel):
    at: str
    cnum: str
    csq: str
    cpin: str
    creg: str
    cops: str
    gpsinfo: str
    data: str
    dns: str
    apn: str


class SendMessageRequest(BaseModel):
    number: str
    msg: str


class AtRequest(BaseModel):
    cmd: str = "AT"
