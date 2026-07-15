# inventario/urls.py
"""
Rotas do módulo de Inventário de Ativos de TI.

Namespace: 'inventario'
Prefixo configurado no urls.py principal: /inventario/
"""

from django.urls import path

from . import views

app_name = "inventario"

urlpatterns = [
    # ── Ativos ────────────────────────────────────────────────────────────
    path("", views.lista_ativos, name="lista_ativos"),
    path("novo/", views.novo_ativo, name="novo_ativo"),
    path("editar/<int:pk>/", views.editar_ativo, name="editar_ativo"),
    path("deletar/<int:pk>/", views.deletar_ativo, name="deletar_ativo"),

    # ── Bipagem em Lote ───────────────────────────────────────────────────
    path("lote/", views.bipagem_lote, name="bipagem_lote"),

    # ── Movimentação Tablet ───────────────────────────────────────────────
    path("movimentacoes/", views.lista_movimentacoes, name="lista_movimentacoes"),
    path("movimentacao/", views.tela_movimentacao, name="tela_movimentacao"),
    path("movimentacao/validar/", views.validar_ativo_bipagem, name="validar_ativo_bipagem"),
    path("movimentacao/buscar-acessorios/", views.buscar_acessorios, name="buscar_acessorios"),
    path("movimentacao/processar/", views.processar_lote_movimentacao, name="processar_lote_movimentacao"),
    path("movimentacao/pdf/<int:movimentacao_id>/", views.gerar_pdf_cautela, name="gerar_pdf_cautela"),

    # ── Catálogo de Modelos ───────────────────────────────────────────────
    path("modelos/", views.lista_modelos, name="lista_modelos"),
    path("modelos/novo/", views.cadastrar_modelo, name="cadastrar_modelo"),
]

