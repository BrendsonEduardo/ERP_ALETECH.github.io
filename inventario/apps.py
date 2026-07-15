# inventario/apps.py
from django.apps import AppConfig


class InventarioConfig(AppConfig):
    """Configuração do app de Inventário de Ativos de TI."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "inventario"
    verbose_name = "Inventário de Ativos"
