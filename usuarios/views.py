from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Aviso


@login_required
def home_geral(request):
    user = request.user

    # Validação baseada nos campos do modelo Colaborador
    # Setores liberados: 'COMERCIAL' ou 'DIRETORIA'
    # Cargos liberados como redundância/segurança: 'COMER', 'LIDER', 'DONO'
    pode_ver_comercial = user.is_superuser or (
        user.setor in ['COMERCIAL', 'DIRETORIA'] or
        user.cargo in ['COMER', 'LIDER', 'DONO']
    )

    # Avisos carregados do banco de dados — gerenciados pelo Django Admin
    avisos = Aviso.objects.filter(ativo=True).order_by('-data_publicacao')[:10]

    context = {
        'avisos': avisos,
        'pode_ver_comercial': pode_ver_comercial,
    }

    return render(request, 'usuarios/home_geral.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')

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