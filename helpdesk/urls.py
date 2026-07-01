from django.urls import path
from . import views

urlpatterns = [
    # 1. Rota raiz do módulo Helpdesk (Aponta para a view unificada)
    path('', views.painel_helpdesk, name='painel_helpdesk'),
    
    # 2. Cadastro de novos chamados (Com a barra final correta)
    path('novo/', views.novo_chamado, name='novo_chamado'),
    
    # 3. Operações e manipulação do chamado por ID
    path('atualizar_status/<int:id>/', views.atualizar_status, name='atualizar_status'),
    path('deletar_chamado/<int:id>/', views.deletar_chamado, name='deletar_chamado'),
    path('chamado/<int:id>/', views.detalhe_chamado, name='detalhe_chamado'),
]