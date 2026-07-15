from django.db import models
from django.conf import settings

class Chamado(models.Model):
    # Opções de Status Oficiais padronizados pelo POP-001
    STATUS_CHOICES = [
        ('Aberto', 'Aberto'),
        ('Em Atendimento', 'Em Atendimento'),
        ('Aguardando Usuário', 'Aguardando Usuário'),
        ('Aguardando Terceiros', 'Aguardando Terceiros'),
        ('Resolvido', 'Resolvido'),
        ('Encerrado', 'Encerrado'),
    ]

    # Opções de Grau de Prioridade exigidos pelo POP-001
    PRIORIDADE_CHOICES = [
        ('Baixa', 'Baixa'),
        ('Média', 'Média'),
        ('Alta', 'Alta'),
    ]

    # Registra a data e hora exata da criação automaticamente
    data_hora = models.DateTimeField(auto_now_add=True)  
    # Adicione este campo logo abaixo do campo 'data_hora' no seu Chamado model:
    id_integracao = models.CharField(max_length=255, unique=True, blank=True, null=True, db_index=True)
    
    # Vincula o chamado a um Colaborador real do ERP
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='chamados_atribuidos'
    )
    
    # Informações gerais do atendimento
    nome_tecnico = models.CharField(max_length=100, blank=True, null=True, default='Não atribuído')
    empresa = models.CharField(max_length=150)
    solicitante = models.CharField(max_length=100)
    forma_atendimento = models.CharField(max_length=50, default='Presencial')
    contato = models.CharField(max_length=50)
    
    # Detalhes do problema
    equipamento = models.CharField(max_length=100)
    problema = models.TextField()
    
    # Grau de prioridade em conformidade com o POP-001
    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE_CHOICES,
        default='Média'
    )
    
    # Controle de fluxo e status baseado nas regras da empresa
    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES,
        default='Aberto'
    )  
    
    # Histórico de fechamento/ações executadas
    ultimo_comentario = models.TextField(blank=True, default='')
    
    # Histórico para automações de notificações (ex: e-mail/WhatsApp)
    notificado_abertura = models.CharField(max_length=10, default='NÃO')
    ultimo_status_notificado = models.CharField(max_length=50, default='Nenhum')
    
    # Tempo de SLA em formato string (ex: "01:30:00") vindo da planilha
    sla = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"#{self.id} - {self.empresa} ({self.status})"