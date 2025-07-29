# project/models.py
from . import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, Text, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default='user')
    
    # Relación uno-a-muchos con Boleta
    boletas: Mapped[list["Boleta"]] = relationship("Boleta", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
        
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role
        }

class Boleta(db.Model):
    __tablename__ = 'boletas'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha: Mapped[str] = mapped_column(String(10), nullable=False)
    monto_total: Mapped[float] = mapped_column(Float, nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    notas: Mapped[str] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    
    # Relación muchos-a-uno con User
    user: Mapped["User"] = relationship("User", back_populates="boletas")
    
    def to_dict(self):
        return {
            "id": self.id,
            "fecha": self.fecha,
            "monto_total": self.monto_total,
            "categoria": self.categoria,
            "notas": self.notas,
            "user_id": self.user_id
        }