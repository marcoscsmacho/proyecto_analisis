from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()

def init_db(app):
    """Inicializar la base de datos con la aplicación Flask"""
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configuración de Flask-Login
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    # Función para cargar usuario
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return db