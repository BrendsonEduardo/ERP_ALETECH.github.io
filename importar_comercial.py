import os
import sys
import csv
from datetime import datetime

# 1. Configurar o ambiente do Django para permitir o uso dos Models fora do servidor ativo
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_aletech.settings')
django.setup()

# Buscando o modelo customizado (usuarios.Colaborador) dinamicamente
from django.contrib.auth import get_user_model
from comercial.models import Cliente, Oportunidade

def limpar_valor(valor_str):
    """Remove R$, pontos de milhar e troca vírgula por ponto para conversão em float."""
    if not valor_str or str(valor_str).strip() == 'nan' or str(valor_str).strip() == '':
        return 0.00
    try:
        limpo = valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
        return float(limpo)
    except ValueError:
        return 0.00

def converter_data(data_str):
    """Converte datas do formato DD/MM/AAAA ou DD/MM/AA para objeto date do Python."""
    if not data_str or str(data_str).strip() == 'nan' or str(data_str).strip() == '':
        return None
    try:
        return datetime.strptime(data_str.strip(), '%d/%m/%Y').date()
    except ValueError:
        try:
            return datetime.strptime(data_str.strip(), '%d/%m/%y').date()
        except ValueError:
            return None

def definir_estagio(row):
    """Varre as colunas booleanas do pipeline para determinar o estágio atual."""
    if row.get('PERDIDO') == 'TRUE':
        return 'Fechado_Perdeu'
    elif row.get('PEDIDO ENTREGUE') == 'TRUE' or row.get('PEDIDO DE COMPRA  RECEBIDO') == 'TRUE':
        return 'Fechado_Ganhou'
    elif row.get('NEGOCIAÇÃO') == 'TRUE':
        return 'Negociação'
    elif row.get('PROPOSTA ENVIADA') == 'TRUE':
        return 'Proposta'
    elif row.get('TESTE') == 'TRUE':
        return 'Qualificação'
    else:
        return 'Prospecção'

