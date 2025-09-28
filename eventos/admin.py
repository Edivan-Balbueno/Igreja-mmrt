from django.contrib import admin
from .models import Evento, ParticipanteEvento

admin.site.register(Evento)
admin.site.register(ParticipanteEvento)
ParticipanteEvento