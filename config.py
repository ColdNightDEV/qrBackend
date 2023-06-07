from dotenv import load_dotenv
import os
import redis

load_dotenv()


class ApplicationConfig:

    # redis_client = redis.Redis()

    SECRET_KEY = "my_secret_key_123"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = r"sqlite:///./db.sqlite"

    SESSION_TYPE = 'redis'
    REDIS_URL = "redis://red-chibjq3hp8u7g2fcfm6g:6379"
    SESSION_REDIS = redis.from_url(REDIS_URL)
    # SESSION_REDIS = redis_client
    # JWT_ACCESS_TOKEN_EXPIRES = 10
    # JWT_SECRET_KEY = "your-secret-key_for_me"

#     from dotenv import load_dotenv
# import os
# import redis

# load_dotenv()

# class ApplicationConfig:

#     redis_client = redis.Redis()

#     SECRET_KEY = "my_secret_key_123"
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     SQLALCHEMY_ECHO = True
#     SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1234@localhost:5432/postgres'
#     SESSION_TYPE = 'redis'
#     SESSION_REDIS = redis_client
