import gspread
from google.oauth2.service_account import Credentials
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # Adicionado para exibir alertas na tela
from .models import Chamado

@login_required(login_url='login')
def painel_helpdesk(request):
    # Busca todos os chamados salvos ordenando pelos mais recentes
    chamados = Chamado.objects.all().order_by('-id')
    
    # Faz as contagens baseadas nos novos status oficiais do POP-001 (Item 2.4)
    total = chamados.count()
    abertos = chamados.filter(status='Aberto').count()
    
    # "Em Andamento" agora engloba Atendimento e Esperas operacionais conforme o POP
    andamento = chamados.filter(status__in=['Em Atendimento', 'Aguardando Usuário', 'Aguardando Terceiros']).count()
    
    # Finalizados engloba o status técnico (Resolvido) e o encerramento formal (Encerrado)
    finalizados = chamados.filter(status__in=['Resolvido', 'Encerrado']).count()
    
    # Empacota os dados para enviar para o HTML
    context = {
        'chamados': chamados,
        'total': total,
        'abertos': abertos,
        'andamento': andamento,
        'finalizados': finalizados,
    }
    
    return render(request, 'helpdesk/painel.html', context)


@login_required(login_url='login')
def novo_chamado(request):
    if request.method == 'POST':
        empresa = request.POST.get('empresa')
        solicitante = request.POST.get('solicitante')
        contato = request.POST.get('contato')
        forma_atendimento = request.POST.get('forma_atendimento')
        equipamento = request.POST.get('equipamento')
        problema = request.POST.get('problema')
        prioridade = request.POST.get('prioridade', 'Média')

        # Cria o chamado associando o usuário logado e os novos parâmetros
        Chamado.objects.create(
            empresa=empresa,
            solicitante=solicitante,
            contato=contato,
            forma_atendimento=forma_atendimento,
            equipamento=equipamento,
            problema=problema,
            prioridade=prioridade,
            tecnico=request.user,  
            nome_tecnico=request.user.get_full_name() or request.user.username,  
            status='Aberto'
        )
        return redirect('painel_helpdesk')
    
    return render(request, 'helpdesk/novo.html')
@login_required(login_url='login')
def atualizar_status(request, id):
    if request.method == 'POST':
        chamado = get_object_or_404(Chamado, id=id)
        
        novo_status = request.POST.get('status')
        comentario_texto = request.POST.get('comentario')
        
        # 1. Salva no banco de dados local imediatamente
        chamado.status = novo_status
        chamado.ultimo_comentario = comentario_texto
        chamado.tecnico = request.user
        chamado.nome_tecnico = request.user.get_full_name() or request.user.username
        chamado.save()

        # 2. 🔥 ATUALIZAÇÃO DIRETA E CIRÚRGICA PELA LINHA
        if chamado.id_integracao and chamado.id_integracao.startswith("LINHA_"):
            try:
                # Extrai o número da linha de dentro da string (ex: "LINHA_15" vira 15)
                linha_localizada = int(chamado.id_integracao.split("_")[1])
                
                scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                caminho_credenciais = r"D:\Meus projetos\erp_aletech\credenciais.json"
                id_da_planilha = "16rGSeEQ7I-qPI8NMrOl5fLDJ85xMumdCXmGWhzNr_Hk"
                
                creds = Credentials.from_service_account_file(caminho_credenciais, scopes=scopes)
                client = gspread.authorize(creds)
                planilha = client.open_by_key(id_da_planilha)
                aba = planilha.get_worksheet(0)
                
                # Atualiza diretamente na célula certa sem precisar ler nada antes!
                aba.update_cell(linha_localizada, 8, novo_status) # Coluna 8 (H)
                aba.update_cell(linha_localizada, 9, comentario_texto if comentario_texto else "") # Coluna 9 (I)
                
                messages.success(request, f"Sincronizado com a planilha com sucesso (Linha {linha_localizada})!")

            except Exception as e:
                print(f"❌ ERRO GOOGLE SHEETS DIRETO: {e}")
                messages.error(request, f"Erro na comunicação com o Google Sheets: {e}")

        return redirect('painel_helpdesk')
    return redirect('painel_helpdesk')


@login_required(login_url='login')
def deletar_chamado(request, id):
    if request.method == 'POST':
        chamado = get_object_or_404(Chamado, id=id)
        chamado.delete()
    return redirect('painel_helpdesk')
    

@login_required(login_url='login')
def detalhe_chamado(request, id):
    chamado = get_object_or_404(Chamado, id=id)
    
    context = {
        'chamado': chamado
    }
    return render(request, 'helpdesk/detalhe.html', context)