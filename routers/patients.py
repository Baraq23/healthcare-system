
# routers/patients.py (absolute imports)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.patient import Patient as PatientModel
from schemas.patient import PatientCreate as PatientCreateSchema
from schemas.patient import Patient as PatientSchema
from sqlalchemy.exc import IntegrityError


router = APIRouter(
    prefix="/patients",
    tags=["patients"]
)

# Create new patient
@router.post(
    "/", 
    status_code=status.HTTP_201_CREATED,
    response_model=PatientSchema
)
def create_patient(
    patient: PatientCreateSchema,
    db: Session = Depends(get_db)
):
    """
    Create a new patient record with:
    - **first_name**: Patient's first name (required)
    - **last_name**: Patient's last name (required)
    - **date_of_birth**: Format YYYY-MM-DD (required)
    - **gender**: Male/Female (required)
    - **email**: Valid email format (required)
    - **phone**: Contact number (required)
    - **address**: Optional address
    """
    try: 
        db_patient = PatientModel(**patient.model_dump())
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient) # autogenerate ID
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
            detail=f"Erro: Missing required fields: ${str(e)}"
        )
    

# Get all patients
@router.get(
    "/", 
    response_model=list[PatientSchema]
)
def get_all_patients(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all patients with optional pagination:
    - **skip**: Number of records to skip (default 0)
    - **limit**: Maximum records to return (default 100)
    """
    patients = db.query(PatientModel).offset(skip).limit(limit).all()
    return patients

# Get single patient by ID
# @router.get(
#     "/{patient_id}", 
#     response_model=schemas.Patient
# )
# def get_patient(
#     patient_id: int, 
#     db: Session = Depends(database.get_db)
# ):
#     """Retrieve a specific patient by their ID"""
#     patient = db.query(models.Patient).filter(
#         models.Patient.id == patient_id
#     ).first()
    
#     if not patient:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Patient with id {patient_id} not found"
#         )
#     return patient

# # Update patient
# @router.put(
#     "/{patient_id}", 
#     response_model=schemas.Patient
# )
# def update_patient(
#     patient_id: int,
#     patient_data: schemas.PatientUpdate,
#     db: Session = Depends(database.get_db)
# ):
#     """
#     Update patient information (partial update supported):
#     - All fields are optional
#     - Only provided fields will be updated
#     """
#     patient_query = db.query(models.Patient).filter(
#         models.Patient.id == patient_id
#     )
#     patient = patient_query.first()

#     if not patient:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Patient with id {patient_id} not found"
#         )

#     update_data = patient_data.dict(exclude_unset=True)
#     patient_query.update(update_data, synchronize_session=False)
#     db.commit()
#     db.refresh(patient)
#     return patient

# # Delete patient
# @router.delete(
#     "/{patient_id}",
#     status_code=status.HTTP_204_NO_CONTENT
# )
# def delete_patient(
#     patient_id: int,
#     db: Session = Depends(database.get_db)
# ):
#     """Delete a patient record by ID"""
#     patient = db.query(models.Patient).filter(
#         models.Patient.id == patient_id
#     ).first()

#     if not patient:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Patient with id {patient_id} not found"
#         )

#     db.delete(patient)
#     db.commit()
#     return