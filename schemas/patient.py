from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

# Base schema
class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=3, max_length=25, description='First name of the patient')
    last_name: str = Field(..., min_length=3, max_length=25, description='Last name of the patient')
    date_of_birth: datetime = Field(...,  description='Patient date of birth')
    gender: str = Field(...,  description='Patient date gender')
    email: EmailStr = Field(None,  description='Patient email address')
    phone: str = Field(...,  description='Patient phone number')
    address: str | None = None

# Schema for creating new patients (POST requests)
class PatientCreate(PatientBase):
    pass  # Inherits all fields from PatientBase

# Schema for updating patients (PUT/PATCH requests)
class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None

# Schema for returning patients (GET responses)
class Patient(PatientBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True  # Allows conversion from SQLAlchemy model