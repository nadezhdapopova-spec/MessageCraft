from django import template
import re
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def highlight(text, query):
    if not query:
        return text

    words = re.findall(r'\w+', query)
    pattern = re.compile(r'(' + '|'.join(re.escape(word) for word in words) + r')', re.IGNORECASE)

    highlighted = pattern.sub(r'<span class="bg-warning text-dark">\1</span>', text)
    return mark_safe(highlighted)
