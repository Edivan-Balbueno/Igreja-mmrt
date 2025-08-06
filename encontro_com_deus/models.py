# encontro_com_deus/models.py

from django.db import models

class Participante(models.Model):
    nome_completo = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20)
    nome_lider = models.CharField(max_length=200, blank=True, null=True)
    nome_amigo_familiar = models.CharField(max_length=200, blank=True, null=True)
    telefone_amigo_familiar = models.CharField(max_length=20, blank=True, null=True)
    expectativas = models.TextField(blank=True, null=True)
    evento_pago = models.BooleanField(default=False) # <-- NOVO CAMPO
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome_completo

class EncontroImage(models.Model):
    image = models.ImageField(upload_to='encontro_fotos/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Imagem do Encontro"
        verbose_name_plural = "Imagens do Encontro"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Imagem de {self.uploaded_at.strftime('%Y-%m-%d')}"