# run.py
"""Punto de entrada de la aplicación y registro de comandos CLI.

Este script se utiliza para instanciar y ejecutar la aplicación Flask
utilizando el patrón de fábrica de aplicaciones. También define comandos
de terminal personalizados para la gestión de la aplicación, como la
creación de usuarios, facilitando la administración del sistema.
"""
import os
import click
from project import create_app, db
from project.models import User

# Carga la configuración correspondiente ('development' o 'production')
# basada en la variable de entorno FLASK_ENV.
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(f'project.config.{config_name.capitalize()}Config')

# -------------------------------------------------------------------
# --- Comandos Personalizados de la Línea de Comandos (CLI) ---
# -------------------------------------------------------------------

# Define un nuevo comando que se ejecutará con: 'flask create-user'
@app.cli.command("create-user")
# Define el primer argumento obligatorio: 'username'
@click.argument("username")
# Define el segundo argumento obligatorio: 'password'
@click.argument("password")
# Define una opción opcional '--admin'. Si se usa, la variable 'admin' será True.
@click.option("--admin", is_flag=True, help="Otorga privilegios de administrador al usuario.")
def create_user(username, password, admin):
    """Crea un nuevo usuario en la base de datos con un rol específico.

    Args:
        username (str): El nombre de usuario para la nueva cuenta.
        password (str): La contraseña para la nueva cuenta.
        admin (bool): Si es True, el usuario se creará con el rol de 'admin'.
    """
    # 'app_context' es necesario para que los comandos de terminal puedan
    # interactuar correctamente con la aplicación y su base de datos.
    with app.app_context():
        # Se verifica si el usuario ya existe para evitar duplicados.
        user_exists = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        if user_exists:
            print(f"Error: El usuario '{username}' ya existe.")
            return

        # Se crea la nueva instancia del modelo User.
        user = User(username=username)
        user.set_password(password)
        user.generate_api_key()

        # Se asigna el rol basado en si se utilizó el flag --admin.
        if admin:
            user.role = 'admin'
            print(f"Creando administrador: {username}")
        else:
            user.role = 'user'
            print(f"Creando usuario: {username}")

        # Se añade el nuevo usuario a la sesión y se guardan los cambios en la base de datos.
        db.session.add(user)
        db.session.commit()
        print("¡Usuario creado exitosamente!")

# Este bloque permite ejecutar la aplicación directamente con 'python run.py',
# aunque el método estándar en un entorno Flask es usar 'flask run'.
if __name__ == '__main__':
    app.run()