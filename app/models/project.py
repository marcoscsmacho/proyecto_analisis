import os
from config.database import db
from app.models.base import BaseModel

class Project(BaseModel):
    """Modelo de Proyecto para manejar archivos CSV/XLS"""
    __tablename__ = 'projects'
    
    # Información básica del proyecto
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Información del archivo
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Tamaño en bytes
    file_type = db.Column(db.String(10))  # csv, xlsx, xls
    
    # Metadatos del análisis
    rows_count = db.Column(db.Integer)
    columns_count = db.Column(db.Integer)
    columns_info = db.Column(db.JSON)  # Información de las columnas
    
    # Estados del proyecto
    status = db.Column(db.Enum('uploaded', 'processing', 'completed', 'error', name='project_status'), 
                       default='uploaded', nullable=False)
    
    # Resultados del análisis
    has_charts = db.Column(db.Boolean, default=False)
    has_statistics = db.Column(db.Boolean, default=False)
    has_report = db.Column(db.Boolean, default=False)
    
    # Archivos generados
    pdf_report_path = db.Column(db.String(500))
    charts_folder = db.Column(db.String(500))
    
    # Relación con usuario
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __init__(self, name, filename, original_filename, file_path, user_id, description=None):
        self.name = name
        self.filename = filename
        self.original_filename = original_filename
        self.file_path = file_path
        self.user_id = user_id
        self.description = description
        
        # Determinar tipo de archivo
        extension = original_filename.rsplit('.', 1)[1].lower()
        self.file_type = extension
        
        # Obtener tamaño del archivo
        if os.path.exists(file_path):
            self.file_size = os.path.getsize(file_path)
    
    @property
    def file_size_mb(self):
        """Tamaño del archivo en MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def update_analysis_info(self, rows_count, columns_count, columns_info):
        """Actualizar información del análisis"""
        self.rows_count = rows_count
        self.columns_count = columns_count
        self.columns_info = columns_info
        self.status = 'completed'
        db.session.commit()
    
    def mark_charts_generated(self, charts_folder):
        """Marcar que se generaron las gráficas"""
        self.has_charts = True
        self.charts_folder = charts_folder
        db.session.commit()
    
    def mark_statistics_generated(self):
        """Marcar que se generaron las estadísticas"""
        self.has_statistics = True
        db.session.commit()
    
    def mark_report_generated(self, pdf_path):
        """Marcar que se generó el reporte PDF"""
        self.has_report = True
        self.pdf_report_path = pdf_path
        db.session.commit()
    
    def delete_files(self):
        """Eliminar archivos asociados al proyecto"""
        # Eliminar archivo original
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        
        # Eliminar reporte PDF
        if self.pdf_report_path and os.path.exists(self.pdf_report_path):
            os.remove(self.pdf_report_path)
        
        # Eliminar carpeta de gráficas
        if self.charts_folder and os.path.exists(self.charts_folder):
            import shutil
            shutil.rmtree(self.charts_folder)
    
    def to_dict(self):
        """Convertir proyecto a diccionario"""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size_mb': self.file_size_mb,
            'file_type': self.file_type,
            'rows_count': self.rows_count,
            'columns_count': self.columns_count,
            'status': self.status,
            'has_charts': self.has_charts,
            'has_statistics': self.has_statistics,
            'has_report': self.has_report,
            'owner': self.owner.full_name if self.owner else None
        })
        return data
    
    def __repr__(self):
        return f'<Project {self.name}>'