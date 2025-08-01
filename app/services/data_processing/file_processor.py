import os
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

class FileProcessor:
    """Servicio para procesar archivos CSV y Excel"""
    
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        
    def allowed_file(self, filename):
        """Verificar si el archivo tiene una extensión permitida"""
        ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    def save_file(self, file, user_id):
        """Guardar archivo subido y generar nombre único"""
        if not file or not self.allowed_file(file.filename):
            raise ValueError("Archivo no válido o extensión no permitida")
        
        # Generar nombre único para evitar conflictos
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Crear carpeta si no existe
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Guardar archivo
        file_path = os.path.join(self.upload_folder, unique_filename)
        file.save(file_path)
        
        return {
            'file_path': file_path,
            'filename': unique_filename,
            'original_filename': filename,
            'file_size': os.path.getsize(file_path)
        }
    
    def analyze_file(self, file_path):
        """Analizar archivo y extraer información básica"""
        try:
            # Determinar tipo de archivo
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Leer archivo según su tipo
            if file_extension == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Tipo de archivo no soportado: {file_extension}")
            
            # Análisis básico
            analysis = {
                'rows_count': len(df),
                'columns_count': len(df.columns),
                'columns_info': self._analyze_columns(df),
                'has_null_values': df.isnull().any().any(),
                'memory_usage': df.memory_usage(deep=True).sum(),
                'data_types': df.dtypes.to_dict(),
                'sample_data': df.head(5).to_dict('records') if len(df) > 0 else []
            }
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Error al analizar archivo: {str(e)}")
    
    def _analyze_columns(self, df):
        """Analizar información detallada de las columnas"""
        columns_info = {}
        
        for column in df.columns:
            col_data = df[column]
            
            # Información básica de la columna
            info = {
                'name': column,
                'data_type': str(col_data.dtype),
                'null_count': int(col_data.isnull().sum()),  # Convertir a int nativo
                'unique_count': int(col_data.nunique()),     # Convertir a int nativo
                'total_count': int(len(col_data))            # Convertir a int nativo
            }
            
            # Análisis específico según el tipo de dato
            if pd.api.types.is_numeric_dtype(col_data):
                # Columna numérica - convertir todos los valores numpy a tipos Python nativos
                info.update({
                    'type_category': 'numeric',
                    'min_value': float(col_data.min()) if not col_data.empty and pd.notna(col_data.min()) else None,
                    'max_value': float(col_data.max()) if not col_data.empty and pd.notna(col_data.max()) else None,
                    'mean_value': float(col_data.mean()) if not col_data.empty and pd.notna(col_data.mean()) else None,
                    'std_value': float(col_data.std()) if not col_data.empty and pd.notna(col_data.std()) else None,
                    'median_value': float(col_data.median()) if not col_data.empty and pd.notna(col_data.median()) else None
                })
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                # Columna de fecha - convertir a string
                info.update({
                    'type_category': 'datetime',
                    'min_date': str(col_data.min()) if not col_data.empty and pd.notna(col_data.min()) else None,
                    'max_date': str(col_data.max()) if not col_data.empty and pd.notna(col_data.max()) else None
                })
            else:
                # Columna de texto
                value_counts = col_data.value_counts().head(3)
                most_common = {str(k): int(v) for k, v in value_counts.items()} if not col_data.empty else {}
                
                info.update({
                    'type_category': 'text',
                    'max_length': int(col_data.astype(str).str.len().max()) if not col_data.empty else 0,
                    'most_common': most_common
                })
            
            columns_info[column] = info
        
        return columns_info
    
    def get_sample_data(self, file_path, n_rows=10):
        """Obtener muestra de datos para preview"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.csv':
                df = pd.read_csv(file_path, nrows=n_rows)
            elif file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, nrows=n_rows)
            else:
                raise ValueError(f"Tipo de archivo no soportado: {file_extension}")
            
            return {
                'columns': df.columns.tolist(),
                'data': df.to_dict('records'),
                'total_preview_rows': len(df)
            }
            
        except Exception as e:
            raise Exception(f"Error al obtener muestra: {str(e)}")
    
    def validate_file_size(self, file, max_size_mb=16):
        """Validar tamaño del archivo"""
        if hasattr(file, 'seek') and hasattr(file, 'tell'):
            # Para archivos en memoria
            file.seek(0, 2)  # Ir al final
            size = file.tell()
            file.seek(0)     # Volver al inicio
        else:
            # Para archivos en disco
            size = os.path.getsize(file) if isinstance(file, str) else 0
        
        size_mb = size / (1024 * 1024)
        
        if size_mb > max_size_mb:
            raise ValueError(f"Archivo demasiado grande: {size_mb:.2f}MB. Máximo permitido: {max_size_mb}MB")
        
        return size_mb