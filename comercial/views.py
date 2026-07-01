# comercial/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from datetime import datetime  # CORRIGIDO: Sintaxe correta de importação
from .models import Cliente, Oportunidade, TesteOportunidade, EquipamentoTeste

# ==========================================
# TRAVAS DE SEGURANÇA E AUXILIARES
# ==========================================

def verificar_permissao_vendedor(user, oportunidade):
    """
    TRAVA DE SEGURANÇA: Apenas superusuários ou o grupo 'Gerência' têm visão global.
    Vendedores comuns (Ana, Laura, etc.) só gerenciam suas próprias oportunidades.
    """
    if user.is_superuser or user.groups.filter(name='Gerência').exists():
        return True
    return oportunidade.vendedor == user

def verificar_permissao_cliente(user, cliente):
    """Garante que um vendedor só mexa em clientes da sua carteira ou das suas oportunidades."""
    if user.is_superuser or user.groups.filter(name='Gerência').exists():
        return True
    return cliente.vendedor == user or cliente.oportunidades.filter(vendedor=user).exists()

def obter_clientes_permitidos(user):
    """
    Retorna apenas os clientes que o utilizador tem permissão para visualizar.
    Se for Admin/Gerência, vê todos. Se for vendedor, vê os clientes da sua carteira
    OU clientes associados às suas oportunidades.
    """
    if user.is_superuser or user.groups.filter(name='Gerência').exists():
        return Cliente.objects.all().order_by('nome_fantasia')
    
    return Cliente.objects.filter(
        Q(vendedor=user) | Q(oportunidades__vendedor=user)
    ).distinct().order_by('nome_fantasia')

def capturar_datas_filtro(request):
    """Função auxiliar para padronizar a captura de datas em todas as views."""
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')
    hoje = timezone.now().date()
    
    if data_inicio_str and data_fim_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            data_inicio = hoje.replace(day=1)
            data_fim = hoje
    else:
        data_inicio = hoje.replace(day=1)
        data_fim = hoje
    return data_inicio, data_fim


# ==========================================
# VIEWS DO PROCESSO COMERCIAL
# ==========================================

@login_required(login_url='login')
def painel_comercial(request):
    user = request.user
    data_inicio, data_fim = capturar_datas_filtro(request)
    
    # Aplicando o filtro de tempo também no Kanban para performance e consistência
    if user.is_superuser or user.groups.filter(name='Gerência').exists():
        base_oportunidades = Oportunidade.objects.filter(
            ultima_atualizacao__date__range=[data_inicio, data_fim]
        ).select_related('cliente').prefetch_related('teste')
    else:
        base_oportunidades = Oportunidade.objects.filter(
            vendedor=user,
            ultima_atualizacao__date__range=[data_inicio, data_fim]
        ).select_related('cliente').prefetch_related('teste')
        
    oportunidades = list(base_oportunidades.order_by('-ultima_atualizacao'))
    
    # HIGIENIZAÇÃO: Remove espaços invisíveis
    for op in oportunidades:
        if op.estagio:
            op.estagio = str(op.estagio).strip()
    
    total_em_negociacao = sum(op.valor_estimado for op in oportunidades if op.estagio in ['Prospecção', 'Qualificação', 'Proposta', 'Negociação', 'Em_Teste'])
    total_ganho = sum(op.valor_estimado for op in oportunidades if op.estagio == 'Fechado_Ganhou')
    total_leads = len(oportunidades)
    propostas_abertas = sum(1 for op in oportunidades if op.estagio == 'Proposta')

    context = {
        'prospeccao': [op for op in oportunidades if op.estagio == 'Prospecção'],
        'em_teste': [op for op in oportunidades if op.estagio in ['Em_Teste', 'Em Teste']],
        'qualificacao': [op for op in oportunidades if op.estagio == 'Qualificação'],
        'proposta': [op for op in oportunidades if op.estagio == 'Proposta'],
        'negociacao': [op for op in oportunidades if op.estagio == 'Negociação'],
        'ganhou': [op for op in oportunidades if op.estagio == 'Fechado_Ganhou'],
        'perdeu': [op for op in oportunidades if op.estagio == 'Fechado_Perdeu'],
        'total_em_negociacao': total_em_negociacao,
        'total_ganho': total_ganho,
        'total_leads': total_leads,
        'propostas_abertas': propostas_abertas,
        'data_inicio': data_inicio.strftime('%Y-%m-%d'),
        'data_fim': data_fim.strftime('%Y-%m-%d'),
    }
    return render(request, 'comercial/painel_comercial.html', context)


