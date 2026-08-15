import os
from io import BytesIO
from PIL import Image
import qrcode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

User = get_user_model()


class Evento(models.Model):
  # Campos de Informação Básica
  titulo = models.CharField(max_length=200)
  slug = models.SlugField(max_length=255, unique=True, blank=True)
  descricao = models.TextField()
  data_inicio = models.DateField()
  data_fim = models.DateField(blank=True, null=True)
  horario = models.CharField(max_length=50, blank=True, null=True)
  local = models.CharField(max_length=200, blank=True, null=True)
  valor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

  # Campos de Mídia e Status
  qrcode = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
  is_active = models.BooleanField(default=True)

  # Auditoria
  criador = models.ForeignKey(User, on_delete=models.CASCADE)
  mp_receiver_id = models.CharField(
      max_length=255,
      blank=True,
      null=True,
      help_text=(
          'ID da conta do Mercado Pago (user_id) do criador para receber os'
          ' pagamentos.'
      ),
  )

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    verbose_name = 'Evento'
    verbose_name_plural = 'Eventos'
    ordering = ['-data_inicio']

  def __str__(self):
    return self.titulo

  def save(self, *args, **kwargs):
    is_new = not self.pk

    # 1. Copia o ID do Mercado Pago do criador (se existir no CustomUser)
    if hasattr(self.criador, 'mp_user_id') and self.criador.mp_user_id:
      self.mp_receiver_id = self.criador.mp_user_id

    # 2. Geração de Slug Único
    if not self.slug or (self.pk and self.slug != slugify(self.titulo)):
      slug_base = slugify(self.titulo)
      slug_unico = slug_base
      contador = 1

      while Evento.objects.filter(slug=slug_unico).exclude(pk=self.pk).exists():
        slug_unico = f'{slug_base}-{contador}'
        contador += 1

      self.slug = slug_unico

    # Primeiro save para registros novos (obter PK)
    if is_new:
      super().save(*args, **kwargs)

    # 3. Geração do QR Code
    if not self.qrcode:
      self._generate_qrcode()
      super().save(update_fields=['qrcode', 'slug', 'mp_receiver_id'])
      return

    super().save(*args, **kwargs)

  def _generate_qrcode(self):
    """Lógica interna para gerar o QR Code do evento com logo."""
    try:
      link_para_evento = settings.BASE_URL + reverse(
          'detalhes_evento', kwargs={'slug': self.slug}
      )

      qr = qrcode.QRCode(
          version=1,
          error_correction=qrcode.constants.ERROR_CORRECT_H,
          box_size=10,
          border=4,
      )
      qr.add_data(link_para_evento)
      qr.make(fit=True)

      qr_img = qr.make_image(fill_color='black', back_color='white').convert(
          'RGB'
      )

      # Tenta inserir o logo caso o caminho esteja configurado
      logo_path = getattr(settings, 'QRCODE_LOGO_PATH', None)
      if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path)
        qr_w, qr_h = qr_img.size
        logo_size = qr_w // 5
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        pos = ((qr_w - logo_size) // 2, (qr_h - logo_size) // 2)
        qr_img.paste(logo, pos)

      buffer = BytesIO()
      qr_img.save(buffer, format='PNG')
      file_name = f'qrcode-{self.slug}.png'
      self.qrcode.save(file_name, File(buffer), save=False)

    except Exception as e:
      print(f'Erro ao gerar QR Code: {e}')


# ==============================================================================
# OUTROS MODELOS DO APP EVENTOS
# ==============================================================================
class CampoFormulario(models.Model):
  CAMPO_CHOICES = [
      ('texto', 'Texto Curto'),
      ('multitexto', 'Texto Longo'),
      ('numero', 'Número'),
      ('email', 'Email'),
      ('radio', 'Opções de Rádio'),
      ('checkbox', 'Caixa de Seleção'),
  ]

  evento = models.ForeignKey(
      Evento, on_delete=models.CASCADE, related_name='campos'
  )
  nome_campo = models.CharField(max_length=100)
  tipo_campo = models.CharField(max_length=20, choices=CAMPO_CHOICES)
  opcoes = models.CharField(
      max_length=200,
      blank=True,
      null=True,
      help_text=(
          'Para campos de rádio, separe as opções por vírgula. Ex: Sim,Não'
      ),
  )
  is_required = models.BooleanField(default=False)
  is_active = models.BooleanField(default=True)
  ordem = models.IntegerField(default=0)

  class Meta:
    ordering = ['ordem']

  def __str__(self):
    return f'{self.nome_campo} ({self.get_tipo_campo_display()})'


class ParticipanteEvento(models.Model):
  evento = models.ForeignKey(
      Evento, on_delete=models.CASCADE, related_name='participantes'
  )
  nome_completo = models.CharField(max_length=255, blank=True, null=True)
  trabalha_no_evento = models.BooleanField(default=False)
  status_pagamento = models.CharField(
      max_length=20,
      choices=[('pago', 'Pago'), ('pendente', 'Pendente')],
      default='pendente',
  )
  pagamento_recebido = models.BooleanField(default=False)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f'Participante do evento {self.evento.titulo}'


class RespostaCampo(models.Model):
  participante = models.ForeignKey(
      ParticipanteEvento, on_delete=models.CASCADE, related_name='respostas'
  )
  campo = models.ForeignKey(CampoFormulario, on_delete=models.CASCADE)
  valor = models.TextField(blank=True, null=True)

  def __str__(self):
    return f'Resposta de {self.participante} para {self.campo.nome_campo}'


class EventoMidia(models.Model):
  MEDIA_CHOICES = [
      ('image', 'Imagem'),
      ('video', 'Vídeo'),
  ]

  evento = models.ForeignKey(
      Evento, on_delete=models.CASCADE, related_name='midias'
  )
  media_file = models.FileField(upload_to='evento_midias/')
  descricao = models.CharField(max_length=255, blank=True, null=True)
  media_type = models.CharField(max_length=10, choices=MEDIA_CHOICES)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f'Mídia para {self.evento.titulo}'