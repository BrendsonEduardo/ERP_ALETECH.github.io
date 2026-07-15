import os
import django
import shutil

# Configura o ambiente do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_aletech.settings')
django.setup()

from inventario.models import Movimentacao, MovimentacaoItem, Ativo
from django.db import connection
from django.conf import settings

# Conta quantas serão apagadas
qtd = Movimentacao.objects.count()

# 1. Apaga tudo (isso apaga MovimentacaoItem em cascata também, mas podemos forçar)
MovimentacaoItem.objects.all().delete()
Movimentacao.objects.all().delete()

# 2. Reseta o status dos Ativos para ESTOQUE
Ativos_resetados = Ativo.objects.exclude(status=Ativo.Status.ESTOQUE).update(status=Ativo.Status.ESTOQUE, cliente_atual=None)

# 3. Zera as sequencias do SQLite
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='inventario_movimentacao'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='inventario_movimentacaoitem'")

# 4. Limpa a pasta de PDFs
cautelas_dir = os.path.join(settings.MEDIA_ROOT, 'cautelas')
if os.path.exists(cautelas_dir):
    shutil.rmtree(cautelas_dir)
    os.makedirs(cautelas_dir)

print(f'Pronto! {qtd} movimentacoes apagadas e {Ativos_resetados} ativos devolvidos ao estoque. Proxima cautela sera a #1.')
