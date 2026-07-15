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


class Aviso(models.Model):
    """
    Avisos e comunicados exibidos no painel inicial do ERP.
    Gerenciados pelo Django Admin — sem necessidade de editar código para atualizar.
    """
    TIPO_CHOICES = [
        ('urgente', '🔴 Urgente'),
        ('sucesso', '🟢 Sucesso'),
        ('info', '🔵 Informação'),
        ('alerta', '🟡 Alerta'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título")
    conteudo = models.TextField(verbose_name="Conteúdo")
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default='info',
        verbose_name="Tipo"
    )
    data_publicacao = models.DateField(verbose_name="Data de Publicação", auto_now_add=True)
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Aviso"
        verbose_name_plural = "Avisos"
        ordering = ['-data_publicacao']

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo}"