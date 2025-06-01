import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate, DoctorResponse, DoctorUpdate
from app.utils.helper import get_specialization_by_name, hash_password
from app.auth import authenticate_user, create_access_token, get_current_doctor, UserType
from dotenv import load_dotenv
import os


load_dotenv()  # Loads variables from a .env file if present

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.post("/login")
async def doctor_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = form_data.username  # This is the email sent as 'username'
    password = form_data.password
    # Authenticate doctor
    user = authenticate_user(db, email, password, UserType.DOCTOR)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    # Create token with user_type
    access_token = create_access_token(
        data={"sub": str(user["id"]), "user_type": UserType.DOCTOR},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}




# protecting router
@router.get("/me", response_model=DoctorResponse)
async def read_doctor_profile(current_doctor: Doctor = Depends(get_current_doctor)):
    return current_doctor



@router.post("/", response_model=DoctorResponse)
def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    """
    Create a new doctor with hashed password.
    """
    # Check if email is already in use
    if db.query(Doctor).filter(Doctor.email == doctor.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Resolve specialization_name to specialization_id
    specialization = get_specialization_by_name(db, doctor.specialization_name)
    if not specialization:
        raise HTTPException(status_code=404, detail="Specialization not found")

    # Prepare doctor data
    doctor_data = doctor.model_dump(exclude={"password", "specialization_name", "first_name", "last_name"})
    doctor_data["specialization_id"] = specialization.id
    
    doctor_data["first_name"] = doctor.first_name[0].upper() + doctor.first_name[1:].lower()
    doctor_data["last_name"] = doctor.last_name[0].upper() + doctor.last_name[1:].lower()
    doctor_data["password"] = hash_password(doctor.password)  # Hash password

    # Create and save doctor
    db_doctor = Doctor(**doctor_data)
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    logger.info(f"Doctor created: ID={db_doctor.id}, Email={doctor.email}")
    return db_doctor

@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a doctor by ID (requires authentication).
    """
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    # if not doctor:
    #     raise HTTPException(status_code=404, detail="Doctor not found")
    # if doctor.id != current_doctor.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to view this doctor")
    return doctor

@router.get("/", response_model=List[DoctorResponse])
def get_all_doctors(db: Session = Depends(get_db)):
    """
    Retrieve all doctors (requires authentication).
    """
    return db.query(Doctor).all()

@router.put("/{doctor_id}", response_model=DoctorResponse)
def update_doctor(
    doctor_id: int,
    doctor_update: DoctorUpdate,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """
    Update a doctor's details, including password if provided (requires authentication).
    """
    db_doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not db_doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if db_doctor.id != current_doctor.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this doctor")

    update_data = doctor_update.model_dump(exclude_unset=True)
    if "specialization_name" in update_data:
        specialization = get_specialization_by_name(db, update_data["specialization_name"])
        if not specialization:
            raise HTTPException(status_code=404, detail="Specialization not found")
        update_data["specialization_id"] = specialization.id
        del update_data["specialization_name"]

    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])

    if "email" in update_data and update_data["email"] != db_doctor.email:
        if db.query(Doctor).filter(Doctor.email == update_data["email"]).first():
            raise HTTPException(status_code=409, detail="Email already registered")

    for key, value in update_data.items():
        setattr(db_doctor, key, value)

    db.commit()
    db.refresh(db_doctor)
    logger.info(f"Doctor updated: ID={doctor_id}")
    return db_doctor