def importar_dados():
    # Obtém o modelo correto configurado no seu AUTH_USER_MODEL (usuarios.Colaborador)
    User = get_user_model()
    
    # Garante um usuário do comercial para o vínculo
    vendedor, _ = User.objects.get_or_create(username='comercial_import', defaults={'is_staff': True})
    
    print("=== PASSO 1: Importando Clientes Base ===")
    clientes_path = r"C:\Users\brendson.vasconcelos\Downloads\CONTROLE CLIENTES ANA - CONTROLE DE CLIENTES.csv"
    
    if os.path.exists(clientes_path):
        with open(clientes_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if 'EMPRESA' not in reader.fieldnames:
                f.seek(0)
                next(f)  # Ignora linha de título estilizada da planilha
                next(f)  # Ignora linha em branco
                reader = csv.DictReader(f)

            # CORRIGIDO: Adicionado enumerate para controlar o índice idx com segurança
            for idx, row in enumerate(reader):
                nome_empresa = row.get('EMPRESA')
                if not nome_empresa or nome_empresa.strip() == '':
                    continue
                
                # CORREÇÃO UNIQUE CONSTRAINT: Se não houver CNPJ, gera um identificador único fictício baseado no index
                cnpj_original = row.get('CNPJ', '').strip()
                if not cnpj_original:
                    cnpj_final = f"SEM-CNPJ-{idx:05d}"
                else:
                    cnpj_final = cnpj_original
                
                cliente, created = Cliente.objects.get_or_create(
                    nome_fantasia=nome_empresa.strip(),
                    defaults={
                        'cnpj_cpf': cnpj_final,
                        'tipo': 'PJ',
                        'email': row.get('EMAIL', '').strip() or 'sem_email@aletech.com',
                        'telefone': row.get('TELEFONE', '').strip() or '(00) 00000-0000',
                        'endereco': row.get('UF/CIDADE', '').strip()
                    }
                )
                if created:
                    print(f"✅ Cliente Cadastrado: {cliente.nome_fantasia}")
    else:
        print(f"❌ Arquivo {clientes_path} não encontrado.")

    print("\n=== PASSO 2: Importando Oportunidades do Pipeline ===")
    pipeline_path = r"C:\Users\brendson.vasconcelos\Downloads\CONTROLE CLIENTES ANA - ATUALIZAÇÃO DIÁRIA.csv"
    
    if os.path.exists(pipeline_path):
        with open(pipeline_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if 'CLIENTE' not in reader.fieldnames:
                f.seek(0)
                next(f)
                reader = csv.DictReader(f)

            # CORRIGIDO: Adicionado enumerate para controlar o índice idx com segurança
            for idx, row in enumerate(reader):
                nome_cliente = row.get('CLIENTE')
                if not nome_cliente or nome_cliente.strip() == '' or nome_cliente == 'CLIENTE':
                    continue
                
                try:
                    cliente_instancia = Cliente.objects.get(nome_fantasia=nome_cliente.strip())
                except Cliente.DoesNotExist:
                    # Se o cliente não existia no cadastro base, cria com CNPJ temporário único
                    cliente_instancia = Cliente.objects.create(
                        nome_fantasia=nome_cliente.strip(),
                        cnpj_cpf=f"N-CAD-{idx:05d}",
                        email='importado@aletech.com',
                        telefone='(00) 00000-0000'
                    )

                estagio_calculado = definir_estagio(row)
                historico_texto = row.get('DATA+ ATUALIZAÇÃO', '').strip()
                interesse_produto = row.get('MOSTROU INTERESSE', '').strip()
                titulo_lead = f"Demanda - {interesse_produto}" if interesse_produto and interesse_produto != 'FALSE' else "Oportunidade Comercial"

                Oportunidade.objects.create(
                    titulo=titulo_lead,
                    cliente=cliente_instancia,
                    vendedor=vendedor,
                    valor_estimado=0.00,  # Vinculado no Passo 3
                    estagio=estagio_calculado,
                    data_fechamento_prevista=datetime.now().date(),
                    descricao=f"Histórico Planilha: {historico_texto}" if historico_texto else "Sem observações iniciais."
                )
                print(f"🚀 Lead Criado: {cliente_instancia.nome_fantasia} -> Estágio: {estagio_calculado}")
    else:
        print(f"❌ Arquivo {pipeline_path} não encontrado.")

    print("\n=== PASSO 3: Cruzando e Atualizando Valores de Propostas ===")
    propostas_path = r"C:\Users\brendson.vasconcelos\Downloads\CONTROLE CLIENTES ANA - PROPOSTAS.csv"
    
    if os.path.exists(propostas_path):
        with open(propostas_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if 'CLIENTE' not in reader.fieldnames:
                f.seek(0)
                next(f)
                next(f)
                reader = csv.DictReader(f)

            for row in reader:
                nome_cliente = row.get('CLIENTE')
                if not nome_cliente or nome_cliente.strip() == '':
                    continue
                
                valor_proposta = limpar_valor(row.get('VALOR'))
                codigo_proposta = row.get('PROPOSTA', '').strip()
                
                oportunidades = Oportunidade.objects.filter(cliente__nome_fantasia=nome_cliente.strip())
                if oportunidades.exists():
                    for op in oportunidades:
                        op.valor_estimado = valor_proposta
                        op.titulo = f"Proposta {codigo_proposta} - " + op.titulo if codigo_proposta else op.titulo
                        op.save()
                    print(f"💰 Valores Atualizados: {nome_cliente.strip()} -> R$ {valor_proposta:.2f}")
    else:
        print(f"⚠️ Arquivo {propostas_path} não encontrado. Valores ficaram zerados.")

    print("\n=== Carga de dados concluída com sucesso! ===")

if __name__ == '__main__':
    importar_dados()