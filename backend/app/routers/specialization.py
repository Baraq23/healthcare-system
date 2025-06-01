from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.specialization import Specialization as SpecializationModel
# from schemas.specialization import SpecializationCreate as SpecializationCreateSchema
from app.schemas.specialization import Specialization as SpecializationSchema
from app.utils.helper import get_specialization_by_id_or_404
from app.models.specialization import Specialization as SpecializationModel
from app.schemas.specialization import Specialization as SpecializationSchema

router = APIRouter(prefix="/specializations", tags=["specializations"])


#CREATE SPCIALIZATION IS PRESERVED FOR ADMINS
# @router.post("/", response_model=SpecializationSchema)
# def create_specialization(
#     specialization: SpecializationCreateSchema,
#     db: Session = Depends(get_db)
# ):
#     """Create a new specialization."""
#     if specialization_exists_by_name(db, specialization.name):
#         raise HTTPException(
#             status_code=400,
#             detail="Specialization already exists"
#         )
#     # capitalize specialization name
#     specialization_data = specialization.model_dump(exclude={"sapecialization_name"})
#     specialization_data["specialization_name"] = specialization.name[0].upper() + specialization.name[1:].lower()
#     db_spec = SpecializationModel(**specialization.model_dump())
#     db.add(db_spec)
#     db.commit()
#     db.refresh(db_spec)
#     return db_spec

@router.get("/", response_model=list[SpecializationSchema])
def get_all_specializations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all specializations with pagination. Adding specialization is reserved for admins"""
    return db.query(SpecializationModel).order_by(SpecializationModel.name.asc()).offset(skip).limit(limit).all()

@router.get("/{specialization_id}", response_model=SpecializationSchema)
def get_specialization(
    specialization_id: int,
    db: Session = Depends(get_db)
):
    """Get a specialization by ID."""
    return get_specialization_by_id_or_404(db, specialization_id)
