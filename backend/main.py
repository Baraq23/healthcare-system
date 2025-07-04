from fastapi import FastAPI, Depends
from app.database import Base, engine  
from app.routers import patient, doctor, specialization, appointment
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer
from app.auth import get_current_doctor, get_current_patient
from app.schemas.doctor import DoctorResponse
from app.schemas.patient import PatientResponse
from app.populate_db.specializations_table import insert_specializations



# Creating tables before creating FastAPI app
try:
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")
    insert_specializations()

except Exception as e:
    print(f"Error creating tables: {e}")




# creating FastAPI app instance
app = FastAPI()

oauth2_doctor_scheme = OAuth2PasswordBearer(
    tokenUrl="/doctors/login",
    scheme_name="OAuth2Doctor"
)
oauth2_patient_scheme = OAuth2PasswordBearer(
    tokenUrl="/patients/login",
    scheme_name="OAuth2Patient"
)


@app.get("/doctors/me", response_model=DoctorResponse)
async def read_doctor_me(current_doctor: dict = Depends(get_current_doctor)):
    return current_doctor


@app.get("/patients/me", response_model=PatientResponse)
async def read_patient_me(current_patient: dict = Depends(get_current_patient)):
    return current_patient


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="API with two OAuth2 flows",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2Doctor": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/doctors/login",
                    "scopes": {}
                }
            }
        },
        "OAuth2Patient": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/patients/login",
                    "scopes": {}
                }
            }
        }
    }
    # Assign security to routes
    for path in openapi_schema["paths"]:
        if path.startswith("/doctors"):
            for method in openapi_schema["paths"][path]:
                openapi_schema["paths"][path][method]["security"] = [{"OAuth2Doctor": []}]
        elif path.startswith("/patients"):
            for method in openapi_schema["paths"][path]:
                openapi_schema["paths"][path][method]["security"] = [{"OAuth2Patient": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Configure CORS
origins = [
    "http://0.0.0.0:5000", 
    "http://localhost:5000", 
    "https://bookyourdoctor.netlify.app/", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(patient.router)
app.include_router(doctor.router)
app.include_router(specialization.router)
app.include_router(appointment.router)

@app.get("/")
def read_root():
    return {"details": "Welcome to healthcare fast api..."}

