from django import template
from django.utils.safestring import mark_safe
from django.conf import settings
import base64
register = template.Library()

@register.filter
def chunk_spaced(value, n=4):
    """Inserta un espacio cada n caracteres (para IDs largos)."""
    s = str(value or "")
    n = int(n)
    return " ".join(s[i:i+n] for i in range(0, len(s), n))

@register.filter(name='force_wrap')
def force_wrap(value, length=40):
    """
    Fuerza el ajuste de línea en palabras largas insertando una etiqueta <br />.
    Este es un método más agresivo para renderizadores de PDF limitados.
    """
    if not isinstance(value, str):
        return value

    br = '<br />'
    words = value.split(' ')
    wrapped_words = []
    
    for word in words:
        if len(word) > length:
            # Divide la palabra larga en trozos
            chunks = [word[i:i+length] for i in range(0, len(word), length)]
            # Une los trozos con un salto de línea
            wrapped_words.append(br.join(chunks))
        else:
            wrapped_words.append(word)
    
    # mark_safe es crucial para que se renderice la etiqueta <br />
    return mark_safe(' '.join(wrapped_words))
