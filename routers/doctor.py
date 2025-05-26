import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.doctor import Doctor
from models.specialization import Specialization
from schemas.doctor import DoctorCreate, DoctorResponse, DoctorUpdate
from utils.helper import get_specialization_by_name, specialization_exists_by_name, hash_password

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/doctors", tags=["doctors"])

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
    doctor_data = doctor.model_dump(exclude={"password", "specialization_name"})
    doctor_data["specialization_id"] = specialization.id
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
    Retrieve a doctor by ID.
    """
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@router.get("/", response_model=List[DoctorResponse])
def get_all_doctors(db: Session = Depends(get_db)):
    """
    Retrieve all doctors.
    """
    return db.query(Doctor).all()

@router.put("/{doctor_id}", response_model=DoctorResponse)
def update_doctor(doctor_id: int, doctor_update: DoctorUpdate, db: Session = Depends(get_db)):
    """
    Update a doctor's details, including password if provided.
    """
    db_doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not db_doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

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