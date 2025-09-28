# eventos/models.py
import qrcode 
import os
from PIL import Image 
from io import BytesIO
from django.core.files import File
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify

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
    # criador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='eventos_criados') # Exemplo, se você tiver este campo
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['-data_inicio']

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        # 1. Geração do SLUG (Antes do primeiro save para garantir o ID e o SLUG)
        if not self.slug or (self.pk and self.slug != slugify(self.titulo)):
            self.slug = slugify(self.titulo)

        # Se for novo, faz o primeiro save para obter o ID (PK)
        if is_new:
             super().save(*args, **kwargs)

        # 2. Geração do QR CODE (Apenas se não existir)
        if not self.qrcode:
            self._generate_qrcode()
            # Chama o save novamente para salvar o campo 'qrcode'
            # Usamos update_fields para evitar o loop infinito
            super().save(update_fields=['qrcode', 'slug'])
            return

        # 3. Salvamento Final: Para edições normais ou se o QR Code já existe
        super().save(*args, **kwargs)

    def _generate_qrcode(self):
        """Lógica interna para gerar o QR Code com o logo."""
        
        # 1. Constrói o Link usando o SLUG (necessário para a URL)
        link_para_evento = settings.BASE_URL + reverse('detalhes_evento', kwargs={'slug': self.slug})
        
        # 2. Gera o QR Code base
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H, # Alta correção para o logo
            box_size=10,
            border=4,
        )
        qr.add_data(link_para_evento)
        qr.make(fit=True)

        # 3. Cria a imagem do QR Code
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        
        # 4. Tenta inserir o Logo
        try:
            # Pega o caminho da configuração
            logo_path = settings.QRCODE_LOGO_PATH
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                
                qr_w, qr_h = qr_img.size
                logo_size = qr_w // 5 # Logo com 20% do tamanho do QR
                
                # Redimensiona e centraliza o logo
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                pos = ((qr_w - logo_size) // 2, (qr_h - logo_size) // 2)
                
                # Cola o logo no centro
                qr_img.paste(logo, pos)
        
        except Exception as e:
            # Ignora o erro se o logo não puder ser inserido, mas gera o QR code
            print(f"Erro ao inserir logo no QR Code: {e}") 

        # 5. Salva a imagem no campo do modelo
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        
        file_name = f'qrcode-{self.slug}.png' # Usar slug no nome do arquivo é mais seguro
        self.qrcode.save(file_name, File(buffer), save=False) # save=False evita loop infinito

# Modelo para os campos do formulário dinâmico
class CampoFormulario(models.Model):
    CAMPO_CHOICES = [
        ('texto', 'Texto Curto'),
        ('multitexto', 'Texto Longo'),
        ('numero', 'Número'),
        ('email', 'Email'),
        ('radio', 'Opções de Rádio'),
        ('checkbox', 'Caixa de Seleção'),
    ]

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='campos')
    nome_campo = models.CharField(max_length=100)
    tipo_campo = models.CharField(max_length=20, choices=CAMPO_CHOICES)
    opcoes = models.CharField(max_length=200, blank=True, null=True, help_text="Para campos de rádio, separe as opções por vírgula. Ex: Sim,Não")
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordem']

    def __str__(self):
        return f"{self.nome_campo} ({self.get_tipo_campo_display()})"

# Modelo para o participante do evento
class ParticipanteEvento(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='participantes')
    nome_completo = models.CharField(max_length=255, blank=True, null=True) # Adicione este campo
    trabalha_no_evento = models.BooleanField(default=False)
    status_pagamento = models.CharField(max_length=20, choices=[('pago', 'Pago'), ('pendente', 'Pendente')], default='pendente')
    pagamento_recebido = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Participante do evento {self.evento.titulo}"

# Modelo para as respostas aos campos do formulário
class RespostaCampo(models.Model):
    participante = models.ForeignKey(ParticipanteEvento, on_delete=models.CASCADE, related_name='respostas')
    campo = models.ForeignKey(CampoFormulario, on_delete=models.CASCADE)
    valor = models.TextField(blank=True, null=True) # Altere esta linha!

    def __str__(self):
        return f"Resposta de {self.participante} para {self.campo.nome_campo}"

# Modelo para as mídias (fotos e vídeos) do evento
class EventoMidia(models.Model):
    MEDIA_CHOICES = [
        ('image', 'Imagem'),
        ('video', 'Vídeo'),
    ]

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='midias')
    media_file = models.FileField(upload_to='evento_midias/')
    descricao = models.CharField(max_length=255, blank=True, null=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mídia para {self.evento.titulo}"