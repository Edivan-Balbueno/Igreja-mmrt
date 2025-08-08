# encontro_com_deus/urls.py

from django.urls import path
from . import views
from django.conf import settings # <-- ADICIONE ESTA LINHA
from django.conf.urls.static import static # <-- E ESTA LINHA

urlpatterns = [
    path('', views.index, name='encontro_com_deus_index'),
    path('cadastro/', views.cadastro_participante, name='cadastro_participante'),
    path('detalhes/<int:participante_id>/', views.detalhes_participante, name='detalhes_participante'),
    path('gerenciar_participantes/', views.gerenciar_participantes, name='gerenciar_participantes'),
    path('detalhes/<int:participante_id>/', views.detalhes_participante, name='detalhes_participante'),
    path('editar/<int:participante_id>/', views.editar_participante, name='editar_participante'),
    path('confirmar_pagamento/<int:participante_id>/', views.confirmar_pagamento, name='confirmar_pagamento'),
    path('gerenciar_imagens/', views.gerenciar_imagens, name='gerenciar_imagens'),
    path('upload_image/', views.upload_image, name='upload_image'),
    path('delete_image/<int:image_id>/', views.delete_image, name='delete_image'),
    path('detalhes/<int:participante_id>/pagar_agora/', views.pagar_agora, name='pagar_agora'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # NECESSÁRIO PARA SERVIR AS IMAGENS NO DESENVOLVIMENTO
