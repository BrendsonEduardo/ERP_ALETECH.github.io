# comercial/templatetags/filtros.py
"""
Filtros de template customizados para o módulo comercial.
Uso: {% load filtros %} no topo do template.
"""
from django import template

register = template.Library()


@register.filter(name='moeda_br')
def moeda_br(valor):
    """
    Formata um valor numérico no padrão monetário brasileiro.
    Exemplo: 1234567.89 → "R$ 1.234.567,89"
    """
    try:
        valor_float = float(valor)
        formatado = f"{valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatado}"
    except (TypeError, ValueError):
        return "R$ 0,00"
