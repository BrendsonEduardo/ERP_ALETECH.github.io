# usuarios/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class Colaborador(AbstractUser):
    # 1. Lista de Cargos Padronizados
    CARGOS_CHOICES = [
        ('COMER', 'Comercial'),
        ('SUPOR', 'Suporte Técnico'),
        ('FINAN', 'Financeiro'),
        ('LIDER', 'Líder Geral'),
        ('DONO', 'Diretoria / Dono'),
    ]

    # 2. Lista de Setores Padronizados
    SETORES_CHOICES = [
        ('COMERCIAL', 'Comercial'),
        ('SUPORTE', 'Suporte Técnico / TI'),
        ('FINANCEIRO', 'Financeiro'),
        ('DIRETORIA', 'Diretoria / Gerência'),
    ]
    
    # Campos customizados do ERP AleTech
    setor = models.CharField(
        max_length=20, 
        choices=SETORES_CHOICES, 
        default='SUPORTE',
        verbose_name="Setor"
    )
    
    cargo = models.CharField(
        max_length=5, 
        choices=CARGOS_CHOICES, 
        default='SUPOR',
        verbose_name="Cargo / Função"
    )
    
    telefone = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        verbose_name="Telefone"
    )

    def __str__(self):
        nome = self.get_full_name() or self.username
        return f"{nome} ({self.username}) - {self.get_cargo_display()}"