# project/models.py
"""Define los modelos de la base de datos para la aplicación.

Este archivo contiene las clases que representan las tablas de la base de datos
utilizando el ORM de SQLAlchemy. Cada clase corresponde a una tabla y sus
atributos a las columnas de esa tabla.
"""
import secrets
from . import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey, Boolean
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """Representa a un usuario en la base de datos."""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default='user')
    api_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=True)
    
    # Define la relación uno-a-muchos: un usuario puede tener muchas boletas.
    # 'cascade="all, delete-orphan"' asegura que si un usuario es eliminado,
    # todas sus boletas asociadas también se eliminen.
    boletas: Mapped[list["Boleta"]] = relationship("Boleta", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password: str):
        """Genera un hash seguro para la contraseña y lo almacena."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verifica si la contraseña proporcionada coincide con el hash almacenado."""
        return check_password_hash(self.password_hash, password)
    
    def generate_api_key(self):
        """Genera una clave de API única y segura para la autenticación sin estado."""
        self.api_key = secrets.token_hex(32)

class Categoria(db.Model):
    """Representa una categoría de gasto en la base de datos."""
    __tablename__ = 'categorias'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Relación inversa para saber qué boletas usan esta categoría.
    boletas: Mapped[list["Boleta"]] = relationship("Boleta", back_populates="categoria")

    def to_dict(self):
        """Devuelve una representación de la categoría en formato de diccionario."""
        return {"id": self.id, "nombre": self.nombre}

class Boleta(db.Model):
    """Representa una boleta o recibo de gasto en la base de datos."""
    __tablename__ = 'boletas'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha: Mapped[str] = mapped_column(String(10), nullable=False)
    monto_total: Mapped[int] = mapped_column(Integer, nullable=False)
    notas: Mapped[str] = mapped_column(Text, nullable=True)
    razon_modificacion: Mapped[str] = mapped_column(String(50), nullable=True)
    imagen_url: Mapped[str] = mapped_column(String(512), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Claves foráneas que conectan la boleta con un usuario y una categoría.
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    categoria_id: Mapped[int] = mapped_column(ForeignKey('categorias.id'), nullable=False)
    
    # Relaciones inversas (muchos-a-uno).
    # Permiten acceder a los objetos completos (ej. boleta.categoria o boleta.user).
    categoria: Mapped["Categoria"] = relationship("Categoria", back_populates="boletas")
    user: Mapped["User"] = relationship("User", back_populates="boletas")

    def to_dict(self):
        """Devuelve una representación de la boleta en formato de diccionario.
        
        Es útil para serializar el objeto a JSON y enviarlo a través de la API.
        Incluye datos de las tablas relacionadas, como el nombre de la categoría y del creador.
        """
        return {
            "id": self.id,
            "fecha": self.fecha,
            "monto_total": self.monto_total,
            "categoria": self.categoria.nombre,
            "notas": self.notas,
            "user_id": self.user_id,
            "creador": self.user.username,
            "razon_modificacion": self.razon_modificacion,
            "imagen_url": self.imagen_url,
            "is_deleted": self.is_deleted
        }