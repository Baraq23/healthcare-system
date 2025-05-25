from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from enum import Enum



# validations classes
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    






# Base schema
class DoctorBase(BaseModel):
    first_name: str = Field(..., min_length=3, max_length=50, description='First name of the Doctor')
    last_name: str = Field(..., min_length=3, max_length=50, description='Last name of the Doctor')
    date_of_birth: date = Field(...,  description='Doctor date of birth')
    gender: Gender = Field(...,  description='Doctor gender')
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
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None

# Schema for returning Doctors (GET responses)
class Doctor(DoctorBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True  # Allows conversion from SQLAlchemy model