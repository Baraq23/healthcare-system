from fastapi import FastAPI, Depends
from database import Base, engine, SessionLocal
from routers import patient, doctor, specialization, appointment
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer
from auth import get_current_doctor, get_current_patient
from schemas.doctor import DoctorResponse
from schemas.patient import PatientResponse
from models.specialization import Specialization
from contextlib import asynccontextmanager


specializations_list = [
    "Dermatology", "Neurology", "Cardiology", "Pediatrics", "Oncology",
    "Psychiatry", "Radiology", "Surgery", "Urology", "Orthopedics",
    "Gynecology", "Ophthalmology", "Gastroenterology", "Nephrology",
    "Hematology", "Endocrinology", "Rheumatology", "Pulmonology",
    "Anesthesiology", "Pathology", "Immunology", "Allergy", "Genetics",
    "Microbiology", "Toxicology"
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully!")

        # Insert specializations if not exist
        db = SessionLocal()
        try:
            for name in specializations_list:
                exists = db.query(Specialization).filter_by(name=name).first()
                if not exists:
                    spec_instance = Specialization(name=name)
                    db.add(spec_instance)
            db.commit()
            print("Specializations inserted/verified successfully!")
        except Exception as e:
            db.rollback()
            print(f"Error inserting specializations: {e}")
        finally:
            db.close()

        yield  # <-- This is required!

    except Exception as e:
        print(f"Error creating tables or inserting specializations: {e}")

# Create FastAPI app with lifespan handler
app = FastAPI(lifespan=lifespan)

# OAuth2 schemes
oauth2_doctor_scheme = OAuth2PasswordBearer(
    tokenUrl="/doctors/login",
    scheme_name="OAuth2Doctor"
)
oauth2_patient_scheme = OAuth2PasswordBearer(
    tokenUrl="/patients/login",
    scheme_name="OAuth2Patient"
)

# CORS middleware
origins = [
    "http://0.0.0.0:5000",
    "http://localhost:5000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
def read_root():
    return {"details": "Welcome to healthcare fast api..."}

@app.get("/doctors/me", response_model=DoctorResponse)
async def read_doctor_me(current_doctor: dict = Depends(get_current_doctor)):
    return current_doctor

@app.get("/patients/me", response_model=PatientResponse)
async def read_patient_me(current_patient: dict = Depends(get_current_patient)):
    return current_patient

# Routers
app.include_router(patient.router)
app.include_router(doctor.router)
app.include_router(specialization.router)
app.include_router(appointment.router)

# Custom OpenAPI
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

app.openapi = custom_openapi