@csrf_exempt
@login_required(login_url='login')
def atualizar_estagio_kanban(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            oportunidade_id = data.get('id')
            id_html = str(data.get('estagio', '')).strip().upper()
            
            MAPA_ESTAGIOS = {
                'PROSPECÇÃO': 'Prospecção', 'PROSPECÇAO': 'Prospecção', 'PROSPECCAO': 'Prospecção',
                'EM TESTE': 'Em_Teste', 'EM_TESTE': 'Em_Teste',
                'QUALIFICAÇÃO': 'Qualificação', 'QUALIFICAÇAO': 'Qualificação', 'QUALIFICACAO': 'Qualificação',
                'PROPOSTA': 'Proposta',
                'NEGOCIAÇÃO': 'Negociação', 'NEGOCIAÇAO': 'Negociação', 'NEGOCIACAO': 'Negociação',
                'FECHADO_GANHOU': 'Fechado_Ganhou', 'FECHADO GANHOU': 'Fechado_Ganhou',
                'FECHADO_PERDEU': 'Fechado_Perdeu', 'FECHADO PERDEU': 'Fechado_Perdeu',
            }
            
            novo_estagio_db = MAPA_ESTAGIOS.get(id_html)
            
            if not novo_estagio_db:
                return JsonResponse({'status': 'error', 'message': f'Estágio/Coluna inválida: {id_html}'}, status=400)
                
            oportunidade = get_object_or_404(Oportunidade, id=oportunidade_id)
            
            if not verificar_permissao_vendedor(request.user, oportunidade):
                return JsonResponse({'status': 'error', 'message': 'Permissão negada para alterar esta oportunidade.'}, status=403)

            oportunidade.estagio = novo_estagio_db
            oportunidade.save()
            return JsonResponse({'status': 'success', 'message': 'Estágio updated com sucesso!'})
            
        except (ValueError, KeyError, json.JSONDecodeError):
            return JsonResponse({'status': 'error', 'message': 'Requisição malformada.'}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Método não permitido.'}, status=405)


@login_required(login_url='login')
def novo_cliente(request):
    if request.method == 'POST':
        Cliente.objects.create(
            nome_fantasia=request.POST.get('nome_fantasia'),
            razao_social=request.POST.get('razao_social'),
            cnpj_cpf=request.POST.get('cnpj_cpf'),
            tipo=request.POST.get('tipo', 'PJ'),
            email=request.POST.get('email'),
            telefone=request.POST.get('telefone'),
            endereco=request.POST.get('endereco'),
            
            # 🔥 SALVA O CAMPO DO FEEDBACK COMERCIAL NO CADASTRO DE NOVOS CLIENTES
            contato_responsavel=request.POST.get('contato_responsavel'),
            
            vendedor=request.user,
            ficha_cadastral=request.FILES.get('ficha_cadastral')
        )
        messages.success(request, "Cliente registrado com sucesso na sua carteira!")
        return redirect('nova_oportunidade')
    return render(request, 'comercial/novo_cliente.html')

@login_required(login_url='login')
def nova_oportunidade(request):
    if request.method == 'POST':
        clientes_permitidos = obter_clientes_permitidos(request.user)
        cliente_instancia = get_object_or_404(clientes_permitidos, id=request.POST.get('cliente'))
        
        valor_cru = request.POST.get('valor_estimado', '0.00')
        valor_final = float(valor_cru) if valor_cru else 0.00

        Oportunidade.objects.create(
            titulo=request.POST.get('titulo'),
            cliente=cliente_instancia,
            vendedor=request.user,
            valor_estimado=valor_final,
            estagio=request.POST.get('estagio', 'Prospecção').strip(),
            data_fechamento_prevista=request.POST.get('data_fechamento_prevista'),
            descricao=request.POST.get('descricao'),
            contracto_proposta=request.FILES.get('contrato_proposta')
        )
        return redirect('painel_comercial')

    clientes = obter_clientes_permitidos(request.user)
    return render(request, 'comercial/nova_oportunidade.html', {'clientes': clientes})


@login_required(login_url='login')
def detalhe_proposta(request, id):
    op = get_object_or_404(
        Oportunidade.objects.select_related('cliente').prefetch_related('teste__equipamentos'), 
        id=id
    )
    if not verificar_permissao_vendedor(request.user, op):
        return HttpResponseForbidden("Você não tem permissão para visualizar esta oportunidade.")
        
    return render(request, 'comercial/detalhe_proposta.html', {'op': op})


@login_required(login_url='login')
def editar_proposta(request, id):
    op = get_object_or_404(Oportunidade, id=id)
    
    if not verificar_permissao_vendedor(request.user, op):
        return HttpResponseForbidden("Você não tem permissão para editar esta oportunidade.")
    
    if request.method == 'POST':
        op.titulo = request.POST.get('titulo')
        
        valor_cru = request.POST.get('valor_estimado')
        if valor_cru:
            op.valor_estimado = float(valor_cru.replace('.', '').replace(',', '.')) if ',' in valor_cru else float(valor_cru)
            
        op.estagio = request.POST.get('estagio').strip()
        op.descricao = request.POST.get('descricao')
        
        if request.FILES.get('contrato_proposta'):
            op.contracto_proposta = request.FILES.get('contrato_proposta')
        
        cliente_id = request.POST.get('cliente')
        if cliente_id:
            clientes_permitidos = obter_clientes_permitidos(request.user)
            op.cliente = get_object_or_404(clientes_permitidos, id=cliente_id)
            
        op.save()
        return redirect('painel_comercial')
        
    clientes = obter_clientes_permitidos(request.user)
    return render(request, 'comercial/editar_proposta.html', {'op': op, 'clientes': clientes})


@login_required(login_url='login')
def gerenciar_teste(request, op_id):
    oportunidade = get_object_or_404(Oportunidade, id=op_id)
    if not verificar_permissao_vendedor(request.user, oportunidade):
        return HttpResponseForbidden("Você não tem permissão para gerenciar testes nesta oportunidade.")
        
    teste = getattr(oportunidade, 'teste', None)

    if request.method == "POST":
        setor_projeto = request.POST.get("setor_projeto")
        data_envio = request.POST.get("data_envio")
        dias_duracao = request.POST.get("dias_duracao")
        observacoes = request.POST.get("observacoes")

        marcas = request.POST.getlist("marca[]")
        modelos = request.POST.getlist("modelo[]")
        quantidades = request.POST.getlist("quantidade[]")
        numeros_serie = request.POST.getlist("numero_serie[]")

        if not marcas or len(marcas) == 0:
            messages.error(request, "Adicione pelo menos um equipamento para salvar o controle de teste.")
        else:
            try:
                with transaction.atomic():
                    if not teste:
                        teste = TesteOportunidade(oportunidade=oportunidade)
                    
                    teste.setor_projeto = setor_projeto
                    teste.data_envio = data_envio
                    teste.dias_duracao = int(dias_duracao) if dias_duracao else 0
                    teste.observacoes = observacoes
                    teste.save()

                    teste.equipamentos.all().delete()

                    for i in range(len(marcas)):
                        if marcas[i] and modelos[i] and numeros_serie[i]:
                            EquipamentoTeste.objects.create(
                                teste=teste,
                                marca=marcas[i],
                                modelo=modelos[i],
                                quantidade=int(quantidades[i]) if quantidades[i] else 1,
                                numero_serie=numeros_serie[i].strip()
                            )
                    
                messages.success(request, "Controle de testes atualizado com sucesso!")
                return redirect('detalhe_proposta', id=oportunidade.id)
                
            except Exception as e:
                messages.error(request, f"Erro operacional ao salvar equipamentos: {str(e)}")

    return render(request, "comercial/gerenciar_teste.html", {"op": oportunidade, "teste": teste})


# ==========================================
# DASHBOARDS E RELATÓRIOS
# ==========================================

@login_required(login_url='login')
def comercial_dashboard(request):
    user = request.user
    data_inicio, data_fim = capturar_datas_filtro(request)
    
    # Dashboard filtrado temporalmente
    if user.is_superuser or user.groups.filter(name='Gerência').exists():
        base_oportunidades = Oportunidade.objects.filter(
            ultima_atualizacao__date__range=[data_inicio, data_fim]
        ).select_related('cliente')
    else:
        base_oportunidades = Oportunidade.objects.filter(
            vendedor=user,
            ultima_atualizacao__date__range=[data_inicio, data_fim]
        ).select_related('cliente')
        
    oportunidades = list(base_oportunidades)
    
    total_leads = len(oportunidades)
    ganhas = [op for op in oportunidades if op.estagio == 'Fechado_Ganhou']
    perdidas = [op for op in oportunidades if op.estagio == 'Fechado_Perdeu']
    em_negociacao = [op for op in oportunidades if op.estagio in ['Prospecção', 'Qualificação', 'Proposta', 'Negociação', 'Em_Teste']]
    
    total_ganho = sum(op.valor_estimado for op in ganhas)
    total_em_negociacao = sum(op.valor_estimado for op in em_negociacao)
    
    total_finalizadas = len(ganhas) + len(perdidas)
    taxa_conversao = round((len(ganhas) / total_finalizadas) * 100, 1) if total_finalizadas > 0 else 0.0

    context = {
        'total_leads': total_leads,
        'total_ganho': total_ganho,
        'total_em_negociacao': total_em_negociacao,
        'taxa_conversao': taxa_conversao,
        'qtd_ganhas': len(ganhas),
        'qtd_perdidas': len(perdidas),
        'qtd_negociacao': len(em_negociacao),
        'data_inicio': data_inicio.strftime('%Y-%m-%d'),
        'data_fim': data_fim.strftime('%Y-%m-%d'),
    }
    return render(request, 'comercial/dashboard.html', context)


@login_required(login_url='login')
def comercial_clientes_lista(request):
    clientes = obter_clientes_permitidos(request.user)
    return render(request, 'comercial/clientes_lista.html', {'clientes': clientes})


@login_required(login_url='login')
def central_relatorios(request):
    user = request.user
    data_inicio, data_fim = capturar_datas_filtro(request)
    tipo_relatorio = request.GET.get('tipo_relatorio', 'geral')

    if user.is_superuser or user.groups.filter(name='Gerência').exists():
        base_oportunidades = Oportunidade.objects.filter(
            ultima_atualizacao__date__range=[data_inicio, data_fim]
        ).select_related('cliente', 'vendedor')
    else:
        base_oportunidades = Oportunidade.objects.filter(
            vendedor=user,
            ultima_atualizacao__date__range=[data_inicio, data_fim]
        ).select_related('cliente')

    oportunidades = list(base_oportunidades)
    
    # Cálculos usando a sua lógica de estágios
    total_clientes = len(set(op.cliente_id for op in oportunidades if op.cliente_id))
    propostas_abertas = sum(1 for op in oportunidades if op.estagio not in ['Fechado_Ganhou', 'Fechado_Perdeu'])
    propostas_ganhas = sum(1 for op in oportunidades if op.estagio == 'Fechado_Ganhou')
    receita_total_valor = sum(op.valor_estimado for op in oportunidades if op.estagio == 'Fechado_Ganhou')
    
    # Formatação de moeda para o padrão brasileiro (R$)
    receita_total = f"{receita_total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    context = {
        'data_inicio': data_inicio.strftime('%Y-%m-%d'),
        'data_fim': data_fim.strftime('%Y-%m-%d'),
        'tipo_relatorio': tipo_relatorio,
        'total_clientes': total_clientes,
        'propostas_abertas': propostas_abertas,
        'propostas_ganhas': propostas_ganhas,
        'receita_total': receita_total,
    }
    return render(request, 'comercial/central_relatorios.html', context)


@login_required(login_url='login')
def exportar_relatorio_clientes(request):
    user = request.user
    data_inicio, data_fim = capturar_datas_filtro(request)
    tipo_relatorio = request.GET.get('tipo_relatorio', 'geral')

    # Busca a base de oportunidades do período para calcular os cards da impressão também!
    if user.is_superuser or user.groups.filter(name='Gerência').exists():
        base_oportunidades = Oportunidade.objects.filter(
            ultima_atualizacao__date__range=[data_inicio, data_fim]
        )
        clientes = Cliente.objects.filter(
            oportunidades__ultima_atualizacao__date__range=[data_inicio, data_fim]
        ).distinct().order_by('nome_fantasia')
    else:
        base_oportunidades = Oportunidade.objects.filter(
            vendedor=user,
            ultima_atualizacao__date__range=[data_inicio, data_fim]
        )
        clientes = Cliente.objects.filter(
            Q(vendedor=user) | Q(oportunidades__vendedor=user),
            oportunidades__ultima_atualizacao__date__range=[data_inicio, data_fim]
        ).distinct().order_by('nome_fantasia')

    oportunidades = list(base_oportunidades)
    total_clientes = clientes.count()
    propostas_abertas = sum(1 for op in oportunidades if op.estagio not in ['Fechado_Ganhou', 'Fechado_Perdeu'])
    propostas_ganhas = sum(1 for op in oportunidades if op.estagio == 'Fechado_Ganhou')
    receita_total_valor = sum(op.valor_estimado for op in oportunidades if op.estagio == 'Fechado_Ganhou')
    receita_total = f"{receita_total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    context = {
        'clientes': clientes,
        'data_inicio': data_inicio.strftime('%d/%m/%Y'),
        'data_fim': data_fim.strftime('%d/%m/%Y'),
        'tipo_relatorio': tipo_relatorio,
        'total_clientes': total_clientes,
        'propostas_abertas': propostas_abertas,
        'propostas_ganhas': propostas_ganhas,
        'receita_total': receita_total,
    }
    return render(request, 'comercial/relatorio_impressao.html', context)
