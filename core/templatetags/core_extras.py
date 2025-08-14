# /core/templatetags/core_extras.py

import base64
from django import template
from django.conf import settings
import os

register = template.Library()

@register.filter(name='get_image_as_base64')
def get_image_as_base64(path):
    """
    Toma una ruta relativa a un archivo estático, lo lee y lo devuelve
    codificado en Base64 para ser usado en una etiqueta <img>.
    """
    # Construye la ruta completa al archivo en el sistema de archivos
    # Asume que tienes STATICFILES_DIRS[0] configurado en settings.py
    file_path = os.path.join(settings.STATICFILES_DIRS[0], path.strip("/"))

    if not os.path.exists(file_path):
        print(f"Warning: Image file not found at {file_path}")
        return ""

    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        # Devuelve el formato completo para el src de la imagen
        return f"data:image/png;base64,{encoded_string}"