import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.patient import Patient
from schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from utils.helper import hash_password

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=PatientResponse)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """
    Create a new patient with hashed password.
    """
    # Check if email is already in use
    if db.query(Patient).filter(Patient.email == patient.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Prepare patient data
    patient_data = patient.model_dump(exclude={"password"})
    patient_data["password"] = hash_password(patient.password)  # Hash password

    # Create and save patient
    db_patient = Patient(**patient_data)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    logger.info(f"Patient created: ID={db_patient.id}, Email={patient.email}")
    return db_patient

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a patient by ID.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.get("/", response_model=List[PatientResponse])
def get_all_patients(db: Session = Depends(get_db)):
    """
    Retrieve all patients.
    """
    return db.query(Patient).all()

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: int, patient_update: PatientUpdate, db: Session = Depends(get_db)):
    """
    Update a patient's details, including password if provided.
    """
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")

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