# eventos/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_eventos, name='lista_eventos'),
    path('criar/', views.criar_evento, name='criar_evento'),
    path('editar/<int:evento_id>/', views.editar_evento, name='editar_evento'),
    path('gerenciar/<slug:slug>/', views.gerenciar_evento, name='gerenciar_evento'),
    path('gerenciar-campos/<int:evento_id>/', views.gerenciar_campos, name='gerenciar_campos'),
    path('cadastro/<int:evento_id>/', views.cadastro_participante_dinamico, name='cadastro_participante_dinamico'),
    path('detalhes/<slug:slug>/', views.detalhes_evento, name='detalhes_evento'),
    path('detalhes/id/<int:pk>/', views.detalhes_evento, name='detalhes_evento'), 
    path('upload-midia/<int:evento_id>/', views.upload_evento_midia, name='upload_evento_midia'),
    path('painel/', views.eventos_index, name='eventos_index'),
    path('participantes/<int:evento_id>/', views.lista_participantes, name='lista_participantes'),
    path('participante/editar/<int:participante_id>/', views.editar_participante, name='editar_participante'),
    path('participante/detalhes/<int:participante_id>/', views.detalhes_participante, name='detalhes_participante'),
    path('pagamento-agora/<int:participante_id>/', views.pagamento_agora, name='pagamento_agora'),
    path('pagamento/sucesso/<int:participante_id>/', views.pagamento_sucesso, name='pagamento_sucesso'),
    path('pagamento/pendente/<int:participante_id>/', views.pagamento_pendente, name='pagamento_pendente'),
    path('pagamento/falha/<int:participante_id>/', views.pagamento_falha, name='pagamento_falha'),
]
