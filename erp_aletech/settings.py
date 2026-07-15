"""
Django settings for erp_aletech project.
"""

from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================
# SEGURANÇA — Configurações lidas do arquivo .env
# NUNCA coloque valores sensíveis diretamente aqui!
# =============================================================

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default=' 127.0.0.1, localhost', cast=Csv())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Aplicativos locais
    'helpdesk',
    'usuarios',
    'comercial',
    'inventario',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'erp_aletech.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Busca a pasta global 'templates' na raiz do projeto
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'erp_aletech.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.x/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.x/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization — Português / Fuso Horário local
# https://docs.djangoproject.com/en/5.x/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Manaus'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Custom User Model
AUTH_USER_MODEL = 'usuarios.Colaborador'

# Autenticação e Redirecionamentos de Sessão
LOGIN_URL = 'login'           # Se o usuário não estiver logado, vai para cá
LOGIN_REDIRECT_URL = '/'      # Para onde ele vai após logar com sucesso
LOGOUT_REDIRECT_URL = 'login' # Para onde ele vai após deslogar

# Arquivos de mídia (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================
# INTEGRAÇÕES EXTERNAS — Lidas do .env
# =============================================================

# Google Sheets — Integração com Helpdesk
# O caminho é relativo à BASE_DIR do projeto
GOOGLE_SHEETS_CREDENTIALS_PATH = BASE_DIR / config(
    'GOOGLE_SHEETS_CREDENTIALS_PATH', default='credenciais.json'
)
GOOGLE_SHEETS_PLANILHA_ID = config('GOOGLE_SHEETS_PLANILHA_ID', default='')