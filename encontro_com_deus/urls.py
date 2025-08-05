# encontro_com_deus/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='encontro_com_deus_index'),
    path('cadastro/', views.cadastro_participante, name='cadastro_participante'),
    path('detalhes/<int:participante_id>/', views.detalhes_participante, name='detalhes_participante'),
    path('gerenciar_participantes/', views.gerenciar_participantes, name='gerenciar_participantes'),
    path('detalhes/<int:participante_id>/', views.detalhes_participante, name='detalhes_participante'),
    path('editar/<int:participante_id>/', views.editar_participante, name='editar_participante'),
    path('confirmar_pagamento/<int:participante_id>/', views.confirmar_pagamento, name='confirmar_pagamento'),
]