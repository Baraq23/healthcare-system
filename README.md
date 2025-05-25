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




