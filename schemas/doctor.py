from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from enum import Enum

from schemas.specialization import Specialization  as SpecializationModel


# validations of gender
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


# Base schema
class DoctorBase(BaseModel):
    first_name: str = Field(..., min_length=3, max_length=50, description='First name of the Doctor')
    last_name: str = Field(..., min_length=3, max_length=50, description='Last name of the Doctor')
    date_of_birth: date = Field(...,  description='Doctor date of birth')
    gender: Gender = Field(...,  description='Doctor gender')
    specialization_name: str = Field(...,  description='Doctor specialization') # Input field
    email: EmailStr = Field(...,  description='Doctor email address')
    phone: str = Field(...,  description='Doctor phone number')
    address: Optional[str] = None

    @field_validator('gender', mode='before')
    @classmethod
    def normalize_gender(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

# Schema for creating new Doctors (POST requests)
class DoctorCreate(DoctorBase):
    pass  # Inherits all fields from DoctorBase

# Schema for updating Doctors (PUT/PATCH requests)
class DoctorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    specialization_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None

# Schema for returning Doctors (GET responses)
class DoctorResponse(BaseModel):
    id: int
    first_name: str 
    last_name: str
    date_of_birth: date 
    gender: Gender 
    specialization: SpecializationModel
    email: EmailStr
    phone: str 
    address: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True  # Allows conversion from SQLAlchemy model