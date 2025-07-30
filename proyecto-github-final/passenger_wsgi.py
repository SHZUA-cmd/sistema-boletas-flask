# passenger_wsgi.py
"""Punto de entrada para el servidor de producción Phusion Passenger.

Este script es utilizado por servidores web en entornos de hosting compartido (como cPanel)
para iniciar la aplicación Python. Su función principal es encontrar, importar y
exponer la instancia de la aplicación Flask para que el servidor pueda comunicarse con ella.
"""
import os
import sys

# Añade el directorio actual del proyecto al 'sys.path' de Python.
# Esto es un paso crucial para asegurar que el importador de Python pueda
# encontrar los módulos de la aplicación (como la carpeta 'project' y 'run.py').
sys.path.insert(0, os.path.dirname(__file__))

# Importa la variable 'app' desde el script run.py.
# La renombra a 'application', que es el nombre estándar que Phusion Passenger
# busca por defecto para ejecutar la aplicación.
from run import app as application