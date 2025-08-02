# blog/forms.py
from django.forms import ModelForm # Já existe
from django import forms # Certifique-se de importar forms
from .models import Comment, PostMmrt, CarouselImage # Importe PostMmrt também
from django_summernote.widgets import SummernoteWidget
# from django_summernote.fields import SummernoteTextField # Pode ser útil, mas SummernoteWidget é o essencial aqui

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'comment']

class PostMmrtForm(ModelForm):
    class Meta:
        model = PostMmrt
        fields = ['titulo_blog', 'conteudo_artigo', 'pub_date']
        widgets = {
            'conteudo_artigo': SummernoteWidget(),
            'pub_date': forms.DateInput(attrs={'type': 'date'}), # Adiciona um seletor de data HTML5
        }
        

class CarouselImageForm(forms.ModelForm):
    class Meta:
        model = CarouselImage
        fields = ['title', 'image', 'is_active', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Título da Imagem',
            'image': 'Ficheiro da Imagem', # Alterado para 'Ficheiro da Imagem'
            'is_active': 'Ativa no Carrossel?',
            'order': 'Ordem de Exibição',
        }
