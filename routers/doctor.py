from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.doctor import Doctor as DoctorModel
from schemas.doctor import DoctorCreate as DoctorCreateSchema
from schemas.doctor import DoctorUpdate as DoctorUpdateSchema
from schemas.doctor import DoctorResponse as DoctorResponseSchema
from sqlalchemy.exc import IntegrityError
from models.specialization import Specialization as SpecializationModel
from utils.helpers import (
    doctor_exists, get_doctor_by_id,
    patient_exists, get_patient_by_id,
    get_specialization_by_name
)


router = APIRouter(prefix="/doctors", tags=["doctors"])

def get_specialization_by_name(db: Session, name: str):
    spec = db.query(SpecializationModel).filter(SpecializationModel.name.ilike(name)).first()
    if not spec:
        raise HTTPException(status_code=404, detail=f"Specialization '{name}' not found")
    return spec

# ----------------------------
# Routes
# ----------------------------

# Create new doctor
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DoctorResponseSchema)
def create_doctor(doctor: DoctorCreateSchema, db: Session = Depends(get_db)):
    """
    Create a new doctor.
    Required fields: first_name, last_name, date_of_birth, gender, specialization_name, email, phone
    Optional: address
    """
    spec = get_specialization_by_name(db, doctor.specialization_name)
    try:
        db_doctor = DoctorModel(
            **doctor.model_dump(exclude={"specialization_name"}),
            specialization_id=spec.id
        )
        db.add(db_doctor)
        db.commit()
        db.refresh(db_doctor)
        return db_doctor
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

# Get all doctors
@router.get("/", response_model=list[DoctorResponseSchema])
def get_all_doctors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all doctors with pagination.
    - skip: Number of records to skip (default 0)
    - limit: Maximum records to return (default 100)
    """
    doctors = db.query(DoctorModel).offset(skip).limit(limit).all()
    return doctors

# Get single doctor by ID
@router.get("/{doctor_id}", response_model=DoctorResponseSchema)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific doctor by ID"""
    doctor = get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor with id {doctor_id} not found")
    return doctor

# Update doctor
@router.put("/{doctor_id}", response_model=DoctorResponseSchema)
def update_doctor(
    doctor_id: int,
    doctor_data: DoctorUpdateSchema,
    db: Session = Depends(get_db)
):
    """
    Update doctor information (partial update supported).
    Only provided fields will be updated.
    """
    if not doctor_exists(db, doctor_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor with id {doctor_id} not found")

    doctor = get_doctor_by_id(db, doctor_id)
    update_data = doctor_data.model_dump(exclude_unset=True)
    try:
        # Handle specialization_name separately
        specialization_name = update_data.pop("specialization_name", None)
        for key, value in update_data.items():
            setattr(doctor, key, value)

        if specialization_name:
            spec = get_specialization_by_name(db, specialization_name)
            doctor.specialization = spec

        db.commit()
        db.refresh(doctor)
        return doctor
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists.")

# Delete doctor
@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Delete a doctor by ID"""
    doctor = get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor with id {doctor_id} not found")
    db.delete(doctor)
    db.commit()
    return
