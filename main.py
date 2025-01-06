# TODO: ! sqlcipher, totp, api key, websocket !
"""FastAPI for SIMCOM 7600G-H"""

import logging
import os
import asyncio
import subprocess
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, status, Depends
from pydantic import BaseModel, ValidationError, ConfigDict
from pi7600 import GPS, SMS, TIMEOUT, Settings

# Integrate into uvicorn logger
logger = logging.getLogger("uvicorn.pi7600")
logger.info("Initializing sim modules")

app = FastAPI()
cwd = os.getcwd()
sms = SMS()
gps = GPS()
settings = Settings()

logger.info("Sim modules ready")

# Database
DATABASE_URL = "sqlite:///./cmgl.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    logger.info("Starting database session")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
    in_sim_memory = Column(Boolean, nullable=True)
    is_sent = Column(Boolean, nullable=True)


async def create_message(db: Session, message: MessageCreate):
    existing_message = (
        db.query(MessageCreate)
        .filter(
            MessageCreate.message_contents == message.message_contents,
            MessageCreate.message_date == message.message_date,
            MessageCreate.message_time == message.message_time,
        )
        .first()
    )
    if existing_message:
        if existing_message.in_sim_memory != message.in_sim_memory:
            logger.info("Message exists, updating...")
            existing_message.in_sim_memory = message.in_sim_memory
            db.commit()
            db.refresh(existing_message)
        logger.info("Message exists, skipping...")
        return
    if message.message_type == "SENT":
        logger.info("Checking if message needs to be sent...")
        if not message.is_sent:
            logger.info(
                f"Sending message\n{message.message_destination_address}\n{message.message_contents}"
            )
            try:
                is_success = await sms.send_message(
                    message.message_destination_address, message.message_contents
                )
                if is_success:
                    message.is_sent = True
            except Exception as e:
                logger.error(f"create_message: {e}")
                return
    logger.info("Commiting message to database")
    db_message = MessageCreate(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)


async def messages_from_db(db: Session):
    messages_db = db.query(MessageCreate).all()
    messages_pydantic = [Messages.model_validate(msg) for msg in messages_db]
    return messages_pydantic


async def messages_to_delete(db: Session):
    messages_delete = (
        db.query(MessageCreate).filter(MessageCreate.in_sim_memory == True).all()
    )
    for msg in messages_delete:
        logger.info(f"Deleting message at idx: {msg.message_index}")
        await sms.delete_message(msg_idx=int(msg.message_index))
        msg.in_sim_memory = False
        db.commit()
        db.refresh(msg)


async def delete_db_message(db: Session, msg_idx: int):
    message_db = db.query(MessageCreate).filter(MessageCreate.id == msg_idx).first()
    if message_db:
        if message_db.in_sim_memory == True:
            await sms.delete_message(msg_idx=msg_idx)
        db.delete(message_db)
        db.commit()
        logger.info(f"Message id: {msg_idx} deleted")
    return


Base.metadata.create_all(bind=engine)


class Messages(BaseModel):
    id: Optional[int] = None
    message_index: Optional[str]
    message_type: str
    message_originating_address: Optional[str]
    message_destination_address: Optional[str]
    message_date: str
    message_time: str
    message_contents: str
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


