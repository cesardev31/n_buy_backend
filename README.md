# N-Buy Backend

Backend para la plataforma N-Buy, un sistema de comercio electrónico con recomendaciones personalizadas y chat en tiempo real.

## Características

- 🛍️ Sistema de productos y categorías
- 💬 Chat en tiempo real con WebSocket
- 🤖 Sistema de recomendaciones personalizado
- 👤 Gestión de usuarios y autenticación
- 📊 Sistema de preferencias de usuario
- 🔄 Actualizaciones en tiempo real

## Tecnologías

- Python 3.12+
- Django 4.2+
- Django Channels para WebSocket
- PostgreSQL
- Redis para caché y WebSocket

## Estructura del Proyecto

```
n_buy_backend/
├── chat/                   # App de chat en tiempo real
├── products/              # App de gestión de productos
├── recommendations/       # Sistema de recomendaciones
├── users/                # Gestión de usuarios
└── n_buy_backend/        # Configuración principal
```

## Requisitos

- Python 3.12 o superior
- PostgreSQL
- Redis
- Entorno virtual (venv)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/n_buy_backend.git
cd n_buy_backend
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
   - Crear archivo `.env` en la raíz del proyecto
   - Copiar `.env.example` a `.env`
   - Configurar las variables necesarias

5. Aplicar migraciones:
```bash
python manage.py migrate
```

6. Crear superusuario:
```bash
python manage.py createsuperuser
```

7. Cargar datos de ejemplo (opcional):
```bash
python create_sample_data.py
```

## Ejecución

1. Activar el entorno virtual:
```bash
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. Iniciar el servidor:
```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

## Endpoints Principales

- `/admin/` - Panel de administración
- `/api/products/` - API de productos
- `/ws/chat/` - WebSocket para chat
- `/api/recommendations/` - API de recomendaciones

## Características del Sistema de Recomendaciones

El sistema utiliza varios factores para generar recomendaciones personalizadas:

- Preferencias del usuario
- Historial de compras
- Similitud entre productos
- Categorías preferidas
- Calificaciones de productos

## Desarrollo

### Estructura de Branches

- `main` - Producción
- `develop` - Desarrollo
- `feature/*` - Nuevas características
- `hotfix/*` - Correcciones urgentes

### Comandos Útiles

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ejecutar tests
python manage.py test

# Crear superusuario
python manage.py createsuperuser
```

## Contribución

1. Fork el repositorio
2. Crear branch para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

César - [@cesardev31](https://github.com/cesardev31)

Link del proyecto: [https://github.com/cesardev31/n_buy_backend](https://github.com/cesardev31/n_buy_backend)
