from datetime import datetime
from config.database import db

class BaseModel(db.Model):
    """Modelo base con campos comunes"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def save(self):
        """Guardar el objeto en la base de datos"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Eliminar el objeto de la base de datos"""
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        """Convertir el objeto a diccionario"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }