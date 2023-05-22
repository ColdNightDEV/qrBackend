from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy

# from models import SessionDb
# import redis

load_dotenv()

class ApplicationConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///./db.sqlite"

    SESSION_TYPE = "sqlalchemy"
    SESSION_SQLALCHEMY_DB_MODEL = "SessionDb"
    SESSION_PERMANENT = False