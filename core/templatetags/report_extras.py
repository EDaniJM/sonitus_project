from django import template
register = template.Library()

@register.filter
def chunk_spaced(value, n=4):
    """Inserta un espacio cada n caracteres (para IDs largos)."""
    s = str(value or "")
    n = int(n)
    return " ".join(s[i:i+n] for i in range(0, len(s), n))
