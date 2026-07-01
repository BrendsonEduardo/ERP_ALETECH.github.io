# comercial/apps.py
from django.apps import AppConfig

class ComercialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField' # Opcional: Garante consistência de IDs no Django moderno
    name = 'comercial'