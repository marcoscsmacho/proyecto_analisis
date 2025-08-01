// JavaScript principal para la aplicación

document.addEventListener('DOMContentLoaded', function() {
    
    // === ANIMACIONES ===
    // Agregar animación fade-in a las cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in-up');
    });
    
    // === TOOLTIPS ===
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // === ALERTAS ===
    // Auto-cerrar alertas después de 5 segundos
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (!alert.classList.contains('alert-danger')) {
            setTimeout(() => {
                if (alert) {
                    alert.classList.add('fade');
                    setTimeout(() => alert.remove(), 150);
                }
            }, 5000);
        }
    });
    
    // === FORMULARIOS ===
    // Validación mejorada de formularios
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // === NAVBAR ===
    // Marcar enlace activo en navbar
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // === EFECTOS HOVER ===
    // Efecto hover en las cards de estadísticas
    const statsCards = document.querySelectorAll('.stats-card');
    statsCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // === UTILIDADES ===
    // Función para mostrar notificaciones
    window.showNotification = function(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remover después de 4 segundos
        setTimeout(() => {
            if (alertDiv) {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }
        }, 4000);
    };
    
    // === CONFIRMACIONES ===
    // Confirmación para acciones de eliminación
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            const message = this.getAttribute('data-confirm-delete') || 
                          '¿Estás seguro de que quieres eliminar este elemento?';
            
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
    
    // === CARGA DE DATOS ===
    // Indicador de carga para formularios
    const submitButtons = document.querySelectorAll('form [type="submit"]');
    submitButtons.forEach(button => {
        button.closest('form').addEventListener('submit', function() {
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando...';
            button.disabled = true;
        });
    });
    
});

// === FUNCIONES GLOBALES ===

// Función para copiar texto al portapapeles
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Texto copiado al portapapeles', 'success');
    }).catch(function() {
        showNotification('Error al copiar texto', 'danger');
    });
}

// Función para formatear números
function formatNumber(num) {
    return new Intl.NumberFormat('es-ES').format(num);
}

// Función para formatear fechas
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Función para validar archivos
function validateFile(file, allowedTypes = ['csv', 'xlsx', 'xls'], maxSize = 16) {
    const fileExtension = file.name.split('.').pop().toLowerCase();
    const fileSizeMB = file.size / (1024 * 1024);
    
    if (!allowedTypes.includes(fileExtension)) {
        showNotification(`Tipo de archivo no permitido. Solo se permiten: ${allowedTypes.join(', ')}`, 'danger');
        return false;
    }
    
    if (fileSizeMB > maxSize) {
        showNotification(`El archivo es demasiado grande. Máximo permitido: ${maxSize}MB`, 'danger');
        return false;
    }
    
    return true;
}

// === SMOOTH SCROLLING ===
// Scroll suave para enlaces ancla
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});