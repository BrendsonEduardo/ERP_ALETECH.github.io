# inventario/models.py
"""
Models do módulo de Inventário de Ativos de TI.

Estrutura em dois níveis:
  - ModeloEquipamento: catálogo de hardware (o "tipo" do equipamento).
  - Ativo: unidade física real, individualizada pelo número de série.
"""

from django.db import models
from django.conf import settings


class ModeloEquipamento(models.Model):
    """
    Catálogo de modelos de hardware disponíveis na empresa.

    Serve como referência para a criação de ativos físicos individuais.
    Ex: "Dell Latitude 5420 Notebook".
    """

    class Categoria(models.TextChoices):
        NOTEBOOK  = "NOTEBOOK",   "Notebook"
        DESKTOP   = "DESKTOP",    "Desktop"
        MONITOR   = "MONITOR",    "Monitor"
        REDE      = "REDE",       "Ativo de Rede"
        IMPRESSORA = "IMPRESSORA", "Impressora"
        TABLET    = "TABLET",     "Tablet"
        COLETOR   = "COLETOR",    "Coletor de Dados"
        OUTROS    = "OUTROS",     "Outros"

    marca = models.CharField(
        max_length=100,
        verbose_name="Marca",
        help_text="Ex: Dell, Lenovo, HP, Samsung",
    )
    modelo = models.CharField(
        max_length=150,
        verbose_name="Modelo",
        help_text="Ex: Latitude 5420, ThinkPad E14",
    )
    categoria = models.CharField(
        max_length=50,  # ampliado para acomodar novos valores de choices
        choices=Categoria.choices,
        default=Categoria.OUTROS,
        db_index=True,
        verbose_name="Categoria",
    )
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição / Especificações",
        help_text="Processador, RAM, armazenamento e outros detalhes relevantes.",
    )

    class Meta:
        verbose_name = "Modelo de Equipamento"
        verbose_name_plural = "Modelos de Equipamento"
        ordering = ["marca", "modelo"]
        unique_together = [["marca", "modelo"]]

    def __str__(self) -> str:
        return f"{self.marca} {self.modelo} ({self.get_categoria_display()})"


class Ativo(models.Model):
    """
    Representa uma unidade física real de equipamento de TI.

    Cada Ativo é individualizado pelo número de série e rastreado por
    status operacional (Estoque, Alocado, Manutenção, Descarte) e pelo
    cliente/localização a que está vinculado.
    """

    class Status(models.TextChoices):
        ESTOQUE = "ESTOQUE", "Em Estoque"
        ALOCADO = "ALOCADO", "Alocado"
        TESTE = "TESTE", "Em Teste (Trial)"
        TRIAGEM = "TRIAGEM", "Em Triagem"
        MANUTENCAO = "MANUTENCAO", "Em Manutenção"
        DESCARTE = "DESCARTE", "Descarte"

    # ─── Referência ao catálogo ───────────────────────────────────────────
    modelo_equipamento = models.ForeignKey(
        ModeloEquipamento,
        on_delete=models.PROTECT,
        related_name="ativos",
        verbose_name="Modelo do Equipamento",
        help_text="Selecione o modelo no catálogo. Não é possível excluir modelos com ativos vinculados.",
    )

    # ─── Controle de serialização ───────────────────────────────────────────
    controla_serial = models.BooleanField(
        default=True,
        verbose_name="Controla Número de Série",
        help_text="Desmarque para acessórios/itens de lote (capas, fontes, berços) que não possuem S/N individual.",
    )

    # ─── Identificação física ─────────────────────────────────────────────
    numero_serie = models.CharField(
        max_length=200,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Número de Série (S/N)",
        help_text="Identificador único gravado no hardware. Deixe vazio para itens sem serial.",
    )

    # ─── Estoque de lote (apenas para itens sem serial) ──────────────────
    quantidade_estoque = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantidade em Estoque",
        help_text="Apenas para itens com controla_serial=False. Controla a quantidade disponível.",
    )

    # ─── Ciclo de vida ────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ESTOQUE,
        db_index=True,
        verbose_name="Status Operacional",
    )

    # ─── Alocação (opcional, usado quando status = ALOCADO) ──────────────
    cliente_atual = models.ForeignKey(
        "comercial.Cliente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ativos_alocados",
        verbose_name="Cliente Atual",
        help_text="Preenchido quando o ativo está alocado em um cliente.",
    )
    unidade = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Unidade",
        help_text="Ex: Matriz, Filial Manaus, Data Center",
    )
    setor = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Setor",
        help_text="Ex: Financeiro, RH, TI, Diretoria",
    )

    # ─── Auditoria ────────────────────────────────────────────────────────
    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Cadastro",
    )
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações",
        help_text="Histórico técnico, defeitos conhecidos ou notas relevantes.",
    )

    class Meta:
        verbose_name = "Ativo"
        verbose_name_plural = "Ativos"
        ordering = ["-data_cadastro"]

    def __str__(self) -> str:
        if self.controla_serial and self.numero_serie:
            return f"{self.modelo_equipamento} | S/N: {self.numero_serie}"
        return f"{self.modelo_equipamento} (Lote - Qtd: {self.quantidade_estoque})"

    @property
    def esta_alocado(self) -> bool:
        """Retorna True se o ativo estiver com status ALOCADO."""
        return self.status == self.Status.ALOCADO


