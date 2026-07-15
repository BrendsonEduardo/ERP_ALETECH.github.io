from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Colaborador, Aviso


@admin.register(Aviso)
class AvisoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'data_publicacao', 'ativo')
    list_filter = ('tipo', 'ativo')
    search_fields = ('titulo', 'conteudo')
    list_editable = ('ativo',)
    ordering = ('-data_publicacao',)

@admin.register(Colaborador)
class ColaboradorAdmin(UserAdmin):
    # REVISADO: Adicionado 'setor' e 'cargo' na listagem principal de funcionários
    list_display = ('username', 'email', 'first_name', 'last_name', 'setor', 'cargo', 'is_staff', 'is_active')
    
    # REVISADO: Adicionado filtros por setor e cargo na barra lateral direita
    list_filter = ('setor', 'cargo', 'is_staff', 'is_active', 'groups')
    
    # REVISADO: Injetando os novos campos customizados dentro de um bloco exclusivo na página de edição
    fieldsets = (
        ('Informações de Login', {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email')}),
        ('Contrato e Função (ERP AleTech)', {
            'fields': ('setor', 'cargo', 'telefone'),
        }),
        ('Permissões de Acesso', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Datas', {'fields': ('last_login', 'date_joined')}),
    )