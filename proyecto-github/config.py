# project/config.py
import os
from datetime import timedelta

class Config:
    """Configuración base."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-clave-secreta-por-defecto'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

class DevelopmentConfig(Config):
    """Configuración de desarrollo."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'project.db')

class ProductionConfig(Config):
    """Configuración de producción."""
    DEBUG = False
    # La URI de la base de datos debe ser proporcionada a través de una variable de entorno
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')

# Mapeo de nombres de configuración a clases
config_by_name = dict(
    dev=DevelopmentConfig,
    prod=ProductionConfig
)