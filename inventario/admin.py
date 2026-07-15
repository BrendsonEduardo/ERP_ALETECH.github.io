# inventario/admin.py
"""
Registro dos models do inventário no Django Admin.
"""

from django.contrib import admin

from .models import Ativo, ModeloEquipamento


@admin.register(ModeloEquipamento)
class ModeloEquipamentoAdmin(admin.ModelAdmin):
    list_display = ["marca", "modelo", "categoria"]
    list_filter = ["categoria"]
    search_fields = ["marca", "modelo"]


@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = [
        "numero_serie",
        "modelo_equipamento",
        "status",
        "cliente_atual",
        "unidade",
        "setor",
        "data_cadastro",
    ]
    list_filter = ["status", "modelo_equipamento__categoria"]
    search_fields = ["numero_serie", "cliente_atual__nome_fantasia"]
    readonly_fields = ["data_cadastro"]
