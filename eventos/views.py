# eventos/views.py

import mimetypes
import mercadopago
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
import qrcode
import json
from django.http import HttpResponse
from django.http import JsonResponse
from django.core.files import File
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.forms import formset_factory, modelformset_factory
from django import forms
from .models import Evento, CampoFormulario, ParticipanteEvento, RespostaCampo, EventoMidia
from .forms import EventoForm, EventoEditForm, CampoFormularioForm, EventoMidiaForm, GerenciarCamposForm
from .forms import CadastroParticipanteForm, EditarParticipanteForm

@permission_required('eventos.add_evento', raise_exception=True)
def criar_evento(request):
    """
    View para criar um novo evento e listar os eventos existentes.
    """
    # 1. Instancie o formulário fora do bloco condicional inicial
    if request.method == 'POST':
        form = EventoForm(request.POST, request.FILES)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.criador = request.user
            evento.save()
            messages.success(request, f"O evento '{evento.titulo}' foi criado com sucesso!")
            # Redireciona APÓS o sucesso, sem precisar definir eventos_existentes neste caminho
            return redirect('gerenciar_evento', slug=evento.slug) 
        else:
            messages.error(request, "Ocorreu um erro ao criar o evento. Por favor, corrija os erros no formulário.")
            # Se o POST falhar, o form inválido será passado para o render abaixo.
    else:
        form = EventoForm()
    
    # 2. Defina eventos_existentes aqui, ANTES do contexto, para que esteja sempre disponível
    eventos_existentes = Evento.objects.all().order_by('-data_inicio')

    context = {
        'form': form,
        'titulo_pagina': 'Criar Novo Evento',
        'botao_acao': 'Criar Evento',
        'eventos_existentes': eventos_existentes, # Agora a variável existe neste ponto
    }
    return render(request, 'eventos/criar_evento.html', context)

