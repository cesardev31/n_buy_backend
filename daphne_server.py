import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'n_buy_backend.settings')
django.setup()

# Importar después de configurar Django
from channels.routing import get_default_application
application = get_default_application()