# helpdesk/admin.py
from django.contrib import admin
from .models import Chamado

# Configuração para o painel de controle ficar bonito e fácil de filtrar
class ChamadoAdmin(admin.ModelAdmin):
    # Exibe as colunas reais presentes no seu models.py
    list_display = ('id', 'empresa', 'solicitante', 'equipamento', 'status', 'data_hora') 
    
    # Filtragem lateral inteligente por campos existentes
    list_filter = ('status', 'prioridade', 'empresa', 'forma_atendimento') 
    
    # Barra de pesquisa funcional
    search_fields = ('id', 'empresa', 'solicitante', 'problema') 

# Registra o modelo no painel administrativo do Django
admin.site.register(Chamado, ChamadoAdmin)