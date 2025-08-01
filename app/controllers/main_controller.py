from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional
from werkzeug.utils import secure_filename
from datetime import datetime
from app.models.user import User
from app.models.project import Project
from app.services.data_processing.file_processor import FileProcessor
from app.services.visualization.chart_service import ChartService
from app.services.reports.pdf_service import PDFService
import os

# Configurar matplotlib para no usar GUI
import matplotlib
matplotlib.use('Agg')  # Usar backend sin GUI

# Crear el blueprint
main = Blueprint('main', __name__)

# === FORMULARIOS ===
class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordar sesión')
    submit = SubmitField('Iniciar Sesión')

class UploadForm(FlaskForm):
    project_name = StringField('Nombre del Proyecto', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    file = FileField('Archivo', validators=[
        FileRequired('Debe seleccionar un archivo'),
        FileAllowed(['csv', 'xlsx', 'xls'], 'Solo se permiten archivos CSV, XLS y XLSX')
    ])
    submit = SubmitField('Procesar Archivo')

class ProfileForm(FlaskForm):
    first_name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    new_password = PasswordField('Nueva Contraseña', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña')
    submit = SubmitField('Guardar Cambios')
    
    def validate_confirm_password(self, field):
        if self.new_password.data and field.data != self.new_password.data:
            raise ValueError('Las contraseñas no coinciden')

# === RUTAS DE AUTENTICACIÓN ===
@main.route('/')
def index():
    """Página de inicio - redirige según el estado de autenticación"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Buscar usuario por username
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if user.is_active:
                login_user(user, remember=form.remember_me.data)
                flash(f'¡Bienvenido, {user.full_name}!', 'success')
                
                # Redirigir a la página solicitada o al dashboard
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
            else:
                flash('Tu cuenta está inactiva. Contacta al administrador.', 'warning')
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    
    return render_template('pages/login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    user_name = current_user.full_name
    logout_user()
    flash(f'Hasta luego, {user_name}!', 'info')
    return redirect(url_for('main.login'))

# === RUTAS PRINCIPALES ===
@main.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal"""
    # Obtener estadísticas del usuario
    total_projects = Project.query.filter_by(user_id=current_user.id).count()
    completed_projects = Project.query.filter_by(user_id=current_user.id, status='completed').count()
    recent_projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).limit(5).all()
    
    stats = {
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'pending_projects': total_projects - completed_projects,
        'success_rate': round((completed_projects / total_projects * 100) if total_projects > 0 else 0, 1)
    }
    
    return render_template('pages/dashboard.html', stats=stats, recent_projects=recent_projects)

@main.route('/projects')
@login_required
def projects():
    """Lista de proyectos del usuario"""
    user_projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).all()
    return render_template('pages/projects.html', projects=user_projects)

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Página de perfil del usuario"""
    form = ProfileForm()
    
    # Prellenar formulario con datos actuales
    if request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    if form.validate_on_submit():
        try:
            # Verificar que username no esté en uso por otro usuario
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user and existing_user.id != current_user.id:
                flash('El nombre de usuario ya está en uso.', 'error')
                return render_template('pages/profile.html', form=form)
            
            # Verificar que email no esté en uso por otro usuario
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email and existing_email.id != current_user.id:
                flash('El email ya está en uso.', 'error')
                return render_template('pages/profile.html', form=form)
            
            # Actualizar información del usuario
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.username = form.username.data
            current_user.email = form.email.data
            
            # Cambiar contraseña si se proporcionó
            if form.new_password.data:
                current_user.set_password(form.new_password.data)
            
            # Guardar cambios
            current_user.save()
            
            flash('Perfil actualizado exitosamente.', 'success')
            return redirect(url_for('main.profile'))
            
        except Exception as e:
            from config.database import db
            db.session.rollback()
            flash(f'Error al actualizar perfil: {str(e)}', 'error')
    
    return render_template('pages/profile.html', form=form)

@main.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Página para subir archivos"""
    form = UploadForm()
    
    if form.validate_on_submit():
        try:
            # Inicializar procesador de archivos
            processor = FileProcessor(current_app.config['UPLOAD_FOLDER'])
            
            # Validar y guardar archivo
            file_info = processor.save_file(form.file.data, current_user.id)
            
            # Analizar archivo
            analysis = processor.analyze_file(file_info['file_path'])
            
            # Crear proyecto en la base de datos
            project = Project(
                name=form.project_name.data,
                filename=file_info['filename'],
                original_filename=file_info['original_filename'],
                file_path=file_info['file_path'],
                user_id=current_user.id,
                description=form.description.data or None
            )
            
            # GUARDAR EL PROYECTO PRIMERO
            project.save()
            
            # Actualizar información del análisis
            project.update_analysis_info(
                analysis['rows_count'],
                analysis['columns_count'],
                analysis['columns_info']
            )
            
            flash(f'¡Archivo procesado exitosamente! Se encontraron {analysis["rows_count"]} filas y {analysis["columns_count"]} columnas.', 'success')
            return redirect(url_for('main.project_detail', project_id=project.id))
            
        except Exception as e:
            # Hacer rollback de la sesión si hay error
            from config.database import db
            db.session.rollback()
            flash(f'Error al procesar archivo: {str(e)}', 'error')
    
    return render_template('pages/upload.html', form=form)

