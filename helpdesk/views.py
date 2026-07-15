import gspread
from google.oauth2.service_account import Credentials
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Chamado


@login_required(login_url='login')
def painel_helpdesk(request):
    # QuerySet completo — usado para KPIs (contagens globais, sem paginar)
    chamados_qs = Chamado.objects.all().order_by('-id')

    # ── KPIs (contagens no QuerySet completo, não na página atual) ────────
    total     = chamados_qs.count()
    abertos   = chamados_qs.filter(status='Aberto').count()
    andamento = chamados_qs.filter(
        status__in=['Em Atendimento', 'Aguardando Usuário', 'Aguardando Terceiros']
    ).count()
    finalizados = chamados_qs.filter(status__in=['Resolvido', 'Encerrado']).count()

    # ── SLA Médio (somente Encerrados com valor válido) ───────────────────
    encerrados = chamados_qs.filter(status='Encerrado')
    total_segundos = 0
    qtd_com_sla = 0

    for chamado in encerrados:
        if chamado.sla:
            partes = chamado.sla.split(':')
            if len(partes) == 3:
                try:
                    h, m, s = int(partes[0]), int(partes[1]), int(partes[2])
                    total_segundos += (h * 3600) + (m * 60) + s
                    qtd_com_sla += 1
                except ValueError:
                    pass

    if qtd_com_sla > 0:
        media_segundos = total_segundos // qtd_com_sla
        h = media_segundos // 3600
        m = (media_segundos % 3600) // 60
        s = media_segundos % 60
        sla_medio = f"{h:02d}:{m:02d}:{s:02d}"
    else:
        sla_medio = "--:--:--"

    # ── Paginação — 15 registros por página ───────────────────────────────
    paginator   = Paginator(chamados_qs, 15)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)   # get_page trata valores inválidos/out-of-range sem lançar exceção

    context = {
        'page_obj'   : page_obj,       # substitui 'chamados' no template
        'paginator'  : paginator,
        'total'      : total,
        'abertos'    : abertos,
        'andamento'  : andamento,
        'finalizados': finalizados,
        'sla_medio'  : sla_medio,
    }

    return render(request, 'helpdesk/painel.html', context)



@login_required(login_url='login')
def novo_chamado(request):
    if request.method == 'POST':
        Chamado.objects.create(
            empresa=request.POST.get('empresa'),
            solicitante=request.POST.get('solicitante'),
            contato=request.POST.get('contato'),
            forma_atendimento=request.POST.get('forma_atendimento'),
            equipamento=request.POST.get('equipamento'),
            problema=request.POST.get('problema'),
            prioridade=request.POST.get('prioridade', 'Média'),
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

        # 2. Atualização direta e cirúrgica na planilha pela linha
        if chamado.id_integracao and chamado.id_integracao.startswith("LINHA_"):
            try:
                linha_localizada = int(chamado.id_integracao.split("_")[1])

                scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

                # Credenciais lidas das settings (que leem do .env) — sem caminhos hardcoded
                caminho_credenciais = str(settings.GOOGLE_SHEETS_CREDENTIALS_PATH)
                id_da_planilha = settings.GOOGLE_SHEETS_PLANILHA_ID

                creds = Credentials.from_service_account_file(caminho_credenciais, scopes=scopes)
                client = gspread.authorize(creds)
                planilha = client.open_by_key(id_da_planilha)
                aba = planilha.get_worksheet(0)

                aba.update_cell(linha_localizada, 8, novo_status)
                aba.update_cell(linha_localizada, 9, comentario_texto if comentario_texto else "")

                messages.success(request, f"Sincronizado com a planilha com sucesso (Linha {linha_localizada})!")

            except Exception as e:
                print(f"❌ ERRO GOOGLE SHEETS: {e}")
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
    return render(request, 'helpdesk/detalhe.html', {'chamado': chamado})