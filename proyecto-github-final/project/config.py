# project/config.py
"""Configuraciones de la aplicación Flask para diferentes entornos.

Este archivo define clases de configuración para separar los ajustes de desarrollo,
producción y cualquier otro entorno. El uso de variables de entorno permite
configurar la aplicación de forma segura sin tener que modificar el código.
"""
import os

class Config:
    """Configuración base que contiene los ajustes comunes para todos los entornos."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') 
    
    # Desactiva una función de Flask-SQLAlchemy que emite señales de eventos.
    # Se recomienda desactivarla para reducir el consumo de memoria.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Define la ruta a la carpeta donde se guardarán las imágenes subidas.
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'uploads')

class DevelopmentConfig(Config):
    """Configuración específica para el entorno de desarrollo local."""
    
    # Activa el modo de depuración de Flask.
    # Esto habilita el recargador automático y un depurador interactivo en el navegador.
    DEBUG = True
    
    # Define la cadena de conexión a la base de datos.
    # Intenta leerla de una variable de entorno, pero si no existe,
    # usa una base de datos SQLite local en la carpeta /instance.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'project.db')

class ProductionConfig(Config):
    """Configuración para el entorno de producción (servidor en vivo)."""
    
    # El modo de depuración NUNCA debe estar activo en producción por razones de seguridad.
    DEBUG = False
    
    # En producción, la cadena de conexión a la base de datos (ej. PostgreSQL o MySQL)
    # DEBE ser proporcionada a través de una variable de entorno.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')