@main.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    """Detalle de un proyecto específico"""
    project = Project.query.get_or_404(project_id)
    
    # Verificar que el proyecto pertenezca al usuario actual (o que sea admin)
    if project.user_id != current_user.id and not current_user.is_admin():
        flash('No tienes permisos para ver este proyecto.', 'error')
        return redirect(url_for('main.projects'))
    
    return render_template('pages/project.html', project=project)

# === RUTAS DE ANÁLISIS ===
@main.route('/project/<int:project_id>/generate-charts')
@login_required
def generate_charts(project_id):
    """Generar gráficas para un proyecto"""
    project = Project.query.get_or_404(project_id)
    
    # Verificar permisos
    if project.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'status': 'error', 'message': 'No tienes permisos para este proyecto'})
    
    try:
        # Generar gráficas
        chart_service = ChartService(project)
        charts = chart_service.generate_all_charts()
        
        # Marcar proyecto como que tiene gráficas
        project.mark_charts_generated('charts_generated')
        
        return jsonify({
            'status': 'success',
            'charts': charts,
            'message': 'Gráficas generadas exitosamente'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al generar gráficas: {str(e)}'
        })

@main.route('/project/<int:project_id>/generate-pdf')
@login_required
def generate_pdf(project_id):
    """Generar reporte PDF para un proyecto"""
    project = Project.query.get_or_404(project_id)
    
    # Verificar permisos
    if project.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'status': 'error', 'message': 'No tienes permisos para este proyecto'})
    
    try:
        # Generar PDF
        pdf_service = PDFService(project, current_app.config['REPORTS_FOLDER'])
        result = pdf_service.generate_complete_report()
        
        if result['success']:
            # Marcar proyecto como que tiene reporte
            project.mark_report_generated(result['pdf_path'])
            
            return jsonify({
                'status': 'success',
                'pdf_path': result['pdf_path'],
                'filename': result['filename'],
                'size_mb': round(result['size'] / (1024 * 1024), 2),
                'message': 'Reporte PDF generado exitosamente'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Error al generar PDF: {result["error"]}'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al generar PDF: {str(e)}'
        })

@main.route('/download-pdf/<int:project_id>')
@login_required
def download_pdf(project_id):
    """Descargar PDF de un proyecto"""
    project = Project.query.get_or_404(project_id)
    
    # Verificar permisos
    if project.user_id != current_user.id and not current_user.is_admin():
        flash('No tienes permisos para descargar este reporte.', 'error')
        return redirect(url_for('main.projects'))
    
    # Verificar que existe el PDF
    if not project.pdf_report_path or not os.path.exists(project.pdf_report_path):
        flash('El reporte PDF no existe. Génera uno nuevo.', 'warning')
        return redirect(url_for('main.project_detail', project_id=project_id))
    
    # Enviar archivo para descarga
    return send_file(
        project.pdf_report_path,
        as_attachment=True,
        download_name=f"reporte_{project.name}_{datetime.now().strftime('%Y%m%d')}.pdf",
        mimetype='application/pdf'
    )

