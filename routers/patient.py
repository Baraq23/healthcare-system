from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from database import get_db
from utils.helpers import patient_exists, get_patient_by_id
from models.patient import Patient as PatientModel
from schemas.patient import (
    Patient as PatientSchema,
    PatientCreate as PatientCreateSchema,
    PatientUpdate as PatientUpdateSchema    
)


router = APIRouter(prefix="/patients", tags=["patients"])

# Create new patient
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PatientSchema)
def create_patient(patient: PatientCreateSchema, db: Session = Depends(get_db)):
    """
    Create a new patient record.
    Required fields: first_name, last_name, date_of_birth, gender, email, phone
    Optional: address
    """
    try:
        db_patient = PatientModel(**patient.model_dump())
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        return db_patient
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already exists."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error: {str(e)}"
        )

# Get all patients
@router.get("/", response_model=List[PatientSchema])
def get_all_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all patients with pagination.
    - skip: Number of records to skip (default 0)
    - limit: Maximum records to return (default 100)
    """
    patients = db.query(PatientModel).offset(skip).limit(limit).all()
    return patients

# Get single patient by ID
@router.get("/{patient_id}", response_model=PatientSchema)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific patient by ID"""
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with id {patient_id} not found"
        )
    return patient

# Update patient
@router.put("/{patient_id}", response_model=PatientSchema)
def update_patient(
    patient_id: int,
    patient_data: PatientUpdateSchema,
    db: Session = Depends(get_db)
):
    """
    Update patient information (partial update supported).
    Only provided fields will be updated.
    """
    if not patient_exists(db, patient_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with id {patient_id} not found"
        )

    patient = get_patient_by_id(db, patient_id)
    update_data = patient_data.model_dump(exclude_unset=True)
    try:
        for key, value in update_data.items():
            setattr(patient, key, value)
        db.commit()
        db.refresh(patient)
        return patient
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already exists."
        )

# Delete patient
@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    """Delete a patient by ID"""
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with id {patient_id} not found"
        )
    db.delete(patient)
    db.commit()
    return
