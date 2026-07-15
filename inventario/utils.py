import io
import os
from django.template.loader import get_template
from django.conf import settings
from xhtml2pdf import pisa


def link_callback(uri, rel):
    """
    Converte URIs de recursos (imagens, CSS, etc.) para caminhos absolutos
    no sistema de arquivos, permitindo ao xhtml2pdf localizar e embutir
    os arquivos no PDF gerado.

    Suporta:
      - Caminhos relativos ao STATIC_ROOT / STATICFILES_DIRS
      - Caminhos relativos ao MEDIA_ROOT
      - Caminhos absolutos diretos no filesystem (ex: /home/... ou D:\...)
    """
    # 1) Se já é um caminho absoluto válido no filesystem, usa direto
    if os.path.isfile(uri):
        return uri

    # 2) Tenta resolver como recurso estático (STATIC_URL)
    static_url = settings.STATIC_URL or '/static/'
    if uri.startswith(static_url):
        path = uri.replace(static_url, '', 1)
        static_root = getattr(settings, 'STATIC_ROOT', None)
        if static_root:
            fpath = os.path.join(static_root, path)
            if os.path.isfile(fpath):
                return fpath
        # Fallback: procurar nas STATICFILES_DIRS
        for sdir in getattr(settings, 'STATICFILES_DIRS', []):
            fpath = os.path.join(sdir, path)
            if os.path.isfile(fpath):
                return fpath

    # 3) Tenta resolver como recurso de media (MEDIA_URL)
    media_url = settings.MEDIA_URL or '/media/'
    if uri.startswith(media_url):
        path = uri.replace(media_url, '', 1)
        fpath = os.path.join(settings.MEDIA_ROOT, path)
        if os.path.isfile(fpath):
            return fpath

    # 4) Último recurso: tenta relativo ao BASE_DIR
    fpath = os.path.join(str(settings.BASE_DIR), uri)
    if os.path.isfile(fpath):
        return fpath

    # Se nada funcionou, retorna o URI original e deixa o xhtml2pdf tentar
    return uri


def render_to_pdf(template_src, context_dict={}):
    """
    Renderiza um template HTML para um arquivo PDF usando xhtml2pdf.
    Usa link_callback para garantir que imagens e recursos locais
    sejam encontrados corretamente no filesystem.
    Retorna os bytes do PDF se sucesso, senão None.
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()

    pdf = pisa.pisaDocument(
        io.BytesIO(html.encode("UTF-8")),
        result,
        link_callback=link_callback
    )

    if not pdf.err:
        return result.getvalue()
    return None