class Movimentacao(models.Model):
    """
    Registra uma transação/movimentação de ativos.
    """
    class Tipo(models.TextChoices):
        ALOCACAO = "ALOCACAO", "Alocação"
        TESTE = "TESTE", "Teste (Trial)"
        DEVOLUCAO = "DEVOLUCAO", "Devolução"
        TROCA = "TROCA", "Troca (Swap)"
        VISITA = "VISITA", "Visita Técnica"

    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        db_index=True,
        verbose_name="Tipo de Movimentação"
    )
    cliente = models.ForeignKey(
        "comercial.Cliente",
        on_delete=models.PROTECT,
        related_name="movimentacoes",
        verbose_name="Cliente"
    )
    data = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Movimentação"
    )
    usuario_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Usuário Responsável"
    )
    cautela_pdf = models.FileField(
        upload_to="cautelas/",
        null=True,
        blank=True,
        verbose_name="PDF da Cautela"
    )
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Movimentação"
        verbose_name_plural = "Movimentações"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente} em {self.data.strftime('%d/%m/%Y')}"


class MovimentacaoItem(models.Model):
    """
    Itens vinculados a uma movimentação específica.
    Suporta tanto ativos com serial (1:1) quanto acessórios de lote (1:N via quantidade).
    """
    movimentacao = models.ForeignKey(
        Movimentacao,
        on_delete=models.CASCADE,
        related_name="itens"
    )
    ativo = models.ForeignKey(
        Ativo,
        on_delete=models.PROTECT,
        related_name="movimentacoes_participadas",
        verbose_name="Ativo"
    )
    ativo_substituto = models.ForeignKey(
        Ativo,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="trocas_realizadas",
        verbose_name="Ativo Substituto (Apenas para Trocas)",
        help_text="O ativo que substituiu o ativo principal (no caso de uma troca)."
    )
    quantidade = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantidade",
        help_text="Para acessórios sem serial, indica quantas unidades foram movimentadas."
    )

    class Meta:
        verbose_name = "Item de Movimentação"
        verbose_name_plural = "Itens de Movimentação"

    def __str__(self):
        if self.ativo_substituto:
            return f"TROCA: Sai {self.ativo_substituto.numero_serie} -> Entra {self.ativo.numero_serie}"
        if self.ativo.controla_serial:
            return str(self.ativo)
        return f"{self.ativo.modelo_equipamento} x{self.quantidade}"
