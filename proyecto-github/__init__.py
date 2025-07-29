# project/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# Inicializar extensiones sin vincularlas a una app
db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_class_name='project.config.DevelopmentConfig'):
    """
    Fábrica de la aplicación Flask.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Cargar configuración desde un objeto
    app.config.from_object(config_class_name)

    # Asegurarse de que la carpeta de instancia exista
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Inicializar extensiones con la app
    db.init_app(app)
    jwt.init_app(app)
    
    # Configurar CORS para permitir solicitudes del frontend
    # En producción, esto debería restringirse al dominio del frontend
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    with app.app_context():
        # Importar y registrar Blueprints (rutas)
        from. import routes
        app.register_blueprint(routes.api_bp, url_prefix='/api')

        # Crear todas las tablas de la base de datos
        db.create_all()

    return app