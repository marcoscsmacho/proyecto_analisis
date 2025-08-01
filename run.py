from flask import Flask
from config.config import config
from config.database import init_db, db
from app.controllers.main_controller import main, init_routes
import os

def create_app(config_name='default'):
    """Factory para crear la aplicación Flask"""
    
    # Crear instancia de Flask
    import os
    template_dir = os.path.abspath('app/templates')
    static_dir = os.path.abspath('app/static')
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    init_db(app)
    
    # Crear directorios necesarios
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
    
    # Registrar blueprints
    app.register_blueprint(main)
    
    # Rutas de configuración inicial (solo para desarrollo)
    @app.route('/setup')
    def setup():
        """Página de configuración inicial"""
        return '''
        <div style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>🚀 Configuración Inicial del Proyecto</h1>
            <p>Usa estas rutas para configurar tu aplicación:</p>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3>Pasos de configuración:</h3>
                <ol>
                    <li><a href="/test-db" style="color: #007bff;">Probar conexión a base de datos</a></li>
                    <li><a href="/create-tables" style="color: #007bff;">Crear tablas</a></li>
                    <li><a href="/create-admin" style="color: #007bff;">Crear usuario administrador</a></li>
                    <li><a href="/" style="color: #28a745;"><strong>Ir a la aplicación</strong></a></li>
                </ol>
            </div>
            <div style="background: #e7f3ff; padding: 15px; border-radius: 8px;">
                <strong>💡 Tip:</strong> Una vez completados los pasos, ve directamente a 
                <a href="/" style="color: #007bff;">la aplicación principal</a>
            </div>
        </div>
        '''
    
    @app.route('/test-db')
    def test_db():
        """Probar conexión a la base de datos"""
        try:
            from sqlalchemy import text
            with db.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
            return '''
            <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
                <h2 style="color: #28a745;">✅ Conexión a base de datos exitosa!</h2>
                <p>La base de datos está funcionando correctamente.</p>
                <a href="/setup" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    ← Volver al setup
                </a>
            </div>
            '''
        except Exception as e:
            return f'''
            <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
                <h2 style="color: #dc3545;">❌ Error de conexión:</h2>
                <p style="background: #f8d7da; padding: 15px; border-radius: 5px; color: #721c24;">
                    {str(e)}
                </p>
                <a href="/setup" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    ← Volver al setup
                </a>
            </div>
            '''
    
    @app.route('/create-tables')
    def create_tables():
        """Crear todas las tablas"""
        try:
            # Importar modelos para que SQLAlchemy los reconozca
            from app.models.user import User
            from app.models.project import Project
            
            # Crear todas las tablas
            with app.app_context():
                db.create_all()
            
            return '''
            <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
                <h2 style="color: #28a745;">✅ Tablas creadas exitosamente!</h2>
                <p>Las siguientes tablas han sido creadas:</p>
                <ul style="text-align: left; display: inline-block;">
                    <li><strong>users</strong> (usuarios)</li>
                    <li><strong>projects</strong> (proyectos)</li>
                </ul>
                <div style="margin-top: 20px;">
                    <a href="/create-admin" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">
                        Crear usuario administrador →
                    </a>
                    <br><br>
                    <a href="/setup" style="background: #6c757d; color: white; padding: 8px 16px; text-decoration: none; border-radius: 5px;">
                        ← Volver al setup
                    </a>
                </div>
            </div>
            '''
        except Exception as e:
            return f'''
            <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
                <h2 style="color: #dc3545;">❌ Error al crear tablas:</h2>
                <p style="background: #f8d7da; padding: 15px; border-radius: 5px; color: #721c24;">
                    {str(e)}
                </p>
                <a href="/setup" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    ← Volver al setup
                </a>
            </div>
            '''
    
    @app.route('/create-admin')
    def create_admin():
        """Crear usuario administrador por defecto"""
        try:
            from app.models.user import User
            
            # Verificar si ya existe un admin
            admin_exists = User.query.filter_by(username='admin').first()
            if admin_exists:
                return '''
                <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
                    <h2 style="color: #ffc107;">⚠️ El usuario administrador ya existe!</h2>
                    <p>Puedes usar las credenciales existentes:</p>
                    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>Usuario:</strong> admin<br>
                        <strong>Contraseña:</strong> admin123
                    </div>
                    <a href="/" style="background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-size: 18px;">
                        🚀 Ir a la aplicación
                    </a>
                </div>
                '''
            
            # Crear usuario administrador
            admin = User(
                username='admin',
                email='admin@proyecto.com',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema',
                role='admin'
            )
            admin.save()
            
            return '''
            <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
                <h2 style="color: #28a745;">✅ Usuario administrador creado!</h2>
                <div style="background: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h4>Credenciales de acceso:</h4>
                    <p style="font-size: 18px; margin: 10px 0;">
                        <strong>Usuario:</strong> <code style="background: #fff; padding: 5px 10px; border-radius: 3px;">admin</code>
                    </p>
                    <p style="font-size: 18px; margin: 10px 0;">
                        <strong>Contraseña:</strong> <code style="background: #fff; padding: 5px 10px; border-radius: 3px;">admin123</code>
                    </p>
                    <p style="font-size: 18px; margin: 10px 0;">
                        <strong>Rol:</strong> <span style="background: #007bff; color: white; padding: 3px 8px; border-radius: 12px; font-size: 14px;">Administrador</span>
                    </p>
                </div>
                <a href="/" style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-size: 20px; font-weight: bold;">
                    🚀 ¡Ir a la aplicación!
                </a>
                <br><br>
                <small style="color: #6c757d;">¡Ya puedes usar estas credenciales para acceder al sistema!</small>
            </div>
            '''
        except Exception as e:
            return f'''
            <div style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
                <h2 style="color: #dc3545;">❌ Error al crear administrador:</h2>
                <p style="background: #f8d7da; padding: 15px; border-radius: 5px; color: #721c24;">
                    {str(e)}
                </p>
                <a href="/setup" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    ← Volver al setup
                </a>
            </div>
            '''
    
    return app

if __name__ == '__main__':
    # Crear la aplicación
    app = create_app('development')
    
    # Ejecutar la aplicación
    print("🚀 Iniciando servidor de desarrollo...")
    print("📍 Accede a: http://localhost:5000")
    print("⚙️  Configuración inicial: http://localhost:5000/setup")
    app.run(debug=True, host='0.0.0.0', port=5000)