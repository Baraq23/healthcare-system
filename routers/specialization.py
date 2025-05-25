# routers/specializations.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.specialization import Specialization as SpecializationModel
from schemas.specialization import SpecializationCreate as SpecializationCreateSchema
from schemas.specialization import Specialization as SpecializationSchema
from sqlalchemy.exc import IntegrityError




router = APIRouter(
    prefix="/specializations",
    tags=["specializations"]
)

@router.post("/", response_model=SpecializationSchema)
def create_specialization(
    specialization: SpecializationCreateSchema,
    db: Session = Depends(get_db)
):
    # Check for existing specialization
    existing = db.query(SpecializationModel).filter(
        SpecializationModel.name.ilike(specialization.name)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Specialization already exists"
        )
    
    db_spec = SpecializationModel(**specialization.model_dump())
    db.add(db_spec)
    db.commit()
    db.refresh(db_spec)
    return db_spec

@router.get("/", response_model=list[SpecializationSchema])
def get_all_specializations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return db.query(SpecializationModel).offset(skip).limit(limit).all()



@router.get("/{specialization_id}", response_model=SpecializationSchema)
def get_specialization(
    specialization_id: int,
    db: Session = Depends(get_db)
):
    # Find the specialization
    specialization = db.query(SpecializationModel).filter(
        SpecializationModel.id == specialization_id
    ).first()

    if not specialization:
        raise HTTPException(
            status_code=404,
            detail=f"Specialization with id {specialization_id} not found"
        )

    return specialization
