from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from enum import Enum

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class Patient(BaseModel):
    first_name: str = Field(..., min_length=3, max_length=50, description='First name of the patient')
    last_name: str = Field(..., min_length=3, max_length=50, description='Last name of the patient')
    date_of_birth: date = Field(..., description='Patient date of birth')
    gender: Gender = Field(..., description='Patient gender')
    email: EmailStr = Field(..., description='Patient email address')
    phone: str = Field(..., description='Patient phone number')
    address: Optional[str] = None

    @field_validator('gender', mode='before')
    @classmethod
    def normalize_gender(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

class PatientCreate(Patient):
    password: str = Field(..., min_length=8, description='Password for patient account')

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, description='New password for patient account')

class PatientResponse(Patient):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Updated from orm_mode