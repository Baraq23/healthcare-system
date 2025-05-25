
# routers/patients.py (absolute imports)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.doctor import Doctor as DoctorModel
from schemas.doctor import DoctorCreate as DoctorCreateSchema
from schemas.doctor import DoctorUpdate as DoctorUpdateSchema
from schemas.doctor import DoctorResponse as DoctorResponseSchema
from sqlalchemy.exc import IntegrityError
from models.specialization import Specialization as SpecializationModel



router = APIRouter(
    prefix="/doctors",
    tags=["doctors"]
)

# Create new doctor
@router.post(
    "/", 
    status_code=status.HTTP_201_CREATED,
    response_model=DoctorResponseSchema
)
def create_doctor(
    doctor: DoctorCreateSchema,
    db: Session = Depends(get_db)
):
    """
    Create a new doctor record with:
    - **first_name**: Doctor's first name (required)
    - **last_name**: Doctor's last name (required)
    - **date_of_birth**: Format YYYY-MM-DD (required)
    - **gender**: Male/Female (required)
    - **specialization_name**: specialty name i.e 'Neurologist'(required)
    - **email**: Valid email format (required)
    - **phone**: Contact number (required)
    - **address**: Optional address
    """
    # Find existing specialization
    spec = db.query(SpecializationModel).filter(
        SpecializationModel.name.ilike(doctor.specialization_name)
    ).first()

    if not spec:
        raise HTTPException(
            status_code=400,
            detail=f"Specialization '{doctor.specialization_name}' not found"
        )
        
        
    try: 
        # Create doctor with existing specialization
        db_doctor = DoctorModel(
            **doctor.model_dump(exclude={"specialization_name"}),
            specialization_id=spec.id
        )
        db.add(db_doctor)
        db.commit()
        db.refresh(db_doctor) # autogenerate ID
        specialization = db.query(SpecializationModel).filter_by(name=doctor.specialization_name).first()
        if not specialization:
            raise HTTPException(status_code=404, detail="Specialization not found")
        return db_doctor
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
            detail=f"Erro: Missing required fields: {str(e)}"
        )
    

# Get all patients
@router.get(
    "/", 
    response_model=list[DoctorResponseSchema]
)
def get_all_doctors(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all doctors with optional pagination:
    - **skip**: Number of records to skip (default 0)
    - **limit**: Maximum records to return (default 100)
    """
    doctors = db.query(DoctorModel).offset(skip).limit(limit).all()
    return doctors

# Get single patient by ID
@router.get(
    "/{doctor_id}", 
    response_model=DoctorResponseSchema
)
def get_doctor(
    doctor_id: int, 
    db: Session = Depends(get_db)
):
    """Retrieve a specific doctor by their ID"""
    doctor = db.query(DoctorModel).filter(
        DoctorModel.id == doctor_id
    ).first()
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with id {doctor_id} not found"
        )
    return doctor

# # Update doctor
@router.put(
    "/{doctor_id}", 
    response_model=DoctorResponseSchema
)
def update_doctor(
    doctor_id: int,
    doctor_data: DoctorUpdateSchema,
    db: Session = Depends(get_db)
):
    """
    Update doctor information (partial update supported):
    - All fields are optional
    - Only provided fields will be updated
    """
    doctor_query = db.query(DoctorModel).filter(
        DoctorModel.id == doctor_id
    )
    doctor = doctor_query.first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with id {doctor_id} not found"
        )

    update_data = doctor_data.model_dump(exclude_unset=True)
    try:
        # Remove specialization_name from update_data (it's handled separately)
        specialization_name = update_data.pop("specialization_name", None)

        # Update other fields directly
        doctor_query.update(update_data, synchronize_session=False)

        # If specialization_name was provided, update the relationship
        if specialization_name:
            specialization_instance = db.query(SpecializationModel).filter_by(
                name=specialization_name
            ).first()
            if not specialization_instance:
                raise HTTPException(status_code=404, detail=f"Specialization '{doctor_data.specialization_name}' not found")
            doctor.specialization = specialization_instance
        db.commit()   
        db.refresh(doctor)
        return doctor
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already exists."
        )


# # Delete doctor
@router.delete(
    "/{doctor_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    """Delete a doctor's record by ID"""
    doctor = db.query(DoctorModel).filter(
        DoctorModel.id == doctor_id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"doctor with id {doctor_id} not found"
        )

    db.delete(doctor)
    db.commit()
    return