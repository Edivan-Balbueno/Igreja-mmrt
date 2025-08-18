# encontro_com_deus/forms.py

from django import forms
from .models import Participante

class ParticipanteForm(forms.ModelForm):
    class Meta:
        model = Participante
        fields = [
            'nome_completo',
            'telefone',
            'nome_lider',
            'nome_amigo_familiar',
            'telefone_amigo_familiar',
            'expectativas',
            'trabalho_encontro',
            'evento_pago', # Certifique-se de que este campo está aqui
        ]
        
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite o nome completo'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: (99) 99999-9999'}),
            'nome_lider': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite o nome do(a) líder (opcional)'}),
            'nome_amigo_familiar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite o nome do amigo/familiar (opcional)'}),
            'telefone_amigo_familiar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: (99) 99999-9999 (opcional)'}),
            'expectativas': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Digite suas expectativas para o Encontro (opcional)', 'rows': 4}),
        }

        labels = {
            'nome_completo': 'Nome completo',
            'telefone': 'Telefone',
            'nome_lider': 'Você tem Líder? Qual o nome dele(a)?',
            'nome_amigo_familiar': 'Nome de um Amigo ou Familiar',
            'telefone_amigo_familiar': 'Telefone do Amigo ou Familiar',
            'expectativas': 'O que espera desse Encontro? Expectativas?',
            'trabalho_encontro': 'Vou trabalhar no Encontro',
            'evento_pago': 'Pagamento (evento pago)', # Adicione este label
        }