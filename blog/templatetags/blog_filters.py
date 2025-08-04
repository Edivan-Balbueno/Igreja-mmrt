# blog/templatetags/blog_filters.py

from django import template
import re

register = template.Library()

@register.filter
def youtube_embed_url_fix(html_string):
    """
    Corrige URLs de embed do YouTube em um HTML string,
    garantindo que o formato seja 'http://googleusercontent.com/youtube.com/embed/...'.
    """
    if isinstance(html_string, str):
        # A regex encontra URLs de iframe com youtube.com e captura o ID do vídeo
        # e outros parâmetros.
        pattern = re.compile(r'src=["\'](http://googleusercontent.com/youtube.com/(?:embed/|v/|watch\?v=|\d+)([a-zA-Z0-9_-]+)(.*?)?)["\']')
        
        def replace_match(match):
            original_url = match.group(1)
            video_id = match.group(2)
            params = match.group(3)
            
            # Constrói o URL de embed correto
            # O URL padrão de embed do YouTube é http://googleusercontent.com/youtube.com/embed/<video_id>
            # Vamos garantir que ele tem ?rel=0 no final para que não mostre vídeos relacionados de outros canais
            # A menos que o parâmetro já exista
            if '?rel=0' not in params:
                 new_src = f'http://googleusercontent.com/youtube.com/embed/{video_id}?rel=0'
            else:
                 new_src = f'http://googleusercontent.com/youtube.com/embed/{video_id}{params}'
            
            return f'src="{new_src}"'
        
        # Faz a substituição usando a função acima
        return pattern.sub(replace_match, html_string)
    return html_string