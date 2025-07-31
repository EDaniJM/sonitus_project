from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders
from django.conf import settings
import os

def link_callback(uri, rel):
    """
    Convierte /static/... a path absoluto para xhtml2pdf.
    """
    if uri.startswith(settings.STATIC_URL):
        path = finders.find(uri.replace(settings.STATIC_URL, ""))
        if path:
            return path
    if uri.startswith("file://"):
        return uri[7:]
    return uri  # último recurso

def render_to_pdf(template_src: str, context: dict, filename: str = "report.pdf"):
    template = get_template(template_src)
    html = template.render(context)

    result = BytesIO()
    pdf = pisa.CreatePDF(BytesIO(html.encode("utf-8")), dest=result, encoding='utf-8', link_callback=link_callback)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    return HttpResponse(html)
