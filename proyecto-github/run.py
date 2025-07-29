# run.py
import os
from project import create_app

# Obtener la configuración del entorno, por defecto 'dev'
config_name = os.getenv('FLASK_ENV', 'dev')
app = create_app(f'project.config.{config_name.capitalize()}Config')

if __name__ == '__main__':
    app.run()