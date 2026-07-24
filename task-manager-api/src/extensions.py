"""Extensões do Flask instanciadas sem aplicação — vinculadas no factory (`create_app`)."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
