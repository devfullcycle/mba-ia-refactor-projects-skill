import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', '5000'))
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-dev-only-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv('JWT_TOKEN_EXPIRES_HOURS', '24'))
    )
