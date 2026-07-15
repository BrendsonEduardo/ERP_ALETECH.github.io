# inventario/forms.py
"""
ModelForms do módulo de Inventário.

Todos os widgets recebem classes Tailwind CSS via o método __init__
para garantir consistência visual em todo o módulo.
"""

from django import forms

from .models import Ativo, ModeloEquipamento

# ─── Classe de estilo padrão Tailwind ─────────────────────────────────────────
_INPUT_CLASS = (
    "w-full border border-gray-600 rounded-lg px-3 py-2 text-sm bg-gray-800 "
    "text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 "
    "focus:ring-purple-500 focus:border-transparent transition-all"
)
_SELECT_CLASS = (
    "w-full border border-gray-600 rounded-lg px-3 py-2 text-sm bg-gray-800 "
    "text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 "
    "focus:border-transparent transition-all"
)
_TEXTAREA_CLASS = (
    "w-full border border-gray-600 rounded-lg px-3 py-2 text-sm bg-gray-800 "
    "text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 "
    "focus:ring-purple-500 focus:border-transparent transition-all resize-y"
)


def _apply_tailwind(form: forms.ModelForm) -> None:
    """
    Itera sobre todos os campos de um form e injeta as classes
    Tailwind CSS de acordo com o tipo de widget.
    """
    for field_name, field in form.fields.items():
        widget = field.widget
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            widget.attrs.update({"class": _SELECT_CLASS})
        elif isinstance(widget, forms.Textarea):
            widget.attrs.update({"class": _TEXTAREA_CLASS, "rows": 3})
        else:
            widget.attrs.update({"class": _INPUT_CLASS})


class ModeloEquipamentoForm(forms.ModelForm):
    """Formulário para cadastro e edição de modelos no catálogo de hardware."""

    class Meta:
        model = ModeloEquipamento
        fields = ["marca", "modelo", "categoria", "descricao"]
        labels = {
            "marca": "Marca",
            "modelo": "Modelo / Linha",
            "categoria": "Categoria",
            "descricao": "Descrição / Especificações",
        }
        help_texts = {
            "descricao": "Processador, RAM, armazenamento, etc. (opcional)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_tailwind(self)
        self.fields["marca"].widget.attrs["placeholder"] = "Ex: Dell, Lenovo, HP"
        self.fields["modelo"].widget.attrs["placeholder"] = "Ex: Latitude 5420"
        self.fields["descricao"].widget.attrs["placeholder"] = (
            "Ex: Intel Core i5, 16GB RAM, SSD 512GB"
        )


class AtivoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de um Ativo físico.

    Os campos de alocação (cliente_atual, unidade, setor) são marcados como
    não obrigatórios no form — a validação condicional (obrigatório quando
    status=ALOCADO) é feita no método clean().
    """

    class Meta:
        model = Ativo
        fields = [
            "modelo_equipamento",
            "controla_serial",
            "numero_serie",
            "quantidade_estoque",
            "status",
            "cliente_atual",
            "unidade",
            "setor",
            "observacoes",
        ]
        labels = {
            "modelo_equipamento": "Modelo do Equipamento",
            "controla_serial": "Controla Nº de Série?",
            "numero_serie": "Número de Série (S/N)",
            "quantidade_estoque": "Quantidade em Estoque",
            "status": "Status Operacional",
            "cliente_atual": "Cliente Atual",
            "unidade": "Unidade",
            "setor": "Setor",
            "observacoes": "Observações",
        }
        help_texts = {
            "controla_serial": "Desmarque para acessórios sem serial (capas, fontes, berços).",
            "quantidade_estoque": "Apenas para itens sem serial. Informe a quantidade disponível.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_tailwind(self)

        # Placeholders
        self.fields["numero_serie"].widget.attrs["placeholder"] = (
            "Ex: DELL-SN-2024-00123"
        )
        self.fields["quantidade_estoque"].widget.attrs["placeholder"] = (
            "Ex: 50"
        )
        self.fields["unidade"].widget.attrs["placeholder"] = (
            "Ex: Matriz, Filial Manaus"
        )
        self.fields["setor"].widget.attrs["placeholder"] = "Ex: Financeiro, TI, RH"
        self.fields["observacoes"].widget.attrs["placeholder"] = (
            "Histórico técnico, defeitos conhecidos ou notas relevantes…"
        )

        # Campos opcionais no nível de form
        self.fields["cliente_atual"].required = False
        self.fields["unidade"].required = False
        self.fields["setor"].required = False
        self.fields["numero_serie"].required = False
        self.fields["quantidade_estoque"].required = False

        # Label amigável para o queryset do select de cliente
        self.fields["cliente_atual"].empty_label = "— Selecione um cliente —"

    def clean(self):
        """
        Validação condicional:
        - status = ALOCADO → cliente_atual obrigatório.
        - controla_serial = True → numero_serie obrigatório.
        - controla_serial = False → quantidade_estoque obrigatório.
        """
        cleaned = super().clean()
        status = cleaned.get("status")
        cliente = cleaned.get("cliente_atual")
        controla_serial = cleaned.get("controla_serial", True)
        numero_serie = cleaned.get("numero_serie")
        quantidade = cleaned.get("quantidade_estoque")

        if status == Ativo.Status.ALOCADO and not cliente:
            self.add_error(
                "cliente_atual",
                "É obrigatório informar o cliente quando o status é 'Alocado'.",
            )

        if controla_serial and not numero_serie:
            self.add_error(
                "numero_serie",
                "O Número de Série é obrigatório para itens com controle de serial.",
            )

        if not controla_serial and (quantidade is None or quantidade < 0):
            self.add_error(
                "quantidade_estoque",
                "Informe a quantidade em estoque para acessórios sem serial.",
            )

        return cleaned

