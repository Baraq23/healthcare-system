import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.utils.helper import hash_password
from app.auth import authenticate_user, create_access_token, get_current_patient, UserType
from fastapi.security import OAuth2PasswordRequestForm
from dotenv import load_dotenv
import os


load_dotenv()  # Loads variables from a .env file if present

ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])



@router.post("/login")
async def patient_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = form_data.username  # This is the email sent as 'username'
    password = form_data.password

    # Authenticate patient
    user = authenticate_user(db, email, password, UserType.PATIENT)
    print("THIS IS THE USER LOGING IN: ", user)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    # Create token with user_type
    access_token = create_access_token(
        data={"sub": str(user["id"]), "user_type": UserType.PATIENT},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    print("ACCESS TOKENS: ", )
    return {"access_token": access_token, "token_type": "bearer"}




@router.get("/me", response_model=PatientResponse)
async def read_patient_profile(current_patient: Patient = Depends(get_current_patient)):
    return current_patient




@router.post("/", response_model=PatientResponse)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """
    Create a new patient with hashed password.
    """
    # Check if email is already in use
    if db.query(Patient).filter(Patient.email == patient.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Prepare patient data
    patient_data = patient.model_dump(exclude={"password", "last_name", "first_name"})
    patient_data["first_name"] = patient.first_name[0].upper() + patient.first_name[1:].lower()
    patient_data["last_name"] = patient.last_name[0].upper() + patient.last_name[1:].lower()
    patient_data["password"] = hash_password(patient.password)  # Hash password
    

    # Create and save patient
    db_patient = Patient(**patient_data)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    logger.info(f"Patient created: ID={db_patient.id}, Email={patient.email}")
    return db_patient

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db), ):
    """
    Retrieve a patient by ID (requires authentication).
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    # if patient.id != current_patient.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to view this patient")
    return patient

@router.get("/", response_model=List[PatientResponse])
def get_all_patients(db: Session = Depends(get_db), current_patient: Patient = Depends(get_current_patient)):
    """
    Retrieve all patients (requires authentication).
    """
    return db.query(Patient).all()

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db),
    current_patient: Patient = Depends(get_current_patient)
):
    """
    Update a patient's details, including password if provided (requires authentication).
    """
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if db_patient.id != current_patient.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this patient")

    update_data = patient_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])

    if "email" in update_data and update_data["email"] != db_patient.email:
        if db.query(Patient).filter(Patient.email == update_data["email"]).first():
            raise HTTPException(status_code=409, detail="Email already registered")

    for key, value in update_data.items():
        setattr(db_patient, key, value)

    db.commit()
    db.refresh(db_patient)
    logger.info(f"Patient updated: ID={patient_id}")
    return db_patient