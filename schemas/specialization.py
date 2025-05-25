from pydantic import BaseModel, Field

class SpecializationBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description='Doctor specialization.')

class SpecializationCreate(SpecializationBase):
    pass

class Specialization(SpecializationBase):
    id: int

    class Config:
        orm_mode = True
