#!/bin/bash

# Create a virtual environment in the current directory
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install the required packages
pip install 'fastapi[standard]'
pip install 'uvicorn[standard]'
pip install sqlalchemy
pip install pymysql
pip install redis
pip install 'passlib[bcrypt]'
pip install python-jose[cryptography] fastapi-security
pip install -U pydantic


echo "Virtual environment setup complete! Use 'source venv/bin/activate' to activate it."
