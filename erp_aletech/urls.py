# erp_aletech/urls.py
from django.contrib import admin
from django.urls import path, include

# ADIÇÕES NECESSÁRIAS PARA LOGÍSTICA DE ARQUIVOS (MEDIA):
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Nova Home Central (Raiz do sistema)
    path('', include('usuarios.urls')), 
    
    # 2. Módulos do Sistema
    path('helpdesk/', include('helpdesk.urls')), 
    path('comercial/', include('comercial.urls')),
    path('inventario/', include('inventario.urls', namespace='inventario')),
]


# Servir arquivos de mídia em ambiente de desenvolvimento (DEBUG = True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)