@permission_required('eventos.add_eventomidia', raise_exception=True)
def upload_evento_midia(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    
    if request.method == 'POST':
        form = EventoMidiaForm(request.POST, request.FILES)
        if form.is_valid():
            midia = form.save(commit=False)
            midia.evento = evento
            
            # Determina o tipo de mídia
            mime_type = mimetypes.guess_type(midia.media_file.name)[0]
            if mime_type and mime_type.startswith('image'):
                midia.media_type = 'image'
            elif mime_type and mime_type.startswith('video'):
                midia.media_type = 'video'
            else:
                messages.error(request, 'Tipo de arquivo não suportado. Por favor, envie uma imagem ou um vídeo.')
                # Continua para o render da página com o erro
            
            midia.save()
            messages.success(request, 'Mídia adicionada com sucesso!')
            # Redireciona para a mesma página, forçando a atualização
            return redirect('upload_evento_midia', evento_id=evento.id)
    else:
        form = EventoMidiaForm()
    
    # Busca todas as mídias do evento para exibi-las
    midias = EventoMidia.objects.filter(evento=evento).order_by('-created_at')
    
    context = {
        'evento': evento,
        'form': form,
        'midias': midias,
    }
    
    return render(request, 'eventos/upload_evento_midia.html', context)

def detalhes_evento(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    # Correção: usar 'created_at' em vez de 'uploaded_at'
    midias = EventoMidia.objects.filter(evento=evento).order_by('-created_at')
    
    context = {
        'evento': evento,
        'midias': midias,
    }
    return render(request, 'eventos/detalhes_evento.html', context)

def eventos_index(request):
    """
    Página de índice para listar todos os eventos ativos em cards.
    """
    eventos = Evento.objects.filter(is_active=True).order_by('data_inicio')
    
    context = {
        'eventos': eventos
    }
    return render(request, 'eventos/index.html', context)

@permission_required('eventos.change_evento', raise_exception=True)
def editar_evento(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    if request.method == 'POST':
        form = EventoEditForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento atualizado com sucesso!')
            return redirect('gerenciar_evento', slug=evento.slug)
    else:
        form = EventoEditForm(instance=evento)
    
    context = {
        'form': form,
        'evento': evento
    }
    return render(request, 'eventos/editar_evento.html', context)

@permission_required('eventos.mostrar_eventos', raise_exception=True)
def gerenciar_evento(request, slug):
    """
    Página de gestão/administração do evento.
    Exige a permissão 'eventos.mostrar_eventos'.
    """
    # Buscamos o evento pelo slug, pois a URL de gestão usará o slug
    evento = get_object_or_404(Evento, slug=slug)
    
    context = {
        'evento': evento,
        'qrcode_url': evento.qrcode.url if evento.qrcode else None,
        # Adicione aqui outros dados de gestão, como lista de participantes, etc.
    }
    return render(request, 'eventos/gerenciar_evento.html', context)

@permission_required('eventos.change_campoformulario', raise_exception=True)
def gerenciar_campos(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    
    campo_mapa = {
        'nome_completo': {'nome': 'Nome completo', 'tipo': 'texto', 'is_required': True, 'ordem': 1},
        'telefone': {'nome': 'Telefone', 'tipo': 'numero', 'is_required': True, 'ordem': 2},
        'email': {'nome': 'E-mail', 'tipo': 'email', 'is_required': False, 'ordem': 3},
        'endereco': {'nome': 'Endereço', 'tipo': 'texto', 'is_required': False, 'ordem': 4},
        'tem_lider': {'nome': 'Você tem Líder? Qual o nome dele(a)?', 'tipo': 'texto', 'is_required': False, 'ordem': 5},
        'participa_igreja': {'nome': 'Você participa da Igreja MMRT? Qual?', 'tipo': 'texto', 'is_required': False, 'ordem': 6},
        'expectativas': {'nome': 'O que espera desse encontro? Expectativas?', 'tipo': 'texto', 'is_required': False, 'ordem': 7},
        'pode_participar': {'nome': 'Você pode participar?', 'tipo': 'radio', 'is_required': False, 'opcoes': 'Sim,Não', 'ordem': 8},
        'nome_amigo': {'nome': 'Nome de um Amigo ou Familiar', 'tipo': 'texto', 'is_required': False, 'ordem': 9},
        'telefone_amigo': {'nome': 'Telefone do Amigo ou Familiar', 'tipo': 'numero', 'is_required': False, 'ordem': 10},
        'trabalhar_no_evento': {'nome': 'Vou trabalhar no Evento', 'tipo': 'checkbox', 'is_required': False, 'ordem': 11},
    }
    
    if request.method == 'POST':
        form = GerenciarCamposForm(request.POST)
        if form.is_valid():
            for field_name, detalhes in campo_mapa.items():
                if not form.cleaned_data.get(field_name):
                    CampoFormulario.objects.filter(evento=evento, nome_campo=detalhes['nome']).delete()
            
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
                        }
                    )
            
            messages.success(request, 'Campos do formulário atualizados com sucesso!')
            return redirect('gerenciar_campos', evento_id=evento.pk)
    else:
        campos_ativos_db = CampoFormulario.objects.filter(evento=evento).values_list('nome_campo', flat=True)
        initial_data = {}
        for field_name, detalhes in campo_mapa.items():
            if detalhes['nome'] in campos_ativos_db:
                initial_data[field_name] = True
        
        form = GerenciarCamposForm(initial=initial_data)

    # --- Lógica para gerar a pré-visualização do formulário dinâmico ---
    campos_do_evento = CampoFormulario.objects.filter(evento=evento).order_by('ordem')
    dynamic_form_fields = {}
    for campo in campos_do_evento:
        field_name = slugify(campo.nome_campo).replace('-', '_')
        if campo.tipo_campo == 'texto':
            dynamic_form_fields[field_name] = forms.CharField(label=campo.nome_campo, required=campo.is_required)
        elif campo.tipo_campo == 'numero':
            dynamic_form_fields[field_name] = forms.IntegerField(label=campo.nome_campo, required=campo.is_required)
        elif campo.tipo_campo == 'email':
            dynamic_form_fields[field_name] = forms.EmailField(label=campo.nome_campo, required=campo.is_required)
        elif campo.tipo_campo == 'multitexto':
            dynamic_form_fields[field_name] = forms.CharField(label=campo.nome_campo, widget=forms.Textarea, required=campo.is_required)
        elif campo.tipo_campo == 'radio':
            opcoes = [(o.strip(), o.strip()) for o in campo.opcoes.split(',')]
            dynamic_form_fields[field_name] = forms.ChoiceField(label=campo.nome_campo, choices=opcoes, widget=forms.RadioSelect, required=campo.is_required)
        elif campo.tipo_campo == 'checkbox':
            dynamic_form_fields[field_name] = forms.BooleanField(label=campo.nome_campo, required=campo.is_required)

    DynamicForm = type('DynamicForm', (forms.Form,), dynamic_form_fields)
    dynamic_form = DynamicForm()
    # ---------------------------------------------------------------------

    context = {
        'form': form,
        'evento': evento,
        'dynamic_form': dynamic_form, # Passa o formulário dinâmico para o template
    }
    return render(request, 'eventos/gerenciar_campos.html', context)

def cadastro_participante_dinamico(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    campos_ativos = CampoFormulario.objects.filter(evento=evento, is_active=True).order_by('ordem')
    
    if request.method == 'POST':
        form = CadastroParticipanteForm(campos_ativos, request.POST)

        if form.is_valid():
            participante = ParticipanteEvento.objects.create(evento=evento)
            
            nome_completo_salvo = ''
            trabalha_no_evento_salvo = False

            for campo_obj in campos_ativos:
                field_name = campo_obj.nome_campo.lower().replace(' ', '_').replace('.', '').replace('?', '')
                valor_campo = form.cleaned_data.get(field_name, '')

                if campo_obj.nome_campo == 'Nome completo':
                    nome_completo_salvo = valor_campo
                
                if campo_obj.nome_campo == 'E-mail':  # Adicione esta verificação para o e-mail
                    participante.email = valor_campo
                
                if campo_obj.nome_campo == 'Telefone':  # Adicione esta verificação para o telefone
                    participante.telefone = valor_campo

                if campo_obj.nome_campo == 'Vou trabalhar no Evento':
                    trabalha_no_evento_salvo = True if valor_campo else False

                RespostaCampo.objects.create(
                    participante=participante,
                    campo=campo_obj,
                    valor=str(valor_campo) if valor_campo is not None else ''
                )

            participante.nome_completo = nome_completo_salvo
            participante.trabalha_no_evento = trabalha_no_evento_salvo
            participante.save()

            # Enviar e-mail com o link de acesso
            participante_url = request.build_absolute_uri(
                reverse('detalhes_participante', args=[participante.id])
            )
            
            subject = f'Confirmação de Inscrição no evento: {evento.titulo}'
            message = (
                f'Olá {participante.nome_completo},\n\n'
                f'Sua inscrição para o evento "{evento.titulo}" foi recebida com sucesso!\n'
                f'Você pode acessar os detalhes de sua inscrição e efetuar o pagamento a qualquer momento através deste link:\n\n'
                f'{participante_url}\n\n'
                f'Agradecemos a sua participação.'
            )
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [participante.email], # Usa o e-mail do participante
                fail_silently=False,
            )

            messages.success(request, "Inscrição realizada com sucesso! Um e-mail com os detalhes foi enviado para você.")
            return redirect('detalhes_participante', participante_id=participante.id)
    else:
        form = CadastroParticipanteForm(campos_ativos)

    return render(request, 'eventos/cadastro_participante.html', {'form': form, 'evento': evento})
    


@permission_required('eventos.view_participanteevento', raise_exception=True)
def lista_participantes(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    participantes = ParticipanteEvento.objects.filter(evento=evento)

    # Coleta os dados para os cards
    total_participantes = participantes.count()
    vao_trabalhar = participantes.filter(trabalha_no_evento=True).count()
    
    # Adicione a contagem dos que NÃO vão trabalhar
    nao_vao_trabalhar = participantes.filter(trabalha_no_evento=False).count()

    pagamentos_pendentes = participantes.filter(pagamento_recebido=False).count()
    
    context = {
        'evento': evento,
        'total_participantes': total_participantes,
        'vao_trabalhar': vao_trabalhar,
        'nao_vao_trabalhar': nao_vao_trabalhar,  # Adicione esta linha
        'pagamentos_pendentes': pagamentos_pendentes,
        'participantes': participantes,
    }
    return render(request, 'eventos/lista_participantes.html', context)

@permission_required('eventos.change_participanteevento', raise_exception=True)
def editar_participante(request, participante_id):
    participante = get_object_or_404(ParticipanteEvento, pk=participante_id)
    evento = participante.evento
    campos_ativos = CampoFormulario.objects.filter(evento=evento, is_active=True).order_by('ordem')

    if request.method == 'POST':
        form = EditarParticipanteForm(campos_ativos, participante, request.POST)
        if form.is_valid():
            
            # 1. Salva os campos diretos do modelo ParticipanteEvento
            # Procura o nome completo e o status de trabalho nos dados do formulário dinâmico
            nome_completo_salvo = ''
            trabalha_no_evento_salvo = False
            for campo_obj in campos_ativos:
                field_name = campo_obj.nome_campo.lower().replace(' ', '_').replace('.', '').replace('?', '')
                valor_campo = form.cleaned_data.get(field_name, '')
                
                if campo_obj.nome_campo == 'Nome completo':
                    nome_completo_salvo = valor_campo
                
                if campo_obj.nome_campo == 'Vou trabalhar no Evento':
                    trabalha_no_evento_salvo = True if valor_campo else False

            # Captura o valor da checkbox de pagamento
            pagamento_recebido = form.cleaned_data.get('pagamento_recebido', False)

            # Atualiza e salva o modelo do Participante
            participante.nome_completo = nome_completo_salvo
            participante.trabalha_no_evento = trabalha_no_evento_salvo
            participante.pagamento_recebido = pagamento_recebido
            participante.save()

            # 2. Salva as respostas dos campos dinâmicos
            for campo_obj in campos_ativos:
                field_name = campo_obj.nome_campo.lower().replace(' ', '_').replace('.', '').replace('?', '')
                valor_campo = form.cleaned_data.get(field_name, '')
                
                resposta, created = RespostaCampo.objects.get_or_create(
                    participante=participante,
                    campo=campo_obj,
                    defaults={'valor': ''}
                )
                resposta.valor = str(valor_campo) if valor_campo is not None else ''
                resposta.save()


            messages.success(request, 'Participante atualizado com sucesso!')
            return redirect('detalhes_participante', participante_id=participante.id)
    else:
        form = EditarParticipanteForm(campos_ativos, participante)
    
    context = {
        'form': form,
        'participante': participante,
    }
    return render(request, 'eventos/editar_participante.html', context)

def detalhes_participante(request, participante_id):
    participante = get_object_or_404(ParticipanteEvento, pk=participante_id)
    respostas = RespostaCampo.objects.filter(participante=participante)

    context = {
        'participante': participante,
        'respostas': respostas,
    }
    return render(request, 'eventos/detalhes_participante.html', context)

def pagamento_agora(request, participante_id):
    """
    Gera um link de pagamento do Mercado Pago para um participante.
    Inclui lógica robusta para encontrar o e-mail, mesmo que não esteja salvo no modelo.
    """
    participante = get_object_or_404(ParticipanteEvento, pk=participante_id)
    evento = participante.evento

    if not evento.valor or float(evento.valor) <= 0:
        messages.error(request, "O valor do evento não está definido ou é zero. Não é possível gerar o link de pagamento.")
        return redirect('detalhes_participante', participante_id=participante.id)

    # 1. LÓGICA DE RECUPERAÇÃO DO E-MAIL
    email_pagador = None

    # Tenta obter o e-mail diretamente do campo do modelo (se existir e estiver preenchido)
    if hasattr(participante, 'email') and participante.email:
        email_pagador = participante.email
    
    # Se o e-mail ainda não foi encontrado, busca nos campos dinâmicos
    if not email_pagador:
        try:
            # Assume que o nome do campo dinâmico de e-mail é 'E-mail'
            email_response = RespostaCampo.objects.get(
                participante=participante,
                campo__nome_campo='E-mail'
            )
            email_pagador = email_response.valor
        except RespostaCampo.DoesNotExist:
            # Se não for possível encontrar o e-mail, exibe erro e para
            messages.error(request, "Erro: Não foi possível encontrar o e-mail do participante. Inscrição incompleta.")
            return redirect('detalhes_participante', participante_id=participante.id)

    # Fim da lógica de recuperação do e-mail

    try:
        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

        preference_data = {
            "items": [
                {
                    "title": f"Inscrição - {evento.titulo}",
                    "quantity": 1,
                    "unit_price": float(evento.valor),
                    "id": participante.id,
                    "category_id": "services",
                }
            ],
            "back_urls": {
                "success": request.build_absolute_uri(f'/eventos/pagamento/sucesso/{participante.id}/'),
                "pending": request.build_absolute_uri(f'/eventos/pagamento/pendente/{participante.id}/'),
                "failure": request.build_absolute_uri(f'/eventos/pagamento/falha/{participante.id}/'),
            },
            # USA A VARIÁVEL email_pagador GARANTIDA
            "payer": { 
                "email": email_pagador 
            },
            "external_reference": str(participante.id),
            "notification_url": request.build_absolute_uri(
                reverse('mercado_pago_ipn')
            ),
        }

        preference_response = sdk.preference().create(preference_data)

        if 'response' not in preference_response or 'init_point' not in preference_response['response']:
            error_details = preference_response.get('error', {})
            error_message = error_details.get('message', 'Erro desconhecido da API do Mercado Pago.')
            raise Exception(f"Erro na criação da preferência: {error_message}")

        return redirect(preference_response['response']['init_point'])

    except Exception as e:
        # Exibe o erro de forma mais amigável, mas registra o erro real para depuração
        messages.error(request, f"Ocorreu um erro ao gerar o link de pagamento: {e}")
        return redirect('detalhes_participante', participante_id=participante.id)

# Manter o decorador nas views de retorno
@csrf_exempt
def pagamento_sucesso(request, participante_id):
    participante = get_object_or_404(ParticipanteEvento, pk=participante_id)
    participante.pagamento_recebido = True
    participante.save()
    messages.success(request, 'Pagamento confirmado com sucesso! O status foi atualizado.')
    return redirect('detalhes_participante', participante_id=participante.id)

@csrf_exempt
def pagamento_pendente(request, participante_id):
    messages.warning(request, 'O pagamento está pendente de confirmação. O status será atualizado em breve.')
    participante = get_object_or_404(ParticipanteEvento, pk=participante_id)
    return redirect('detalhes_participante', participante_id=participante.id)

@csrf_exempt
def pagamento_falha(request, participante_id):
    messages.error(request, 'O pagamento não pôde ser concluído. Por favor, tente novamente.')
    participante = get_object_or_404(ParticipanteEvento, pk=participante_id)
    return redirect('detalhes_participante', participante_id=participante.id)


def lista_eventos(request):
    """
    Lista todos os eventos disponíveis.
    """
    # CORREÇÃO: Usar o campo correto 'data_inicio'
    eventos = Evento.objects.all().order_by('-data_inicio')
    return render(request, 'eventos/lista_eventos.html', {'eventos': eventos})

# Coloque esta função no final do seu arquivo eventos/views.py

@csrf_exempt
def mercado_pago_ipn(request):
    """
    View que recebe as notificações automáticas (IPN) do Mercado Pago.
    Atualiza o status do participante (pagamento_recebido).
    Retorna 200 OK em todos os caminhos para evitar reenvio do MP.
    """
    # 1. Resposta para Testes (GET)
    if request.method == 'GET':
        # Retorna 200 OK para o Mercado Pago testar a URL (como visto no seu screenshot de sucesso)
        return HttpResponse('IPN URL OK', status=200) 

    # 2. Processamento da Notificação (POST)
    if request.method == 'POST':
        # As notificações geralmente vêm como form data (request.POST) ou query params
        data = request.POST 
        topic = data.get('topic') or data.get('type')
        resource_id = data.get('id')

        # Processa apenas notificações de pagamento válidas
        if topic == 'payment' and resource_id:
            try:
                sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

                # Consulta o status real do pagamento na API
                # Se a consulta falhar, a exceção será capturada no final.
                payment_response = sdk.payment().get(resource_id)
                payment = payment_response.get('response')

                if payment and payment['status'] == 'approved':
                    # O external_reference foi definido como participante.id na view pagamento_agora
                    participante_id = payment.get('external_reference')
                    
                    if participante_id:
                        # Busca o participante pelo ID fornecido no external_reference
                        # Isso garante que a notificação está ligada ao participante correto.
                        participante = ParticipanteEvento.objects.get(pk=int(participante_id))

                        if not participante.pagamento_recebido:
                            participante.pagamento_recebido = True
                            participante.save()
                            # Opcional: Adicione aqui uma função de log.

                # 3. CRÍTICO: Retornar 200 OK é o requisito do Mercado Pago.
                # Se chegarmos aqui, a notificação foi processada ou o status não era 'approved'.
                return HttpResponse('Notification processed successfully', status=200)

            except ParticipanteEvento.DoesNotExist:
                # O participante não foi encontrado, mas retorna 200 OK para evitar reenvio do MP
                return HttpResponse('Participante not found, accepted', status=200) 
            
            except Exception as e:
                # Captura qualquer erro de consulta de API ou SDK e retorna 200 OK para evitar reenvio
                print(f"Erro ao processar IPN: {e}")
                return HttpResponse('Error processing notification', status=200)

    # 4. Resposta padrão para qualquer requisição inválida ou que não seja POST/GET de teste
    return HttpResponse(status=200)