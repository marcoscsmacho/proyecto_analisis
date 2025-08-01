import os
import pandas as pd

# Configurar matplotlib ANTES de importar pyplot
import matplotlib
matplotlib.use('Agg')  # Usar backend sin GUI para aplicaciones web

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from wordcloud import WordCloud
import json
import base64
from io import BytesIO
import numpy as np

class ChartService:
    """Servicio para generar gráficas automáticas"""
    
    def __init__(self, project):
        self.project = project
        self.df = None
        self.charts_data = {}
        
    def load_data(self):
        """Cargar datos del archivo del proyecto"""
        try:
            file_extension = os.path.splitext(self.project.file_path)[1].lower()
            
            if file_extension == '.csv':
                # Intentar diferentes encodings para CSV
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        self.df = pd.read_csv(self.project.file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("No se pudo leer el archivo CSV con ningún encoding común")
                    
            elif file_extension in ['.xlsx', '.xls']:
                self.df = pd.read_excel(self.project.file_path)
            else:
                raise ValueError(f"Tipo de archivo no soportado: {file_extension}")
                
            return True
        except Exception as e:
            raise Exception(f"Error al cargar datos: {str(e)}")
    
    def generate_all_charts(self):
        """Generar todas las gráficas automáticamente"""
        if not self.load_data():
            return None
            
        charts = {}
        
        try:
            # 1. Gráfica de barras
            charts['bar_chart'] = self.generate_bar_chart()
            
            # 2. Mapa de calor (heatmap)
            charts['heatmap'] = self.generate_heatmap()
            
            # 3. Gráfica de dispersión
            charts['scatter_plot'] = self.generate_scatter_plot()
            
            # 4. Nube de palabras
            charts['wordcloud'] = self.generate_wordcloud()
            
            # 5. Estadísticas descriptivas
            charts['statistics'] = self.generate_statistics()
            
            self.charts_data = charts
            return charts
            
        except Exception as e:
            raise Exception(f"Error al generar gráficas: {str(e)}")
    
    def generate_bar_chart(self):
        """Generar gráfica de barras con matplotlib"""
        categorical_cols = [col for col, info in self.project.columns_info.items() 
                           if info['type_category'] == 'text' and info['unique_count'] < 20]
        
        if not categorical_cols:
            return self._create_placeholder_chart("No hay columnas categóricas adecuadas para gráfica de barras")
        
        # Tomar la primera columna categórica
        col = categorical_cols[0]
        value_counts = self.df[col].value_counts().head(10)
        
        # Crear gráfica con matplotlib (configurado para web)
        plt.figure(figsize=(10, 6))
        plt.style.use('default')  # Usar estilo por defecto
        
        bars = plt.bar(range(len(value_counts)), value_counts.values, color='skyblue')
        plt.title(f'Distribución de {col}', fontsize=16, fontweight='bold')
        plt.xlabel(col, fontsize=12)
        plt.ylabel('Frecuencia', fontsize=12)
        plt.xticks(range(len(value_counts)), value_counts.index, rotation=45, ha='right')
        
        # Agregar valores en las barras
        for bar, value in zip(bars, value_counts.values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(value), ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Convertir a base64
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='PNG', dpi=150, bbox_inches='tight')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()  # IMPORTANTE: Cerrar la figura para liberar memoria
        
        return {
            'type': 'bar_chart',
            'title': f'Gráfica de Barras - {col}',
            'image_base64': img_str,
            'column': col,
            'description': f'Distribución de frecuencias para la columna {col}'
        }
    
    def generate_heatmap(self):
        """Generar mapa de calor con matplotlib/seaborn"""
        numeric_cols = [col for col, info in self.project.columns_info.items() 
                       if info['type_category'] == 'numeric']
        
        if len(numeric_cols) < 2:
            return self._create_placeholder_chart("Se necesitan al menos 2 columnas numéricas para el mapa de calor")
        
        # Calcular matriz de correlación
        correlation_matrix = self.df[numeric_cols].corr()
        
        # Crear heatmap con seaborn
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='RdBu', center=0, 
                   square=True, fmt='.2f', cbar_kws={'shrink': 0.8})
        plt.title('Mapa de Calor - Correlaciones entre Variables Numéricas', 
                 fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Convertir a base64
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='PNG', dpi=150, bbox_inches='tight')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()  # IMPORTANTE: Cerrar la figura
        
        return {
            'type': 'heatmap',
            'title': 'Mapa de Calor - Correlaciones',
            'image_base64': img_str,
            'columns': numeric_cols,
            'description': f'Correlaciones entre {len(numeric_cols)} variables numéricas'
        }
    
    def generate_scatter_plot(self):
        """Generar gráfica de dispersión con matplotlib"""
        numeric_cols = [col for col, info in self.project.columns_info.items() 
                       if info['type_category'] == 'numeric']
        
        if len(numeric_cols) < 2:
            return self._create_placeholder_chart("Se necesitan al menos 2 columnas numéricas para la gráfica de dispersión")
        
        # Tomar las dos primeras columnas numéricas
        x_col, y_col = numeric_cols[0], numeric_cols[1]
        
        # Limpiar datos (remover NaN)
        clean_data = self.df[[x_col, y_col]].dropna()
        
        if len(clean_data) == 0:
            return self._create_placeholder_chart("No hay datos válidos para la gráfica de dispersión")
        
        # Crear scatter plot con matplotlib
        plt.figure(figsize=(10, 6))
        plt.scatter(clean_data[x_col], clean_data[y_col], alpha=0.6, color='blue')
        
        # Agregar línea de tendencia si hay suficientes datos
        if len(clean_data) > 1:
            z = np.polyfit(clean_data[x_col], clean_data[y_col], 1)
            p = np.poly1d(z)
            plt.plot(clean_data[x_col], p(clean_data[x_col]), "r--", alpha=0.8)
        
        plt.title(f'Gráfica de Dispersión: {x_col} vs {y_col}', fontsize=16, fontweight='bold')
        plt.xlabel(x_col, fontsize=12)
        plt.ylabel(y_col, fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convertir a base64
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='PNG', dpi=150, bbox_inches='tight')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()  # IMPORTANTE: Cerrar la figura
        
        return {
            'type': 'scatter_plot',
            'title': f'Dispersión - {x_col} vs {y_col}',
            'image_base64': img_str,
            'x_column': x_col,
            'y_column': y_col,
            'description': f'Relación entre {x_col} y {y_col} con línea de tendencia'
        }
    
    def generate_wordcloud(self):
        """Generar nube de palabras"""
        text_cols = [col for col, info in self.project.columns_info.items() 
                    if info['type_category'] == 'text']
        
        if not text_cols:
            return self._create_placeholder_chart("No hay columnas de texto para generar nube de palabras")
        
        # Combinar todo el texto de las columnas de texto
        all_text = ""
        for col in text_cols:
            text_data = self.df[col].dropna().astype(str)
            all_text += " ".join(text_data.values)
        
        if len(all_text.strip()) == 0:
            return self._create_placeholder_chart("No hay suficiente texto para generar nube de palabras")
        
        # Generar WordCloud
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='viridis',
            max_words=100
        ).generate(all_text)
        
        # Convertir a imagen base64
        img_buffer = BytesIO()
        wordcloud.to_image().save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return {
            'type': 'wordcloud',
            'title': 'Nube de Palabras',
            'image_base64': img_str,
            'columns': text_cols,
            'description': f'Nube de palabras generada desde {len(text_cols)} columna(s) de texto'
        }
    
    def _safe_float(self, value):
        """Convertir valor a float seguro, reemplazando NaN/inf con None"""
        if pd.isna(value) or np.isinf(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def generate_statistics(self):
        """Generar estadísticas descriptivas"""
        numeric_cols = [col for col, info in self.project.columns_info.items() 
                       if info['type_category'] == 'numeric']
        
        if not numeric_cols:
            return {
                'type': 'statistics',
                'title': 'Estadísticas Descriptivas',
                'data': None,
                'description': 'No hay columnas numéricas para calcular estadísticas'
            }
        
        stats_data = {}
        
        for col in numeric_cols:
            series = self.df[col].dropna()
            
            # Verificar que hay datos suficientes
            if len(series) == 0:
                continue
                
            try:
                # Calcular estadísticas básicas de forma segura
                mode_value = None
                if not series.mode().empty:
                    mode_value = self._safe_float(series.mode().iloc[0])
                
                stats_data[col] = {
                    'count': int(len(series)),
                    'mean': self._safe_float(series.mean()),
                    'median': self._safe_float(series.median()),
                    'mode': mode_value,
                    'std': self._safe_float(series.std()),
                    'var': self._safe_float(series.var()),
                    'min': self._safe_float(series.min()),
                    'max': self._safe_float(series.max()),
                    'q25': self._safe_float(series.quantile(0.25)),
                    'q75': self._safe_float(series.quantile(0.75)),
                    'skewness': self._safe_float(series.skew()) if len(series) > 1 else None,
                    'kurtosis': self._safe_float(series.kurtosis()) if len(series) > 1 else None
                }
            except Exception as e:
                # Si hay error calculando estadísticas para esta columna, saltarla
                print(f"Error calculando estadísticas para {col}: {e}")
                continue
        
        return {
            'type': 'statistics',
            'title': 'Estadísticas Descriptivas',
            'data': stats_data,
            'columns': list(stats_data.keys()),
            'description': f'Medidas de tendencia central y dispersión para {len(stats_data)} variables'
        }
    
    def _create_placeholder_chart(self, message):
        """Crear gráfica placeholder cuando no se puede generar"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title="Gráfica no disponible",
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        return {
            'type': 'placeholder',
            'title': 'No disponible',
            'html': fig.to_html(include_plotlyjs='inline', div_id=f"placeholder_{self.project.id}"),
            'description': message
        }
    
    def get_charts_summary(self):
        """Obtener resumen de las gráficas generadas"""
        if not self.charts_data:
            return None
            
        summary = {
            'total_charts': len(self.charts_data),
            'available_charts': [chart['type'] for chart in self.charts_data.values()],
            'project_id': self.project.id,
            'generated_at': pd.Timestamp.now().isoformat()
        }
        
        return summary