import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone


PRIVATE_KEY_PATH = '.ssh/id_rsa'
PUBLIC_KEY_PATH = '.ssh/id_rsa.pub'
EXPIRE_MINUTES = 30

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

with open(PRIVATE_KEY_PATH, 'r') as file:
    PRIVATE_KEY = file.read()

with open(PUBLIC_KEY_PATH, 'r') as file:
    PUBLIC_KEY = file.read()

def create_jwt(data: dict, expires_delta: timedelta = timedelta(minutes=EXPIRE_MINUTES)):
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    payload["iat"] = datetime.now(timezone.utc)
    payload["iss"] = 'pi.daazed.dev'
    return jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')

def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("TOKEN EXPIRED")
    except jwt.InvalidTokenError:
        raise ValueError("INVALID TOKEN")

def verify_password(password, hashed_password):
    return pwd_ctx.verify(password, hashed_password)

def hash_password(password):
    return pwd_ctx.hash(password)

