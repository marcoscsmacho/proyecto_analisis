from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import db
from app.models.base import BaseModel

class User(BaseModel, UserMixin):
    """Modelo de Usuario con roles"""
    __tablename__ = 'users'
    
    # Campos básicos
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Información personal
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    
    # Rol del usuario
    role = db.Column(db.Enum('admin', 'analista', name='user_roles'), 
                     default='analista', nullable=False)
    
    # Estado del usuario
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relación con proyectos
    projects = db.relationship('Project', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, username, email, password, first_name, last_name, role='analista'):
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
    
    def set_password(self, password):
        """Encriptar y guardar la contraseña"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Verificar si el usuario es administrador"""
        return self.role == 'admin'
    
    def is_analyst(self):
        """Verificar si el usuario es analista"""
        return self.role == 'analista'
    
    @property
    def full_name(self):
        """Nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convertir usuario a diccionario"""
        data = super().to_dict()
        data.update({
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'projects_count': len(self.projects)
        })
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'