from dotenv import load_dotenv
import os
import redis

load_dotenv()

class ApplicationConfig:
    SECRET_KEY = os.environ["SECRET_KEY"]
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = r"sqlite:///./db.sqlite"
    
    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_DOMAIN = ".onrender.com"
    
    # SESSION_REDIS = redis.from_url("redis://127.0.0.1:6379")
    REDIS_URL = "redis://red-chibjq3hp8u7g2fcfm6g:6379"
    SESSION_REDIS = redis.from_url(REDIS_URL)
