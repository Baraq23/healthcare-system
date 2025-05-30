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
SECRET_KEY = "healthcare123" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180  # 3 hours

# OAuth2 scheme for token validation
oauth2_doctor_scheme = OAuth2PasswordBearer(tokenUrl="/doctors/login")
oauth2_patient_scheme = OAuth2PasswordBearer(tokenUrl="/patients/login")

# Pydantic model for login request
class LoginRequest(BaseModel):
    username: str
    password: str

class UserType:
    DOCTOR = "doctor"
    PATIENT = "patient"



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(db: Session, email: str, password: str, user_type: str) -> Optional[dict]:
    """
    Authenticate a doctor or patient by email and password.
    """
    if user_type == UserType.DOCTOR:
        user = db.query(Doctor).filter(Doctor.email == email).first()
    elif user_type == UserType.PATIENT:
        user = db.query(Patient).filter(Patient.email == email).first()
    else:
        print("def authenticate_user:: User authentication by user or passwor FAILED")
        return None

    if not user or not verify_password(password, user.password):
        print("Failed: returned None: User not authenticated, or password not verified")
        return None

    print('SUCCESS: (id": user.id, "email": user.email, "user_type": user_type) Returned')
    return {"id": user.id, "email": user.email, "user_type": user_type}





# Doctor-specific dependency
async def get_current_doctor(
    token: str = Depends(oauth2_doctor_scheme), 
    db: Session = Depends(get_db)
) -> Doctor:
    payload = decode_token(token)
    user_type = payload.get("user_type")
    user_id = payload.get("sub")
    
    if user_type != UserType.DOCTOR or not user_id:
        raise HTTPException(status_code=403, detail="Not authorized as a doctor")
    
    doctor = db.query(Doctor).filter(Doctor.id == user_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    return doctor

# Patient-specific dependency
async def get_current_patient(
    token: str = Depends(oauth2_patient_scheme), 
    db: Session = Depends(get_db)
) -> Patient:
    payload = decode_token(token)
    user_type = payload.get("user_type")
    user_id = payload.get("sub")
    
    if user_type != UserType.PATIENT or not user_id:
        raise HTTPException(status_code=403, detail="Not authorized as a patient")
    
    patient = db.query(Patient).filter(Patient.id == user_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return patient

# Helper to decode token (reusable)
def decode_token(token: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception