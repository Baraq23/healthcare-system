# Heathcare System FastAPI Project

## Overview

This project is a healthcare appointment scheduling system. It focuses on designing and implementing a robust, secure backend service that manages patients and enables them to schedule appointments with doctors.

The backend is built using Python FastAPI for the API framework, ORM-Alchemy for data modeling and database interactions, and MySQL as the database.

## Project Structure:

    healthcare-system/
    ├── venv/                 # Virtual environment
    ├── routers/              # API endpoints
    ├── models/               # Database models
    ├── schemas/              # Pydantic schemas
    ├── main.py               # FastAPI app instance
    ├── database.py           # DB connection
    ├── requirements.txt      # Dependencies
    ├── .env                  # Environment variables
    ├── .gitignore            # Ignore rules
    └── README.md             # Project Documentation


### List of Packages to Download in your environment


- `FastAPI`: high-performance web framework for building APIs with Python

```bash
    pip install fastapi uvicorn[standard]
```

 - `Uvicorn`: an ASGI (Asynchronous Server Gateway Interface) web server for Python.
 ```bash
    pip install 'uvicorn[standard]'
```


- `SQLAlchemy`: ORM (Object Relational Mapper) and SQL toolkit for Python (Object Relational Mapper)

```bash
    pip install sqlalchemy
```

- `PyMySQL`: pure-Python MySQL client library allowing Python to connect to MySQL databases

```bash
    pip install pymysql
```



## API Endpoints


### Patiens

- **POST /patients**: Create a new patient.
- **GET /patients**: Get all patients.
- **GET /patients/{id}**: Get a specific patient by ID.
- **PUT /patients/{id}**: Update a patient's record.
- **DELETE /patients/{id}**: Delete a patient's record.

### Doctors

- **POST /doctors**: Create a new doctor.
- **GET /doctors**: Get all doctors.
- **GET /doctors/{id}**: Get a specific doctor by ID.
- **PUT /doctors/{id}**: Update a doctor's record.
- **DELETE /doctors/{id}**: Delete a doctor's record.

### Specializations

- **POST /specializations**: Create a new specialization.
- **GET /specializations**: Get all specializations.
- **GET /specializations/{id}**: Get a specific specialization by ID.

### Appointments

- **POST /appointments**: Create a new appointment.
- **GET /appointments**: Get all appointments.
- **GET /appointments/{appointment_id}**: Get a specific appointment by ID.
- **GET /appointments/doctors/{doctor_id}**: Get records of appointments linked to a doctor.
- **GET /appointments/patient/{patient_id}**: Get records of appointments linked to a patient.
- **GET /appointments/availability/{doctor_id}**: Get a list of available time slots for a doctor with specific a ID.







## Future improvements:

- Incorporate different hospitals to the system so that doctors can attend to patients in different hospitals that offer facilities and equipment in their field of specialization.
