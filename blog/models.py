from django.db import models
from django.contrib.auth.models import User # Supondo que você já tenha isso

class CarouselImage(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name="Título (Opcional)")
    image = models.ImageField(upload_to='carousel_images/', verbose_name="Imagem")
    is_active = models.BooleanField(default=True, verbose_name="Ativa no Carrossel?")
    order = models.IntegerField(default=0, verbose_name="Ordem de Exibição")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Imagem do Carrossel"
        verbose_name_plural = "Imagens do Carrossel"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title if self.title else f"Imagem {self.id}"

class PostMmrt(models.Model) :
    author = models.CharField(max_length=50)
    pub_date = models.DateField("Data de publicação")
    titulo_blog = models.CharField(max_length=200)
    conteudo_artigo = models.TextField()

    def __str__(self):
        return self.titulo_blog
    
    
class Comment(models.Model):
  
    post = models.ForeignKey(PostMmrt, on_delete=models.CASCADE, related_name='comments')

    name = models.CharField(max_length=255, blank=False)
    
    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    approved_comment = models.BooleanField(default=False)

    def approve(self):
        self.approved_comment = True
        self.save()

    def __str__(self):
        return self.name
