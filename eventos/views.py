import logging
import mimetypes
import urllib.parse
from io import BytesIO

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
import mercadopago
from PIL import Image
import qrcode
import requests

from .forms import (
    CadastroParticipanteForm,
    CampoFormularioForm,
    EditarParticipanteForm,
    EventoEditForm,
    EventoForm,
    EventoMidiaForm,
    GerenciarCamposForm,
)
from .models import (
    CampoFormulario,
    Evento,
    EventoMidia,
    ParticipanteEvento,
    RespostaCampo,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# FUNÇÃO AUXILIAR DE PERMISSÃO
# ==============================================================================
def e_blog_admin(user):
  """Permite acesso se for Superusuário, Staff ou se pertencer ao grupo 'Blog Admins'."""
  return user.is_authenticated and (
      user.is_superuser
      or user.is_staff
      or user.groups.filter(name='Blog Admins').exists()
  )


# ==============================================================================
# VIEWS DE GESTÃO DE EVENTOS
# ==============================================================================
@login_required
def criar_evento(request):
  if not e_blog_admin(request.user):
    raise PermissionDenied

  if request.method == 'POST':
    form = EventoForm(request.POST, request.FILES)
    if form.is_valid():
      evento = form.save(commit=False)
      evento.criador = request.user  # Vincula o usuário logado como criador

      # Trata unicidade de slug no MySQL
      slug_base = slugify(evento.titulo)
      slug_unico = slug_base
      contador = 1
      while Evento.objects.filter(slug=slug_unico).exists():
        slug_unico = f'{slug_base}-{contador}'
        contador += 1
      evento.slug = slug_unico

      evento.save()
      messages.success(
          request, f"O evento '{evento.titulo}' foi criado com sucesso!"
      )
      return redirect('gerenciar_evento', slug=evento.slug)
    else:
      messages.error(
          request,
          'Ocorreu um erro ao criar o evento. Por favor, corrija o formulário.',
      )
  else:
    form = EventoForm()

  # FILTRO ESTRITO: Carrega APENAS os eventos onde o criador é o usuário atual
  eventos_existentes = Evento.objects.filter(criador=request.user).order_by(
      '-data_inicio'
  )

  context = {
      'form': form,
      'titulo_pagina': 'Criar Novo Evento',
      'botao_acao': 'Criar Evento',
      'eventos_existentes': eventos_existentes,
  }
  return render(request, 'eventos/criar_evento.html', context)


@login_required
def editar_evento(request, evento_id):
  if not e_blog_admin(request.user):
    raise PermissionDenied

  if request.user.is_superuser:
    evento = get_object_or_404(Evento, pk=evento_id)
  else:
    evento = get_object_or_404(Evento, pk=evento_id, criador=request.user)

  if request.method == 'POST':
    form = EventoEditForm(request.POST, instance=evento)
    if form.is_valid():
      form.save()
      messages.success(request, 'Evento atualizado com sucesso!')
      return redirect('gerenciar_evento', slug=evento.slug)
  else:
    form = EventoEditForm(instance=evento)

  context = {'form': form, 'evento': evento}
  return render(request, 'eventos/editar_evento.html', context)


@login_required
def gerenciar_evento(request, slug):
  if not e_blog_admin(request.user):
    raise PermissionDenied

  if request.user.is_superuser:
    evento = get_object_or_404(Evento, slug=slug)
  else:
    evento = get_object_or_404(Evento, slug=slug, criador=request.user)

  context = {
      'evento': evento,
      'qrcode_url': evento.qrcode.url if evento.qrcode else None,
  }
  return render(request, 'eventos/gerenciar_evento.html', context)


@login_required
def upload_evento_midia(request, evento_id):
  if not e_blog_admin(request.user):
    raise PermissionDenied

  if request.user.is_superuser:
    evento = get_object_or_404(Evento, pk=evento_id)
  else:
    evento = get_object_or_404(Evento, pk=evento_id, criador=request.user)

  if request.method == 'POST':
    form = EventoMidiaForm(request.POST, request.FILES)
    if form.is_valid():
      midia = form.save(commit=False)
      midia.evento = evento

      mime_type = mimetypes.guess_type(midia.media_file.name)[0]
      if mime_type and mime_type.startswith('image'):
        midia.media_type = 'image'
      elif mime_type and mime_type.startswith('video'):
        midia.media_type = 'video'
      else:
        messages.error(
            request,
            'Tipo de arquivo não suportado. Envie uma imagem ou vídeo.',
        )

      midia.save()
      messages.success(request, 'Mídia adicionada com sucesso!')
      return redirect('upload_evento_midia', evento_id=evento.id)
  else:
    form = EventoMidiaForm()

  midias = EventoMidia.objects.filter(evento=evento).order_by('-created_at')
  context = {'evento': evento, 'form': form, 'midias': midias}
  return render(request, 'eventos/upload_evento_midia.html', context)


@login_required
def gerenciar_campos(request, evento_id):
  if not e_blog_admin(request.user):
    raise PermissionDenied

  if request.user.is_superuser:
    evento = get_object_or_404(Evento, pk=evento_id)
  else:
    evento = get_object_or_404(Evento, pk=evento_id, criador=request.user)

  campo_mapa = {
      'nome_completo': {
          'nome': 'Nome completo',
          'tipo': 'texto',
          'is_required': True,
          'ordem': 1,
      },
      'telefone': {
          'nome': 'Telefone',
          'tipo': 'numero',
          'is_required': True,
          'ordem': 2,
      },
      'email': {
          'nome': 'E-mail',
          'tipo': 'email',
          'is_required': False,
          'ordem': 3,
      },
      'endereco': {
          'nome': 'Endereço',
          'tipo': 'texto',
          'is_required': False,
          'ordem': 4,
      },
      'tem_lider': {
          'nome': 'Você tem Líder? Qual o nome dele(a)?',
          'tipo': 'texto',
          'is_required': False,
          'ordem': 5,
      },
      'participa_igreja': {
          'nome': 'Você participa da Igreja MMRT? Qual?',
          'tipo': 'texto',
          'is_required': False,
          'ordem': 6,
      },
      'expectativas': {
          'nome': 'O que espera desse encontro? Expectativas?',
          'tipo': 'texto',
          'is_required': False,
          'ordem': 7,
      },
      'pode_participar': {
          'nome': 'Você pode participar?',
          'tipo': 'radio',
          'is_required': False,
          'opcoes': 'Sim,Não',
          'ordem': 8,
      },
      'nome_amigo': {
          'nome': 'Nome de um Amigo ou Familiar',
          'tipo': 'texto',
          'is_required': False,
          'ordem': 9,
      },
      'telefone_amigo': {
          'nome': 'Telefone do Amigo ou Familiar',
          'tipo': 'numero',
          'is_required': False,
          'ordem': 10,
      },
      'trabalhar_no_evento': {
          'nome': 'Vou trabalhar no Evento',
          'tipo': 'checkbox',
          'is_required': False,
          'ordem': 11,
      },
  }

  if request.method == 'POST':
    form = GerenciarCamposForm(request.POST)
    if form.is_valid():
      for field_name, detalhes in campo_mapa.items():
        if not form.cleaned_data.get(field_name):
          CampoFormulario.objects.filter(
              evento=evento, nome_campo=detalhes['nome']
          ).delete()

      for field_name, detalhes in campo_mapa.items():
        if form.cleaned_data.get(field_name):
          CampoFormulario.objects.update_or_create(
              evento=evento,
              nome_campo=detalhes['nome'],
              defaults={
                  'tipo_campo': detalhes['tipo'],
                  'is_required': detalhes['is_required'],
                  'opcoes': detalhes.get('opcoes', ''),
                  'ordem': detalhes.get('ordem'),
              },
          )

      messages.success(
          request, 'Campos do formulário atualizados com sucesso!'
      )
      return redirect('gerenciar_campos', evento_id=evento.pk)
  else:
    campos_ativos_db = CampoFormulario.objects.filter(
        evento=evento
    ).values_list('nome_campo', flat=True)
    initial_data = {
        field_name: True
        for field_name, detalhes in campo_mapa.items()
        if detalhes['nome'] in campos_ativos_db
    }
    form = GerenciarCamposForm(initial=initial_data)

  campos_do_evento = CampoFormulario.objects.filter(evento=evento).order_by(
      'ordem'
  )
  dynamic_form_fields = {}
  for campo in campos_do_evento:
    field_name = slugify(campo.nome_campo).replace('-', '_')
    if campo.tipo_campo == 'texto':
      dynamic_form_fields[field_name] = forms.CharField(
          label=campo.nome_campo, required=campo.is_required
      )
    elif campo.tipo_campo == 'numero':
      dynamic_form_fields[field_name] = forms.IntegerField(
          label=campo.nome_campo, required=campo.is_required
      )
    elif campo.tipo_campo == 'email':
      dynamic_form_fields[field_name] = forms.EmailField(
          label=campo.nome_campo, required=campo.is_required
      )
    elif campo.tipo_campo == 'multitexto':
      dynamic_form_fields[field_name] = forms.CharField(
          label=campo.nome_campo,
          widget=forms.Textarea,
          required=campo.is_required,
      )
    elif campo.tipo_campo == 'radio':
      opcoes = [(o.strip(), o.strip()) for o in campo.opcoes.split(',')]
      dynamic_form_fields[field_name] = forms.ChoiceField(
          label=campo.nome_campo,
          choices=opcoes,
          widget=forms.RadioSelect,
          required=campo.is_required,
      )
    elif campo.tipo_campo == 'checkbox':
      dynamic_form_fields[field_name] = forms.BooleanField(
          label=campo.nome_campo, required=campo.is_required
      )

  DynamicForm = type('DynamicForm', (forms.Form,), dynamic_form_fields)
  dynamic_form = DynamicForm()

  context = {'form': form, 'evento': evento, 'dynamic_form': dynamic_form}
  return render(request, 'eventos/gerenciar_campos.html', context)


# ==============================================================================
# VIEWS PÚBLICAS DE EVENTO E CADASTRO
# ==============================================================================
def detalhes_evento(request, slug):
  evento = get_object_or_404(Evento, slug=slug)
  midias = EventoMidia.objects.filter(evento=evento).order_by('-created_at')
  return render(
      request,
      'eventos/detalhes_evento.html',
      {'evento': evento, 'midias': midias},
  )


def eventos_index(request):
  eventos = Evento.objects.filter(is_active=True).order_by('data_inicio')
  return render(request, 'eventos/index.html', {'eventos': eventos})


def lista_eventos(request):
  eventos = Evento.objects.all().order_by('-data_inicio')
  return render(request, 'eventos/lista_eventos.html', {'eventos': eventos})


def cadastro_participante_dinamico(request, evento_id):
  evento = get_object_or_404(Evento, pk=evento_id)
  campos_ativos = CampoFormulario.objects.filter(
      evento=evento, is_active=True
  ).order_by('ordem')

  if request.method == 'POST':
    form = CadastroParticipanteForm(campos_ativos, request.POST)
    if form.is_valid():
      participante = ParticipanteEvento.objects.create(evento=evento)
      nome_completo_salvo = ''
      trabalha_no_evento_salvo = False

      for campo_obj in campos_ativos:
        field_name = (
            campo_obj.nome_campo.lower()
            .replace(' ', '_')
            .replace('.', '')
            .replace('?', '')
        )
        valor_campo = form.cleaned_data.get(field_name, '')

        if campo_obj.nome_campo == 'Nome completo':
          nome_completo_salvo = valor_campo
        elif campo_obj.nome_campo == 'E-mail':
          participante.email = valor_campo
        elif campo_obj.nome_campo == 'Telefone':
          participante.telefone = valor_campo
        elif campo_obj.nome_campo == 'Vou trabalhar no Evento':
          trabalha_no_evento_salvo = bool(valor_campo)

        RespostaCampo.objects.create(
            participante=participante,
            campo=campo_obj,
            valor=str(valor_campo) if valor_campo is not None else '',
        )

      participante.nome_completo = nome_completo_salvo
      participante.trabalha_no_evento = trabalha_no_evento_salvo
      participante.save()

      # Envio de E-mail de confirmação
      if participante.email:
        participante_url = request.build_absolute_uri(
            reverse('detalhes_participante', args=[participante.id])
        )
        subject = f'Confirmação de Inscrição no evento: {evento.titulo}'
        message = (
            f'Olá {participante.nome_completo},\n\n'
            f'Sua inscrição para o evento "{evento.titulo}" foi recebida com'
            ' sucesso!\n'
            'Acesse os detalhes e o pagamento através deste link:\n\n'
            f'{participante_url}\n\n'
            'Agradecemos a sua participação.'
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [participante.email],
            fail_silently=True,
        )

      messages.success(
          request,
          'Inscrição realizada com sucesso! Um e-mail com os detalhes foi'
          ' enviado.',
      )
      return redirect(
          'detalhes_participante', participante_id=participante.id
      )
  else:
    form = CadastroParticipanteForm(campos_ativos)

  return render(
      request,
      'eventos/cadastro_participante.html',
      {'form': form, 'evento': evento},
  )


# ==============================================================================
# VIEWS DE GESTÃO DE PARTICIPANTES
# ==============================================================================
@login_required
def lista_participantes(request, evento_id):
  if not e_blog_admin(request.user):
    raise PermissionDenied

  if request.user.is_superuser:
    evento = get_object_or_404(Evento, pk=evento_id)
  else:
    evento = get_object_or_404(Evento, pk=evento_id, criador=request.user)

  participantes = ParticipanteEvento.objects.filter(evento=evento)

  context = {
      'evento': evento,
      'total_participantes': participantes.count(),
      'vao_trabalhar': participantes.filter(trabalha_no_evento=True).count(),
      'nao_vao_trabalhar': participantes.filter(
          trabalha_no_evento=False
      ).count(),
      'pagamentos_pendentes': participantes.filter(
          pagamento_recebido=False
      ).count(),
      'participantes': participantes,
  }
  return render(request, 'eventos/lista_participantes.html', context)


@login_required
def editar_participante(request, participante_id):
  if not e_blog_admin(request.user):
    raise PermissionDenied

  participante = get_object_or_404(ParticipanteEvento, pk=participante_id)

  # Garante permissão de dono do evento
  if (
      not request.user.is_superuser
      and participante.evento.criador != request.user
  ):
    raise PermissionDenied

  evento = participante.evento
  campos_ativos = CampoFormulario.objects.filter(
      evento=evento, is_active=True
  ).order_by('ordem')

  if request.method == 'POST':
    form = EditarParticipanteForm(campos_ativos, participante, request.POST)
    if form.is_valid():
      nome_completo_salvo = ''
      trabalha_no_evento_salvo = False

      for campo_obj in campos_ativos:
        field_name = (
            campo_obj.nome_campo.lower()
            .replace(' ', '_')
            .replace('.', '')
            .replace('?', '')
        )
        valor_campo = form.cleaned_data.get(field_name, '')

        if campo_obj.nome_campo == 'Nome completo':
          nome_completo_salvo = valor_campo
        elif campo_obj.nome_campo == 'Vou trabalhar no Evento':
          trabalha_no_evento_salvo = bool(valor_campo)

      participante.nome_completo = nome_completo_salvo
      participante.trabalha_no_evento = trabalha_no_evento_salvo
      participante.pagamento_recebido = form.cleaned_data.get(
          'pagamento_recebido', False
      )
      participante.save()

      for campo_obj in campos_ativos:
        field_name = (
            campo_obj.nome_campo.lower()
            .replace(' ', '_')
            .replace('.', '')
            .replace('?', '')
        )
        valor_campo = form.cleaned_data.get(field_name, '')

        resposta, _ = RespostaCampo.objects.get_or_create(
            participante=participante, campo=campo_obj, defaults={'valor': ''}
        )
        resposta.valor = str(valor_campo) if valor_campo is not None else ''
        resposta.save()

      messages.success(request, 'Participante atualizado com sucesso!')
      return redirect(
          'detalhes_participante', participante_id=participante.id
      )
  else:
    form = EditarParticipanteForm(campos_ativos, participante)

  return render(
      request,
      'eventos/editar_participante.html',
      {'form': form, 'participante': participante},
  )


def detalhes_participante(request, participante_id):
  participante = get_object_or_404(ParticipanteEvento, pk=participante_id)
  respostas = RespostaCampo.objects.filter(participante=participante)
  return render(
      request,
      'eventos/detalhes_participante.html',
      {'participante': participante, 'respostas': respostas},
  )

# ==============================================================================
# INTEGRACÃO MERCADO PAGO E PAGAMENTOS
# ==============================================================================
def pagamento_agora(request, participante_id):
    participante = get_object_or_404(ParticipanteEvento, pk=participante_id)
    evento = participante.evento

    # Recuperação de e-mail flexível
    email_pagador = getattr(participante, 'email', None)

    if not email_pagador:
        resposta_email = (
            RespostaCampo.objects.filter(participante=participante)
            .filter(
                Q(campo__nome_campo__iexact='email')
                | Q(campo__nome_campo__iexact='e-mail')
            )
            .first()
        )

        if resposta_email and resposta_email.valor:
            email_pagador = resposta_email.valor.strip()

    # Fallback de e-mail
    if not email_pagador:
        email_pagador = (
            request.user.email
            if (hasattr(request, 'user') and request.user.email)
            else 'participante@email.com'
        )

    if not evento.valor or float(evento.valor) <= 0:
        messages.error(request, 'O valor do evento não é válido para pagamento.')
        return redirect('detalhes_participante', participante_id=participante.id)

    try:
        criador = evento.criador
        user_access_token = getattr(criador, 'mp_access_token', None)
        receiver_id = getattr(criador, 'mp_user_id', None)

        # Se a conta do criador possui Access Token próprio (OAuth), usa para receber 100% diretamente
        if user_access_token:
            sdk = mercadopago.SDK(user_access_token)
            use_sponsor = False
        # Caso contrário, verifica se tem o mp_user_id registrado para fallback via token global
        elif receiver_id:
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
            use_sponsor = True
        else:
            messages.error(
                request,
                'Erro: O criador deste evento ainda não conectou a conta do Mercado Pago.',
            )
            return redirect('detalhes_participante', participante_id=participante.id)

        preference_data = {
            'items': [{
                'title': f'Inscrição - {evento.titulo}',
                'quantity': 1,
                'unit_price': float(evento.valor),
                'id': participante.id,
                'category_id': 'services',
            }],
            'back_urls': {
                'success': request.build_absolute_uri(
                    reverse('pagamento_sucesso', kwargs={'participante_id': participante.id})
                ),
                'pending': request.build_absolute_uri(
                    reverse('pagamento_pendente', kwargs={'participante_id': participante.id})
                ),
                'failure': request.build_absolute_uri(
                    reverse('pagamento_falha', kwargs={'participante_id': participante.id})
                ),
            },
            'payer': {'email': email_pagador},
            'external_reference': str(participante.id),
            'notification_url': request.build_absolute_uri(
                reverse('mercado_pago_ipn')
            ),
        }

        # Adiciona o sponsor_id apenas no cenário de fallback sem token individual
        if use_sponsor and receiver_id:
            preference_data['sponsor_id'] = int(receiver_id)

        preference_response = sdk.preference().create(preference_data)

        # Captura detalhada do retorno da API
        if (
            'response' not in preference_response
            or 'init_point' not in preference_response['response']
        ):
            import sys

            print('RESPOSTA COMPLETA MP:', preference_response, file=sys.stderr)

            error_details = preference_response.get('response', {})
            error_msg = error_details.get(
                'message', preference_response.get('error', 'Erro desconhecido.')
            )
            raise Exception(f'Erro MP ({preference_response.get("status")}): {error_msg}')

        return redirect(preference_response['response']['init_point'])

    except Exception as e:
        messages.error(
            request, f'Ocorreu um erro ao gerar o link de pagamento: {e}'
        )
        return redirect('detalhes_participante', participante_id=participante.id)


@csrf_exempt
def pagamento_sucesso(request, participante_id):
  participante = get_object_or_404(ParticipanteEvento, pk=participante_id)
  participante.pagamento_recebido = True
  participante.save()
  messages.success(request, 'Pagamento confirmado com sucesso!')
  return redirect('detalhes_participante', participante_id=participante.id)


@csrf_exempt
def pagamento_pendente(request, participante_id):
  messages.warning(
      request, 'O pagamento está pendente de confirmação pelo Mercado Pago.'
  )
  return redirect('detalhes_participante', participante_id=participante_id)


@csrf_exempt
def pagamento_falha(request, participante_id):
  messages.error(
      request, 'O pagamento não foi concluído. Por favor, tente novamente.'
  )
  return redirect('detalhes_participante', participante_id=participante_id)


@csrf_exempt
def mercado_pago_ipn(request):
  if request.method == 'GET':
    return HttpResponse('IPN URL OK', status=200)

  if request.method == 'POST':
    try:
      body = json.loads(request.body.decode('utf-8'))
      topic = body.get('topic') or body.get('type')
      resource_id = body.get('id') or body.get('resource')

      sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

      if topic == 'payment' and resource_id:
        payment_response = sdk.payment().get(resource_id)
        payment = payment_response.get('response')

        if payment and payment.get('status') == 'approved':
          participante_id = payment.get('external_reference')
          if participante_id:
            try:
              participante = ParticipanteEvento.objects.get(
                  pk=int(participante_id)
              )
              if not participante.pagamento_recebido:
                participante.pagamento_recebido = True
                participante.save()
            except ParticipanteEvento.DoesNotExist:
              pass

      return HttpResponse('Notification processed', status=200)
    except Exception as e:
      return HttpResponse('Error', status=200)

  return HttpResponse(status=200)


def mercado_pago_connect_auth(request):
  BASE_AUTH_URL = 'https://auth.mercadopago.com.br/authorization'
  params = {
      'client_id': settings.MP_CLIENT_ID,
      'response_type': 'code',
      'redirect_uri': settings.MP_REDIRECT_URI,
  }
  return redirect(f'{BASE_AUTH_URL}?{urllib.parse.urlencode(params)}')


@login_required
def mercado_pago_connect_callback(request):
  code = request.GET.get('code')

  if not code:
    messages.error(
        request, 'Erro: Código de autorização não retornado pelo Mercado Pago.'
    )
    return redirect('perfil')

  TOKEN_URL = 'https://api.mercadopago.com/oauth/token'

  payload = {
      'client_id': settings.MP_CLIENT_ID,
      'client_secret': settings.MP_CLIENT_SECRET,
      'code': code,
      'redirect_uri': settings.MP_REDIRECT_URI,
      'grant_type': 'authorization_code',
  }

  headers = {'Content-Type': 'application/x-www-form-urlencoded'}

  try:
    response = requests.post(
        TOKEN_URL, data=payload, headers=headers, timeout=10
    )

    if response.status_code != 200:
      data_error = response.json()
      mensagem_erro = data_error.get(
          'message', data_error.get('error', response.text)
      )
      messages.error(
          request,
          f'Erro no Mercado Pago ({response.status_code}): {mensagem_erro}',
      )
      return redirect('perfil')

    data = response.json()
    mp_user_id = data.get('user_id')

    if mp_user_id:
      user = request.user
      user.mp_user_id = str(mp_user_id)

      # 1. Salva explicitamente no MySQL
      user.save(update_fields=['mp_user_id'])

      # 2. Recarrega o objeto do banco para a view de perfil ler o valor atualizado
      user.refresh_from_db()

      messages.success(
          request,
          '✅ Conta do Mercado Pago conectada com sucesso! ID do Recebedor:'
          f' {mp_user_id}',
      )
    else:
      messages.error(
          request,
          'A API do Mercado Pago respondeu, mas não retornou o campo user_id.',
      )

  except requests.exceptions.RequestException as e:
    messages.error(
        request, f'Falha ao conectar na API do Mercado Pago: {str(e)}'
    )

  return redirect('perfil')


def buscar_participante_ajax(request, evento_id):
    nome_query = request.GET.get('nome', '').strip()
    
    if not nome_query:
        return JsonResponse({'participantes': []})

    # Filtra as respostas dinâmicas pelo nome digitado
    respostas = RespostaCampo.objects.filter(
        participante__evento_id=evento_id,
        valor__icontains=nome_query
    ).select_related('participante')

    participantes_dict = {}
    for resp in respostas:
        part = resp.participante
        if part.id not in participantes_dict:
            # Verifica com segurança se o participante está pago
            is_pago = getattr(part, 'pago', None) or getattr(part, 'pagamento_confirmado', False) or (getattr(part, 'status_pagamento', '') == 'Pago')
            
            participantes_dict[part.id] = {
                'id': part.id,
                'nome': resp.valor,
                'status_pagamento': 'Pago' if is_pago else 'Pendente'
            }

    return JsonResponse({'participantes': list(participantes_dict.values())})