# encontro_com_deus/views.py

from django.shortcuts import render, redirect, get_object_or_404
from .forms import ParticipanteForm
from .models import Participante, EncontroImage
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages

def index(request):
    # Busque todas as imagens do Encontro com Deus
    encontro_images = EncontroImage.objects.all().order_by('-uploaded_at')

    context = {
        'titulo': 'Encontro com Deus',
        'encontro_images': encontro_images, # Passe as imagens para o template
    }
    return render(request, 'encontro_com_deus/index.html', context)

def cadastro_participante(request):
    if request.method == 'POST':
        form = ParticipanteForm(request.POST)
        if form.is_valid():
            participante = form.save()
            return redirect('detalhes_participante', participante_id=participante.id)
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
    participantes = Participante.objects.all().order_by('nome_completo')
    context = {
        'titulo': 'Gerenciar Participantes',
        'participantes': participantes,
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
            return redirect('detalhes_participante', participante_id=participante.id)
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
    
    return redirect('gerenciar_participantes')

@login_required
@permission_required('encontro_com_deus.add_encontroimage', raise_exception=True)
def gerenciar_imagens(request):
    images = EncontroImage.objects.all()
    return render(request, 'encontro_com_deus/gerenciar_imagens.html', {'images': images})

@login_required
@permission_required('encontro_com_deus.add_encontroimage', raise_exception=True)
def upload_image(request):
    if request.method == 'POST':
        form = EncontroImageForm(request.POST, request.FILES) # <-- O FORMULÁRIO AINDA PRECISA SER CRIADO
        if form.is_valid():
            form.save()
            messages.success(request, 'Imagem carregada com sucesso!')
            return redirect('gerenciar_imagens')
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
        return redirect('gerenciar_imagens')
    return render(request, 'encontro_com_deus/confirm_delete_image.html', {'image': image})

# Para o formulário de upload, crie o arquivo encontro_com_deus/forms.py
from django import forms
class EncontroImageForm(forms.ModelForm):
    class Meta:
        model = EncontroImage
        fields = ['image', 'caption']