# === RUTA DE ELIMINACIÓN ===
@main.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """Eliminar un proyecto y todos sus archivos asociados"""
    project = Project.query.get_or_404(project_id)
    
    # Verificar permisos - solo el dueño o admin pueden eliminar
    if project.user_id != current_user.id and not current_user.is_admin():
        flash('No tienes permisos para eliminar este proyecto.', 'error')
        return redirect(url_for('main.projects'))
    
    try:
        project_name = project.name  # Guardar nombre antes de eliminar
        
        # Eliminar archivos físicos asociados al proyecto
        project.delete_files()
        
        # Eliminar registro de la base de datos
        project.delete()
        
        flash(f'Proyecto "{project_name}" eliminado exitosamente.', 'success')
        
    except Exception as e:
        # En caso de error, hacer rollback de la sesión
        from config.database import db
        db.session.rollback()
        flash(f'Error al eliminar proyecto: {str(e)}', 'error')
    
    return redirect(url_for('main.projects'))

# === RUTAS DE ADMINISTRACIÓN ===
@main.route('/admin')
@login_required
def admin():
    """Panel de administración (solo para admins)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Estadísticas generales del sistema
    total_users = User.query.count()
    total_projects = Project.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    
    admin_stats = {
        'total_users': total_users,
        'total_projects': total_projects,
        'active_users': User.query.filter_by(is_active=True).count(),
        'completed_projects': Project.query.filter_by(status='completed').count()
    }
    
    return render_template('pages/admin.html', 
                         stats=admin_stats, 
                         recent_users=recent_users, 
                         recent_projects=recent_projects)

@main.route('/admin/create-user', methods=['POST'])
@login_required
def admin_create_user():
    """Crear nuevo usuario desde el panel de administración"""
    if not current_user.is_admin():
        return jsonify({'status': 'error', 'message': 'No tienes permisos para esta acción'})
    
    try:
        # Obtener datos del formulario
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['firstName', 'lastName', 'username', 'email', 'password', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'status': 'error', 'message': f'El campo {field} es requerido'})
        
        # Verificar que el username no exista
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'status': 'error', 'message': 'El nombre de usuario ya existe'})
        
        # Verificar que el email no exista
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'status': 'error', 'message': 'El email ya está registrado'})
        
        # Crear nuevo usuario
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['firstName'],
            last_name=data['lastName'],
            role=data['role']
        )
        
        # Guardar usuario
        new_user.save()
        
        return jsonify({
            'status': 'success', 
            'message': f'Usuario {data["username"]} creado exitosamente',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'full_name': new_user.full_name,
                'email': new_user.email,
                'role': new_user.role
            }
        })
        
    except Exception as e:
        # En caso de error, hacer rollback
        from config.database import db
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error al crear usuario: {str(e)}'})

@main.route('/admin/toggle-user-status', methods=['POST'])
@login_required
def admin_toggle_user_status():
    """Activar/desactivar usuario"""
    if not current_user.is_admin():
        return jsonify({'status': 'error', 'message': 'No tienes permisos para esta acción'})
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        # Buscar usuario
        user = User.query.get_or_404(user_id)
        
        # No permitir desactivar el propio usuario
        if user.id == current_user.id:
            return jsonify({'status': 'error', 'message': 'No puedes desactivar tu propia cuenta'})
        
        # Cambiar estado
        user.is_active = not user.is_active
        user.save()
        
        action = 'activado' if user.is_active else 'desactivado'
        return jsonify({
            'status': 'success',
            'message': f'Usuario {user.username} {action} exitosamente',
            'user_id': user.id,
            'new_status': user.is_active
        })
        
    except Exception as e:
        from config.database import db
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error al cambiar estado: {str(e)}'})

# === FUNCIONES DE UTILIDAD ===
def init_routes(app):
    """Registrar el blueprint en la aplicación"""
    app.register_blueprint(main)