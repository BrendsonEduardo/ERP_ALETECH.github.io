from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def home_geral(request):
    user = request.user  # Este objeto já é uma instância do seu modelo Colaborador!
    
    # AJUSTE: Validação baseada estritamente nos campos do modelo Colaborador
    # Setores liberados: 'COMERCIAL' ou 'DIRETORIA'
    # Cargos liberados como redundância/segurança: 'COMER', 'LIDER', 'DONO'
    pode_ver_comercial = user.is_superuser or (
        user.setor in ['COMERCIAL', 'DIRETORIA'] or 
        user.cargo in ['COMER', 'LIDER', 'DONO']
    )

    avisos = [
        {
            "titulo": "⚠️ Atualização do Sistema (POP-001)",
            "conteudo": "Implementado o novo fluxo obrigatório de justificativas ao alterar o status dos chamados técnicos.",
            "tipo": "urgente",
            "data": "16/06/2026"
        },
        {
            "titulo": "🚀 Meta Comercial Batida",
            "conteudo": "Parabéns à equipe comercial! Atingimos 100% da meta de novos contratos desta quinzena.",
            "tipo": "sucesso",
            "data": "15/06/2026"
        },
        {
            "titulo": "📅 Manutenção Programada",
            "conteudo": "O servidor passará por backup geral no próximo domingo às 02:00h.",
            "tipo": "info",
            "data": "14/06/2026"
        }
    ]
    
    context = {
        'avisos': avisos,
        'pode_ver_comercial': pode_ver_comercial,
    }
    
    return render(request, 'usuarios/home_geral.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')  # Se já estiver logado, vai direto pro painel

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
            else:
                messages.error(request, "Usuário ou senha inválidos.")
        else:
            messages.error(request, "Usuário ou senha inválidos.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'usuarios/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')