# API
@app.get("/", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def root() -> StatusResponse:
    """Parses out modem and network information

    Returns:
        dict: Various network and device checks
    """
    logger.info("Compiling modem status information")

    # Ensure to await all asynchronous calls
    at_check = await settings.send_at("AT", "OK", TIMEOUT)
    at = at_check.splitlines()[2] if at_check else "ERROR"

    cnum_check = await settings.send_at("AT+CNUM", "+CNUM:", TIMEOUT)
    cnum = (
        cnum_check.splitlines()[2].split(",")[1].replace('"', "")
        if cnum_check
        else "ERROR"
    )

    csq_check = await settings.send_at("AT+CSQ", "OK", TIMEOUT)
    csq = csq_check.splitlines()[2] if csq_check else "ERROR"

    cpin_check = await settings.send_at("AT+CPIN?", "READY", TIMEOUT)
    cpin = cpin_check.splitlines()[2] if cpin_check else "ERROR"

    creg_check = await settings.send_at("AT+CREG?", "OK", TIMEOUT)
    creg = creg_check.splitlines()[2] if creg_check else "ERROR"

    cops_check = await settings.send_at("AT+COPS?", "OK", TIMEOUT)
    cops = cops_check.splitlines()[2] if cops_check else "ERROR"

    # Await the GPS position asynchronously
    gps_check = await gps.get_gps_position()  # Await the GPS position
    gpsinfo = gps_check if gps_check else "ERROR"

    # Asynchronously run subprocess commands using asyncio.create_subprocess_exec
    data_check = await run_async_subprocess(
        ["ping", "-I", "usb0", "-c", "1", "1.1.1.1"]
    )
    data = "ERROR" if "Unreachable" in data_check else "OK"

    dns_check = await run_async_subprocess(
        ["ping", "-I", "usb0", "-c", "1", "www.google.com"]
    )
    dns = "ERROR" if "Unreachable" in dns_check else "OK"

    apn_check = await settings.send_at("AT+CGDCONT?", "OK", TIMEOUT)
    apn = (
        ",".join(apn_check.splitlines()[2].split(",")[2:3])[1:-1]
        if apn_check
        else "ERROR"
    )

    return StatusResponse(
        at=at,
        cnum=cnum,
        csq=csq,
        cpin=cpin,
        creg=creg,
        cops=cops,
        gpsinfo=gpsinfo,
        data=data,
        dns=dns,
        apn=apn,
    )


async def run_async_subprocess(cmd: List[str]) -> str:
    """Runs a subprocess command asynchronously and captures its output."""
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode() if stdout else stderr.decode()


@app.get("/info", response_model=InfoResponse, status_code=status.HTTP_200_OK)
async def info() -> InfoResponse:
    """Host device information

    Returns:
        dict: hostname, uname, date, arch
    """
    logger.info("Compiling host device information")

    hostname = await run_async_subprocess(["hostname"])
    uname = await run_async_subprocess(["uname", "-r"])
    date = await run_async_subprocess(["date"])
    arch = await run_async_subprocess(["arch"])

    return InfoResponse(
        hostname=hostname.strip(),
        uname=uname.strip(),
        date=date.strip(),
        arch=arch.strip(),
    )


@app.get("/sms", response_model=List[Messages], status_code=status.HTTP_200_OK)
async def sms_root(
    msg_query: str = "ALL", db: Session = Depends(get_db)
) -> List[Messages]:
    """Read messages from modem
    Args:
        msg_query (str, optional): ["ALL", "REC READ", "REC UNREAD", "STO UNSENT", "STO SENT"]. Defaults to "ALL".

    Returns:
        List<dict>: [{Messages}, {Messages}]
    """
    logger.info(f"Reading {msg_query} messages")

    # Await the receive_message function to ensure async execution
    raw_messages = await sms.receive_message(message_type=msg_query)
    for raw_msg in raw_messages:
        try:
            # this should set true for any message read from the sim
            # since the storage is limited, this can be used to remove later
            raw_msg["in_sim_memory"] = True
            message = Messages(**raw_msg)
            await create_message(db=db, message=message)
        except ValidationError as e:
            logger.error(f"Validation error: {e} for raw message: {raw_msg}")
            continue
    return await messages_from_db(db=db)


@app.delete("/sms/delete/{msg_idx}", status_code=status.HTTP_202_ACCEPTED)
async def delete_msg(msg_idx: int, db: Session = Depends(get_db)) -> dict:
    """Delete sms message by MODEM index

    Args:
        msg_idx (int): MODEM message index

    Returns:
        dict: {"response": "Success"} | False
    """
    logger.info(f"DELETED_SMS: {msg_idx}")
    # resp = await sms.delete_message(msg_idx)  # Await the async delete_message call
    await delete_db_message(db=db, msg_idx=msg_idx)
    return {"response": "Ok"}


@app.delete("/sms/cleanup/", status_code=status.HTTP_202_ACCEPTED)
async def clear_sim_memory(db: Session = Depends(get_db)) -> dict:
    logger.info("Clearing sim sms memory")
    await messages_to_delete(db=db)
    return {"response": "Ok"}


@app.post("/sms", status_code=status.HTTP_201_CREATED)
async def send_msg(
    request: SendMessageRequest,
    db: Session = Depends(get_db),
) -> Messages:
    """POST SMS Message to destination number

    Args:
        msg (str): sms text body
        number (str): sms destination number

    Returns:
        MessageCreate
    """
    logger.info("/sms: Received request to send message")
    # Await the async send_message call
    current_time = datetime.now()
    msg = Messages(
        message_index=None,
        message_type="SENT",
        message_originating_address=None,
        message_destination_address=request.number,
        message_date=current_time.strftime("%Y-%d-%m"),
        message_time=current_time.strftime("%H:%M:%S"),
        message_contents=request.msg,
        in_sim_memory=False,
        is_sent=False,
    )
    await create_message(db=db, message=msg)  # TODO: return db message in create_message instead to avoid this next bit
    db_msg = (
        db.query(MessageCreate)
        .filter(
            MessageCreate.message_contents == msg.message_contents,
            MessageCreate.message_date == msg.message_date,
            MessageCreate.message_time == msg.message_time,
        )
        .first()
    )
    return db_msg


@app.post("/at", status_code=status.HTTP_202_ACCEPTED)
async def catcmd(request: AtRequest) -> str:
    r"""Sends raw AT commands to modem and returns raw stdout, will not work with commands that require input, return response

    Args:
        cmd (str, optional): Defaults to "AT".

    Returns:
        str: raw stdout response if "OK" or "ERROR" if "\r\n" is returned
    """
    logger.info(f"Sending AT cmd: {request.cmd}")
    # Run command asynchronously if possible, otherwise handle it synchronously
    resp = subprocess.run(
        ["./scripts/catcmd", request.cmd], capture_output=True, text=True, check=False
    ).stdout
    return resp
