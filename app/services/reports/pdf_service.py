import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import base64
from PIL import Image as PILImage
from app.services.visualization.chart_service import ChartService

class PDFService:
    """Servicio para generar reportes PDF completos"""
    
    def __init__(self, project, output_folder):
        self.project = project
        self.output_folder = output_folder
        self.styles = getSampleStyleSheet()
        self.charts_data = None
        
        # Crear estilos personalizados
        self._create_custom_styles()
        
    def _create_custom_styles(self):
        """Crear estilos personalizados para el PDF"""
        # Estilo para título principal
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Estilo para subtítulos
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#34495e')
        )
        
        # Estilo para texto normal
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            alignment=TA_LEFT
        )
        
        # Estilo para información destacada
        self.info_style = ParagraphStyle(
            'CustomInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=6
        )
    
    def generate_complete_report(self):
        """Generar reporte PDF completo"""
        try:
            # Crear carpeta de reportes si no existe
            os.makedirs(self.output_folder, exist_ok=True)
            
            # Generar nombre único para el PDF
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"reporte_{self.project.name}_{timestamp}.pdf"
            pdf_path = os.path.join(self.output_folder, filename)
            
            # Crear documento PDF
            doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=0.5*inch)
            story = []
            
            # Generar gráficas primero
            chart_service = ChartService(self.project)
            self.charts_data = chart_service.generate_all_charts()
            
            # 1. Portada
            story.extend(self._create_cover_page())
            story.append(PageBreak())
            
            # 2. Información del proyecto
            story.extend(self._create_project_info())
            story.append(Spacer(1, 20))
            
            # 3. Análisis de datos
            story.extend(self._create_data_analysis())
            story.append(PageBreak())
            
            # 4. Gráficas
            story.extend(self._create_charts_section())
            
            # 5. Estadísticas descriptivas
            if self.charts_data and 'statistics' in self.charts_data:
                story.append(PageBreak())
                story.extend(self._create_statistics_section())
            
            # 6. Conclusiones
            story.append(PageBreak())
            story.extend(self._create_conclusions())
            
            # Construir PDF
            doc.build(story)
            
            return {
                'success': True,
                'pdf_path': pdf_path,
                'filename': filename,
                'size': os.path.getsize(pdf_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_cover_page(self):
        """Crear portada del reporte"""
        elements = []
        
        # Título principal
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph("REPORTE DE ANÁLISIS DE DATOS", self.title_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # Información del proyecto
        elements.append(Paragraph(f"<b>Proyecto:</b> {self.project.name}", self.subtitle_style))
        elements.append(Spacer(1, 0.3*inch))
        
        if self.project.description:
            elements.append(Paragraph(f"<b>Descripción:</b> {self.project.description}", self.normal_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Información del archivo
        elements.append(Paragraph(f"<b>Archivo:</b> {self.project.original_filename}", self.normal_style))
        elements.append(Paragraph(f"<b>Tamaño:</b> {self.project.file_size_mb} MB", self.normal_style))
        elements.append(Paragraph(f"<b>Tipo:</b> {self.project.file_type.upper()}", self.normal_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Información del análisis
        elements.append(Paragraph(f"<b>Dimensiones:</b> {self.project.rows_count} filas × {self.project.columns_count} columnas", self.normal_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # Información del usuario y fecha
        elements.append(Paragraph(f"<b>Analista:</b> {self.project.owner.full_name}", self.info_style))
        elements.append(Paragraph(f"<b>Fecha de análisis:</b> {self.project.created_at.strftime('%d/%m/%Y %H:%M')}", self.info_style))
        elements.append(Paragraph(f"<b>Fecha del reporte:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", self.info_style))
        
        return elements
    
    def _create_project_info(self):
        """Crear sección de información del proyecto"""
        elements = []
        
        elements.append(Paragraph("1. INFORMACIÓN DEL PROYECTO", self.subtitle_style))
        
        # Tabla con información básica
        data = [
            ['Campo', 'Valor'],
            ['Nombre del proyecto', self.project.name],
            ['Archivo original', self.project.original_filename],
            ['Tamaño del archivo', f"{self.project.file_size_mb} MB"],
            ['Tipo de archivo', self.project.file_type.upper()],
            ['Estado del análisis', self.project.status.title()],
            ['Filas totales', str(self.project.rows_count)],
            ['Columnas totales', str(self.project.columns_count)]
        ]
        
        if self.project.description:
            data.append(['Descripción', self.project.description])
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_data_analysis(self):
        """Crear sección de análisis de datos"""
        elements = []
        
        elements.append(Paragraph("2. ANÁLISIS DE ESTRUCTURA DE DATOS", self.subtitle_style))
        
        if not self.project.columns_info:
            elements.append(Paragraph("No hay información de columnas disponible.", self.normal_style))
            return elements
        
        # Tabla de análisis de columnas
        data = [['Columna', 'Tipo', 'Valores Únicos', 'Valores Nulos', 'Información Adicional']]
        
        for col_name, info in self.project.columns_info.items():
            # Información adicional según el tipo
            additional_info = ""
            if info['type_category'] == 'numeric':
                if info.get('min_value') is not None and info.get('max_value') is not None:
                    additional_info = f"Min: {info['min_value']:.2f}, Max: {info['max_value']:.2f}"
                    if info.get('mean_value') is not None:
                        additional_info += f", Media: {info['mean_value']:.2f}"
            elif info['type_category'] == 'text':
                additional_info = f"Long. máx: {info.get('max_length', 0)}"
            elif info['type_category'] == 'datetime':
                additional_info = "Rango de fechas"
            
            data.append([
                col_name,
                info['type_category'].title(),
                str(info['unique_count']),
                str(info['null_count']),
                additional_info
            ])
        
        table = Table(data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_charts_section(self):
        """Crear sección con todas las gráficas"""
        elements = []
        
        elements.append(Paragraph("3. VISUALIZACIONES", self.subtitle_style))
        
        if not self.charts_data:
            elements.append(Paragraph("No se pudieron generar las gráficas.", self.normal_style))
            return elements
        
        # Agregar cada gráfica
        chart_order = ['bar_chart', 'heatmap', 'scatter_plot', 'wordcloud']
        
        for chart_type in chart_order:
            if chart_type in self.charts_data:
                chart = self.charts_data[chart_type]
                
                if chart.get('image_base64') and chart['type'] != 'placeholder':
                    # Título de la gráfica
                    elements.append(Paragraph(f"3.{chart_order.index(chart_type)+1} {chart['title']}", 
                                            self.normal_style))
                    elements.append(Paragraph(chart['description'], self.info_style))
                    elements.append(Spacer(1, 10))
                    
                    # Convertir imagen base64 a imagen para PDF
                    try:
                        image_data = base64.b64decode(chart['image_base64'])
                        img_buffer = BytesIO(image_data)
                        
                        # Crear imagen temporal
                        img = Image(img_buffer, width=6*inch, height=3.6*inch)
                        elements.append(img)
                        elements.append(Spacer(1, 20))
                        
                    except Exception as e:
                        elements.append(Paragraph(f"Error al cargar gráfica: {str(e)}", self.info_style))
                        elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_statistics_section(self):
        """Crear sección de estadísticas descriptivas"""
        elements = []
        
        elements.append(Paragraph("4. ESTADÍSTICAS DESCRIPTIVAS", self.subtitle_style))
        
        stats = self.charts_data.get('statistics')
        if not stats or not stats.get('data'):
            elements.append(Paragraph("No hay estadísticas numéricas disponibles.", self.normal_style))
            return elements
        
        # Tabla de estadísticas
        data = [['Variable', 'Media', 'Mediana', 'Moda', 'Desv. Est.', 'Mínimo', 'Máximo']]
        
        for column, stat_data in stats['data'].items():
            data.append([
                column,
                f"{stat_data['mean']:.2f}",
                f"{stat_data['median']:.2f}",
                f"{stat_data['mode']:.2f}" if stat_data.get('mode') else 'N/A',
                f"{stat_data['std']:.2f}",
                f"{stat_data['min']:.2f}",
                f"{stat_data['max']:.2f}"
            ])
        
        table = Table(data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fadbd8')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_conclusions(self):
        """Crear sección de conclusiones"""
        elements = []
        
        elements.append(Paragraph("5. CONCLUSIONES Y RESUMEN", self.subtitle_style))
        
        # Resumen automático basado en los datos
        conclusions = []
        
        # Conclusión sobre el tamaño del dataset
        conclusions.append(f"• El dataset analizado contiene {self.project.rows_count} registros distribuidos en {self.project.columns_count} variables.")
        
        # Conclusión sobre tipos de datos
        if self.project.columns_info:
            numeric_count = len([col for col, info in self.project.columns_info.items() if info['type_category'] == 'numeric'])
            text_count = len([col for col, info in self.project.columns_info.items() if info['type_category'] == 'text'])
            datetime_count = len([col for col, info in self.project.columns_info.items() if info['type_category'] == 'datetime'])
            
            conclusions.append(f"• La estructura de datos incluye {numeric_count} variables numéricas, {text_count} variables de texto y {datetime_count} variables de fecha.")
            
            # Conclusión sobre valores nulos
            null_columns = [col for col, info in self.project.columns_info.items() if info['null_count'] > 0]
            if null_columns:
                conclusions.append(f"• Se detectaron valores faltantes en {len(null_columns)} columna(s): {', '.join(null_columns[:3])}{'...' if len(null_columns) > 3 else ''}.")
            else:
                conclusions.append("• No se encontraron valores faltantes en el dataset.")
        
        # Conclusión sobre visualizaciones generadas
        if self.charts_data:
            chart_count = len([chart for chart in self.charts_data.values() if chart.get('type') != 'placeholder'])
            conclusions.append(f"• Se generaron {chart_count} visualizaciones para facilitar el análisis y comprensión de los datos.")
        
        conclusions.append(f"• El análisis fue realizado el {datetime.now().strftime('%d/%m/%Y')} por {self.project.owner.full_name}.")
        
        for conclusion in conclusions:
            elements.append(Paragraph(conclusion, self.normal_style))
            elements.append(Spacer(1, 8))
        
        # Nota final
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Este reporte fue generado automáticamente por el Sistema de Análisis de Datos.", 
                                self.info_style))
        
        return elements