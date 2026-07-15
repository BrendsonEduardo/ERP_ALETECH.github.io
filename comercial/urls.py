# comercial/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 1. Painel Principal (Kanban Comercial)
    path('', views.painel_comercial, name='painel_comercial'),

    # 2. Cadastro e Manutenção de Clientes
    path('cliente/novo/', views.novo_cliente, name='novo_cliente'),
    path('cliente/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('cliente/<int:pk>/excluir/', views.excluir_cliente, name='excluir_cliente'),

    # 3. Cadastro e API de Oportunidades (Kanban Drag and Drop — CSRF protegido)
    path('oportunidade/nova/', views.nova_oportunidade, name='nova_oportunidade'),
    path('oportunidade/atualizar-estagio/', views.atualizar_estagio_kanban, name='atualizar_estagio_kanban'),

    # 4. Visualização, Edição e Testes de Oportunidades
    path('oportunidade/<int:pk>/', views.detalhe_proposta, name='detalhe_proposta'),
    path('oportunidade/<int:pk>/editar/', views.editar_proposta, name='editar_proposta'),
    path('oportunidade/<int:op_id>/teste/', views.gerenciar_teste, name='gerenciar_teste'),

    # 5. Visões Globais, Listagens e Relatórios
    path('dashboard/', views.comercial_dashboard, name='comercial_dashboard'),
    path('clientes/lista/', views.comercial_clientes_lista, name='comercial_clientes_lista'),
    path('relatorios/', views.central_relatorios, name='central_relatorios'),
    path('relatorios/exportar/', views.exportar_relatorio_clientes, name='exportar_relatorio_clientes'),
]