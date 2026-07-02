import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')
    DEBUG = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    TOKEN_MAX_AGE_SECONDS = int(os.environ.get('TOKEN_MAX_AGE_SECONDS', str(60 * 60 * 24)))

    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USER = os.environ.get('EMAIL_USER', 'taskmanager@example.com')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'dev-only-change-me')


settings = Settings()
