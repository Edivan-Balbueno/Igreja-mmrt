# encontro_com_deus/views.py

from django.shortcuts import render, redirect, get_object_or_404
from .forms import ParticipanteForm, EncontroImageForm
from .models import Participante, EncontroImage
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages

def index(request):
    # Busque todas as imagens do Encontro com Deus
    encontro_images = EncontroImage.objects.all().order_by('-uploaded_at')

    context = {
        'titulo': '14° Encontro com Deus para Homens',
        'encontro_images': encontro_images, # Passe as imagens para o template
    }
    return render(request, 'encontro_com_deus/index.html', context)

def cadastro_participante(request):
    if request.method == 'POST':
        form = ParticipanteForm(request.POST)
        if form.is_valid():
            participante = form.save()
            return redirect('encontro_com_deus:detalhes_participante', participante_id=participante.id)
    else:
        form = ParticipanteForm()
    
    return render(request, 'encontro_com_deus/cadastro_participante.html', {'form': form})

def detalhes_participante(request, participante_id):
    participante = get_object_or_404(Participante, pk=participante_id)
    
    is_admin = False
    if request.user.is_authenticated:
        is_admin = request.user.groups.filter(name='Blog Admins').exists()
    
    context = {
        'participante': participante,
        'is_admin': is_admin,
    }
    return render(request, 'encontro_com_deus/detalhes_participante.html', context)

@login_required
@permission_required('encontro_com_deus.change_participante', raise_exception=True)
def gerenciar_participantes(request):
    # Obtém o parâmetro de filtro da URL (por exemplo, '?filtro=pendente')
    filtro = request.GET.get('filtro')

    # Obter todos os participantes para a contagem, independente do filtro
    todos_participantes = Participante.objects.all()

    # Define o queryset inicial para a lista a ser exibida
    participantes_list = todos_participantes.order_by('nome_completo')

    # Aplica o filtro se ele existir na URL
    if filtro == 'vai_trabalhar':
        participantes_list = todos_participantes.filter(trabalho_encontro=True).order_by('nome_completo')
    elif filtro == 'nao_vai_trabalhar':
        participantes_list = todos_participantes.filter(trabalho_encontro=False).order_by('nome_completo')
    elif filtro == 'pagamentos_pendentes':
        participantes_list = todos_participantes.filter(evento_pago=False).order_by('nome_completo')
    
    context = {
        'titulo': 'Gerenciar Participantes',
        'participantes': participantes_list,
        'total_participantes': todos_participantes.count(),
        'vai_trabalhar': todos_participantes.filter(trabalho_encontro=True).count(),
        'nao_vai_trabalhar': todos_participantes.filter(trabalho_encontro=False).count(),
        'pagamentos_pendentes': todos_participantes.filter(evento_pago=False).count(),
        'filtro_ativo': filtro,  # Adiciona o filtro ativo ao contexto
    }

    return render(request, 'encontro_com_deus/gerenciar_participantes.html', context)


def detalhes_participante(request, participante_id):
    participante = get_object_or_404(Participante, pk=participante_id)
    
    # ADICIONE ESTA VERIFICAÇÃO DE LÓGICA AQUI
    is_admin = False
    if request.user.is_authenticated:
        # Verificação robusta e segura para o grupo
        is_admin = request.user.groups.filter(name='Blog Admins').exists()
    
    context = {
        'participante': participante,
        'is_admin': is_admin, # Passe a variável booleana para o template
    }
    return render(request, 'encontro_com_deus/detalhes_participante.html', context)


@login_required
@permission_required('encontro_com_deus.change_participante', raise_exception=True) 
def editar_participante(request, participante_id):
    participante = get_object_or_404(Participante, pk=participante_id)
    if request.method == 'POST':
        form = ParticipanteForm(request.POST, instance=participante)
        if form.is_valid():
            form.save()
            return redirect('encontro_com_deus:detalhes_participante', participante_id=participante.id)
    else:
        form = ParticipanteForm(instance=participante)
    
    return render(request, 'encontro_com_deus/editar_participante.html', {'form': form, 'participante': participante, 'titulo': 'Editar Participante'})

@login_required
@permission_required('encontro_com_deus.change_participante', raise_exception=True)
def confirmar_pagamento(request, participante_id):
    participante = get_object_or_404(Participante, pk=participante_id)
    if not participante.evento_pago:
        participante.evento_pago = True
        participante.save()
        messages.success(request, f'O pagamento para {participante.nome_completo} foi confirmado com sucesso.')
    
    return redirect('encontro_com_deus:gerenciar_participantes')

@login_required
@permission_required('encontro_com_deus.view_encontroimage', raise_exception=True)
def gerenciar_imagens(request):
    encontro_images = EncontroImage.objects.all().order_by('-uploaded_at')
    return render(request, 'encontro_com_deus/gerenciar_imagens.html', {'encontro_images': encontro_images})

@login_required
@permission_required('encontro_com_deus.add_encontroimage', raise_exception=True)
def upload_image(request):
    if request.method == 'POST':
        form = EncontroImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mídia carregada com sucesso!')
            return redirect('encontro_com_deus:gerenciar_imagens')
    else:
        form = EncontroImageForm()
    return render(request, 'encontro_com_deus/upload_image.html', {'form': form})

@login_required
@permission_required('encontro_com_deus.delete_encontroimage', raise_exception=True)
def delete_image(request, image_id):
    image = get_object_or_404(EncontroImage, pk=image_id)
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Imagem excluída com sucesso.')
        return redirect('encontro_com_deus:gerenciar_imagens')
    return render(request, 'encontro_com_deus/confirm_delete_image.html', {'image': image})

def pagar_agora(request, participante_id):
    participante = get_object_or_404(Participante, pk=participante_id)

    # Dados do QR Code fornecidos pelo utilizador
    qrcode_image_url = 'images/enconito_com_Deus.jpeg'
    pix_copia_e_cola = '00020126710014br.gov.bcb.pix0114+55679964812100231Pagamento do Encontro com Deus.5204000053039865406350.005802BR5929Edevaldo Xisperes de Oliveira6008Dourados62070503***6304BA9A' # Substitua pelo seu código real

    context = {
        'participante': participante,
        'qrcode_image_url': qrcode_image_url,
        'pix_copia_e_cola': pix_copia_e_cola,
    }
    return render(request, 'encontro_com_deus/pagar_agora.html', context)