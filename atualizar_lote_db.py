import os
import django
from django.db import transaction

# Configura o ambiente do Django (Certifique-se de estar na raiz do projeto)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_aletech.settings')
django.setup()

from comercial.models import Cliente
from inventario.models import Ativo

# A lista exata fornecida
LISTA_SNS = [
    "2423110479", "2100710602", "2208310336", "2100710703", "2208310304",
    "2100710466", "2100710467", "2100710451", "2100710488", "2100710289",
    "2100710201", "2100710252", "2100710569", "2100710448", "2208310245",
    "2100710249", "2100710686", "2100710614", "2100710475", "2208310354",
    "2100710443", "2100710412", "2100710608", "2021010123", "2131310516",
    "2229510072", "2100710406", "2100710471", "2100710606", "2100710391",
    "2229410335", "2100710665", "2100710651", "2100710268", "2100710496",
    "2208310370", "2131310527", "2208310414", "2100710489", "2131310524",
    "2100710202", "2206110202", "2208310423", "2021010052", "2100710258",
    "2021010102", "2100710567", "2100710251", "2208310361", "2100710428",
    "2100710253", "2100710648", "2100710426", "2100710429", "2208310328",
    "2100710583", "2208310343", "2107920220", "2107210632", "2304110106",
    "2423310127", "2221910582", "2113310694", "2221910562", "2221910604",
    "2304110196", "2107210616", "2423310064", "2107210634", "2221910609",
    "2107210655", "2107210637", "11J201002094", "11J184302811"
]

def alocar_lote():
    # 1. ENCONTRAR O CLIENTE
    clientes = Cliente.objects.filter(nome_fantasia__icontains="SUPERMERCADOS DB")
    
    if not clientes.exists():
        raise ValueError(
            "\n[ERRO] Cliente 'SUPERMERCADOS DB' não encontrado. "
            "Por favor, verifique se o nome exato foi cadastrado no sistema, pois o cadastro "
            "de cliente exige CNPJ."
        )
        
    cliente = clientes.first()
    print(f"[INFO] Cliente alvo localizado: {cliente.nome_fantasia} (ID: {cliente.pk})")
    
    encontrados = 0
    nao_encontrados = []

    # 2. ATUALIZAR OS ATIVOS DE FORMA ATÔMICA
    # O transaction.atomic() garante que se der erro crítico, nada será salvo parcialmente.
    with transaction.atomic():
        for sn in LISTA_SNS:
            try:
                # select_for_update evita problemas se outro usuário estiver editando o ativo agora
                ativo = Ativo.objects.select_for_update().get(numero_serie=sn)
                
                # Atribui o Choice correto do model (ALOCADO)
                ativo.status = Ativo.Status.ALOCADO
                ativo.cliente_atual = cliente
                ativo.save()
                
                encontrados += 1
            except Ativo.DoesNotExist:
                nao_encontrados.append(sn)

    # 3. RETORNO / LOG
    print("\n" + "="*40)
    print("--- RESUMO DA OPERACAO ---")
    print(f"Total de itens na lista: {len(LISTA_SNS)}")
    print(f"Atualizados com sucesso: {encontrados}")
    
    if nao_encontrados:
        print(f"\nATENCAO: {len(nao_encontrados)} numeros de serie nao foram encontrados no banco de dados:")
        for sn in nao_encontrados:
            print(f"  - {sn}")
    else:
        print("\nTodos os ativos da lista foram encontrados e alocados com sucesso!")
    print("="*40 + "\n")

if __name__ == "__main__":
    alocar_lote()