# ==========================================
# MODIFICAÇÃO DE ENTIDADES (CLIENTE)
# ==========================================

@login_required(login_url='login')
def editar_cliente(request, id):  # <-- AJUSTE TAMBÉM A VIEW DE EDIÇÃO (A DO SEU PRINT)
    cliente = get_object_or_404(Cliente, id=id)
    
    if request.method == 'POST':
        cliente.nome_fantasia = request.POST.get('nome_fantasia')
        cliente.razao_social = request.POST.get('razao_social')
        cliente.cnpj_cpf = request.POST.get('cnpj_cpf')
        cliente.tipo = request.POST.get('tipo', 'PJ')
        cliente.email = request.POST.get('email')
        cliente.telefone = request.POST.get('telefone')
        cliente.endereco = request.POST.get('endereco')
        
        # 🔥 SALVA O NOVO CAMPO QUANDO EDITAREM O PERFIL EXISTENTE
        cliente.contato_responsavel = request.POST.get('contato_responsavel')
        
        if request.FILES.get('ficha_cadastral'):
            cliente.ficha_cadastral = request.FILES.get('ficha_cadastral')
            
        cliente.save()
        messages.success(request, "Perfil do cliente atualizado com sucesso!")
        return redirect('lista_clientes')  # ajuste para a sua rota de retorno
        
    return render(request, 'comercial/editar_cliente.html', {'cliente': cliente})

@login_required(login_url='login')
def excluir_cliente(request, id):
    if not (request.user.is_superuser or request.user.groups.filter(name='Gerência').exists()):
        return HttpResponseForbidden("Você não tem permissão administrativa para excluir clientes.")
        
    cliente = get_object_or_404(Cliente, id=id)
    nome_cliente = cliente.nome_fantasia
    
    try:
        cliente.delete()
        messages.success(request, f"Cliente '{nome_cliente}' excluído permanentemente com sucesso!")
    except Exception:
        messages.error(request, "Não foi possível excluir o cliente pois ele possui propostas ou históricos ativos associados no banco de dados.")

    return redirect('comercial_clientes_lista')