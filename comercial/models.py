# comercial/models.py
from django.db import models
from django.conf import settings
import datetime
import re

from .querysets import OportunidadeManager, ClienteManager


class Cliente(models.Model):
    TIPO_CHOICES = [('PF', 'Pessoa Física'), ('PJ', 'Pessoa Jurídica')]

    nome_fantasia = models.CharField(max_length=200)
    razao_social = models.CharField(max_length=200, blank=True, null=True)
    cnpj_cpf = models.CharField(max_length=20, unique=True)
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, default='PJ')
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    endereco = models.TextField(blank=True, null=True)

    contato_responsavel = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Contato Responsável"
    )

    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carteira_clientes',
        db_index=True,
        help_text="Vendedor responsável pela carteira deste cliente."
    )

    data_cadastro = models.DateTimeField(auto_now_add=True)
    ultima_atualizacao = models.DateTimeField(auto_now=True)
    ficha_cadastral = models.FileField(upload_to='fichas_cadastrais/', null=True, blank=True)

    # Manager customizado com lógica de permissão centralizada
    objects = ClienteManager()

    def __str__(self):
        return self.nome_fantasia

    def save(self, *args, **kwargs):
        if self.cnpj_cpf:
            self.cnpj_cpf = re.sub(r'[^0-9]', '', str(self.cnpj_cpf))
        super().save(*args, **kwargs)


class Oportunidade(models.Model):
    ESTAGIO_CHOICES = [
        ('Prospecção', 'Prospecção'),
        ('Qualificação', 'Qualificação'),
        ('Proposta', 'Proposta Enviada'),
        ('Negociação', 'Negociação'),
        ('Em_Teste', '🔬 Em Teste / Validação'),
        ('Fechado_Ganhou', '🏆 Fechado (Aprovado)'),
        ('Fechado_Perdeu', '❌ Fechado (Perdeu)'),
    ]

    titulo = models.CharField(max_length=200)
    # PROTECT está correto para segurança financeira do histórico de vendas
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='oportunidades')
    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, db_index=True)
    valor_estimado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    estagio = models.CharField(max_length=20, choices=ESTAGIO_CHOICES, default='Prospecção', db_index=True)
    data_fechamento_prevista = models.DateField()
    descricao = models.TextField(blank=True, null=True)
    contrato_proposta = models.FileField(upload_to='propostas_contratos/', null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultima_atualizacao = models.DateTimeField(auto_now=True, db_index=True)

    # Manager customizado com lógica de permissão centralizada
    objects = OportunidadeManager()

    def __str__(self):
        return f"{self.titulo} - {self.cliente.nome_fantasia}"


class TesteOportunidade(models.Model):
    oportunidade = models.OneToOneField(Oportunidade, on_delete=models.CASCADE, related_name='teste')
    setor_projeto = models.CharField("Setor / Projeto ou Empresa Destinada", max_length=150, help_text="Ex: TI / Projeto Expansão Fabril")
    data_envio = models.DateField("Data de Envio do Equipamento")
    dias_duracao = models.PositiveIntegerField("Quantidade de Dias de Teste", default=7)
    observacoes = models.TextField("Observações Técnicas / Escopo do Teste", blank=True, null=True)

    data_cadastro = models.DateTimeField(auto_now_add=True)
    ultima_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Teste: {self.oportunidade.titulo} ({self.setor_projeto})"

    @property
    def data_devolucao_prevista(self):
        if self.data_envio:
            return self.data_envio + datetime.timedelta(days=self.dias_duracao)
        return None


class EquipamentoTeste(models.Model):
    teste = models.ForeignKey(TesteOportunidade, on_delete=models.CASCADE, related_name='equipamentos')
    marca = models.CharField("Marca", max_length=100)
    modelo = models.CharField("Modelo", max_length=100)
    quantidade = models.PositiveIntegerField("Quantidade", default=1)

    # unique=True removido para permitir rastreabilidade do mesmo equipamento em testes históricos
    numero_serie = models.CharField("Número de Série", max_length=100)

    def __str__(self):
        return f"{self.marca} {self.modelo} (S/N: {self.numero_serie})"