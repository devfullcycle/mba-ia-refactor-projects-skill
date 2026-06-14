import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-in-production")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "loja.db")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
