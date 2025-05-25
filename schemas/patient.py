from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from enum import Enum



# validations classes
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    






# Base schema
class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=3, max_length=50, description='First name of the patient')
    last_name: str = Field(..., min_length=3, max_length=50, description='Last name of the patient')
    date_of_birth: date = Field(...,  description='Patient date of birth')
    gender: Gender = Field(...,  description='Patient gender')
    email: EmailStr = Field(...,  description='Patient email address')
    phone: str = Field(...,  description='Patient phone number')
    address: Optional[str] = None

    @field_validator('gender', mode='before')
    @classmethod
    def normalize_gender(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

# Schema for creating new patients (POST requests)
class PatientCreate(PatientBase):
    pass  # Inherits all fields from PatientBase

# Schema for updating patients (PUT/PATCH requests)
class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None

# Schema for returning patients (GET responses)
class Patient(PatientBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True  # Allows conversion from SQLAlchemy model