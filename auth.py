import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models.doctor import Doctor
from models.patient import Patient
from utils.helper import verify_password

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT settings (replace with environment variables in production)
SECRET_KEY = "your-secret-key-please-change-this"  # Use a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180  # 3 hours
# OAuth2 scheme for token validation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")  # Generic token endpoint

# Pydantic model for login request
class LoginRequest(BaseModel):
    email: str
    password: str

class UserType:
    DOCTOR = "doctor"
    PATIENT = "patient"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, email: str, password: str, user_type: str) -> Optional[dict]:
    """
    Authenticate a doctor or patient by email and password.
    """
    if user_type == UserType.DOCTOR:
        user = db.query(Doctor).filter(Doctor.email == email).first()
    elif user_type == UserType.PATIENT:
        user = db.query(Patient).filter(Patient.email == email).first()
    else:
        return None

    if not user or not verify_password(password, user.password):
        return None

    return {"id": user.id, "email": user.email, "user_type": user_type}

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get the current user from a JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        user_type: str = payload.get("user_type")
        if user_id is None or user_type not in [UserType.DOCTOR, UserType.PATIENT]:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if user_type == UserType.DOCTOR:
        user = db.query(Doctor).filter(Doctor.id == user_id).first()
    else:
        user = db.query(Patient).filter(Patient.id == user_id).first()

    if user is None:
        raise credentials_exception

    return {"user": user, "user_type": user_type}

def get_current_doctor(current_user: dict = Depends(get_current_user)):
    """
    Ensure the current user is a doctor.
    """
    if current_user["user_type"] != UserType.DOCTOR:
        raise HTTPException(status_code=403, detail="Not authorized as a doctor")
    return current_user["user"]

def get_current_patient(current_user: dict = Depends(get_current_user)):
    """
    Ensure the current user is a patient.
    """
    if current_user["user_type"] != UserType.PATIENT:
        raise HTTPException(status_code=403, detail="Not authorized as a patient")
    return current_user["user"]