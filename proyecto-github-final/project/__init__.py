# project/__init__.py
"""Punto de inicialización del paquete de la aplicación.

Este archivo contiene la fábrica de la aplicación ('application factory'), una función
llamada create_app que construye y configura la instancia de la aplicación Flask.
Este patrón permite una mejor organización, facilita las pruebas y evita
problemas de importación circular.
"""
import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# Se crean las instancias de las extensiones de Flask en el ámbito global.
# No se asocian a una aplicación todavía para mantener la modularidad.
db = SQLAlchemy()
jwt = JWTManager() # Se mantiene por si se usa en el futuro, pero no está activo en el sistema de API Key.

def create_app(config_class_name='project.config.DevelopmentConfig'):
    """Construye y configura una instancia de la aplicación Flask.

    Esta función sigue el patrón de "fábrica de aplicaciones", centralizando la
    creación de la app, la carga de configuración, la inicialización de
    extensiones y el registro de rutas (Blueprints).

    Args:
        config_class_name (str): La ruta de importación de la clase de configuración
                                 a utilizar (ej. 'project.config.DevelopmentConfig').

    Returns:
        Flask: La instancia de la aplicación Flask configurada y lista para usarse.
    """
    # Se crea la instancia de Flask. '__name__' le indica a Flask dónde buscar recursos.
    # 'instance_relative_config=True' permite configuraciones en la carpeta /instance.
    # 'static_folder' se define para que Flask sirva los archivos del frontend.
    app = Flask(__name__, instance_relative_config=True, static_folder='static')

    # Carga la configuración desde el objeto Python especificado (definido en config.py).
    app.config.from_object(config_class_name)

    # Se asegura de que la carpeta /instance exista. Flask la usa para archivos
    # que no deben estar en el control de versiones, como la base de datos SQLite.
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Vincula las extensiones (db, CORS) con la instancia de la aplicación.
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # El 'app_context' es necesario para que las extensiones sepan a qué aplicación
    # pertenecen al realizar operaciones como la creación de tablas.
    with app.app_context():
        # Se importan las rutas aquí para evitar importaciones circulares.
        from . import routes
        # Se registra el Blueprint de la API, añadiendo el prefijo '/api' a todas sus rutas.
        app.register_blueprint(routes.api_bp, url_prefix='/api')

        # Crea todas las tablas definidas en los modelos si no existen.
        db.create_all()

    # Define una ruta para la raíz del sitio ('/').
    @app.route('/')
    def serve_index():
        """Sirve el archivo principal del frontend (index.html)."""
        return send_from_directory(app.static_folder, 'index.html')

    # Devuelve la instancia de la aplicación ya creada y configurada.
    return app