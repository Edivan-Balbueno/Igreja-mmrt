# eventos/forms.py

from django import forms
from .models import Evento, CampoFormulario, EventoMidia, ParticipanteEvento, RespostaCampo
from django.forms import CheckboxInput, RadioSelect

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['titulo', 'data_inicio', 'data_fim', 'horario', 'local', 'valor', 'descricao']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_fim': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'horario': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'descricao': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'data_inicio': 'Data de Início',
            'data_fim': 'Data de Fim',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_inicio'].input_formats = ['%Y-%m-%d']
        self.fields['data_fim'].input_formats = ['%Y-%m-%d']

class EventoEditForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            'titulo',
            'slug',
            'data_inicio',
            'data_fim',
            'horario',
            'local',
            'valor',
            'descricao',
            'is_active'
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_fim': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'horario': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # força o formato correto nas instâncias
        self.fields['data_inicio'].input_formats = ['%Y-%m-%d']
        self.fields['data_fim'].input_formats = ['%Y-%m-%d']



class CampoFormularioForm(forms.ModelForm):
    class Meta:
        model = CampoFormulario
        fields = ['nome_campo', 'tipo_campo', 'is_active', 'is_required', 'opcoes']
        widgets = {
            'opcoes': forms.TextInput(attrs={'placeholder': 'Ex: Sim,Não'}),
        }

class EventoMidiaForm(forms.ModelForm):
    class Meta:
        model = EventoMidia
        fields = ['media_file', 'descricao']
        widgets = {
            'media_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'media_file': 'Arquivo de Mídia',
            'descricao': 'Descrição (opcional)',
        }

class GerenciarCamposForm(forms.Form):
    nome_completo = forms.BooleanField(label="Nome Completo", required=False)
    telefone = forms.BooleanField(label="Telefone", required=False)
    email = forms.BooleanField(label="E-mail", required=False) # Adicionar este campo
    endereco = forms.BooleanField(label="Endereço", required=False) # Adicionar este campo
    tem_lider = forms.BooleanField(label="Você tem Líder?", required=False)
    participa_igreja = forms.BooleanField(label="Você participa da Igreja MMRT?", required=False) # Adicionar este campo
    expectativas = forms.BooleanField(label="Expectativas para o Encontro", required=False)
    pode_participar = forms.BooleanField(label="Você pode participar?", required=False) # Adicionar este campo
    nome_amigo = forms.BooleanField(label="Nome de um Amigo ou Familiar", required=False)
    telefone_amigo = forms.BooleanField(label="Telefone do Amigo ou Familiar", required=False)
    trabalhar_no_evento = forms.BooleanField(label="Vou trabalhar no Evento", required=False)

class CadastroParticipanteForm(forms.Form):
    def __init__(self, campos_ativos, *args, **kwargs):
        super(CadastroParticipanteForm, self).__init__(*args, **kwargs)
        
        # Garante que os campos sejam criados na ordem correta
        for campo in campos_ativos:
            # Normaliza o nome do campo para usar como chave do dicionário
            field_name = campo.nome_campo.lower().replace(' ', '_').replace('.', '').replace('?', '')

            if campo.tipo_campo == 'texto':
                self.fields[field_name] = forms.CharField(label=campo.nome_campo, required=campo.is_required, max_length=255)
            elif campo.tipo_campo == 'multitexto':
                self.fields[field_name] = forms.CharField(label=campo.nome_campo, required=campo.is_required, widget=forms.Textarea)
            elif campo.tipo_campo == 'email':
                self.fields[field_name] = forms.EmailField(label=campo.nome_campo, required=campo.is_required)
            elif campo.tipo_campo == 'numero':
                self.fields[field_name] = forms.IntegerField(label=campo.nome_campo, required=campo.is_required)
            elif campo.tipo_campo == 'radio':
                choices = [(o.strip(), o.strip()) for o in campo.opcoes.split(',')]
                self.fields[field_name] = forms.ChoiceField(label=campo.nome_campo, required=campo.is_required, choices=choices, widget=RadioSelect)
            elif campo.tipo_campo == 'checkbox':
                self.fields[field_name] = forms.BooleanField(label=campo.nome_campo, required=False, widget=CheckboxInput())

class EditarParticipanteForm(forms.Form):
    def __init__(self, campos_ativos, participante, *args, **kwargs):
        super(EditarParticipanteForm, self).__init__(*args, **kwargs)
        
        # Adicione o campo de pagamento e defina o valor inicial
        self.fields['pagamento_recebido'] = forms.BooleanField(
            label="Pagamento Recebido",
            required=False,
            initial=participante.pagamento_recebido
        )

        respostas_existentes = {resposta.campo.nome_campo: resposta.valor for resposta in participante.respostas.all()}

        for campo in campos_ativos:
            field_name = campo.nome_campo.lower().replace(' ', '_').replace('.', '').replace('?', '')
            initial_value = respostas_existentes.get(campo.nome_campo, None)

            if campo.tipo_campo == 'texto':
                self.fields[field_name] = forms.CharField(label=campo.nome_campo, required=campo.is_required, max_length=255, initial=initial_value)
            elif campo.tipo_campo == 'multitexto':
                self.fields[field_name] = forms.CharField(label=campo.nome_campo, required=campo.is_required, widget=forms.Textarea, initial=initial_value)
            elif campo.tipo_campo == 'email':
                self.fields[field_name] = forms.EmailField(label=campo.nome_campo, required=campo.is_required, initial=initial_value)
            elif campo.tipo_campo == 'numero':
                self.fields[field_name] = forms.IntegerField(label=campo.nome_campo, required=campo.is_required, initial=initial_value)
            elif campo.tipo_campo == 'radio':
                choices = [(o.strip(), o.strip()) for o in campo.opcoes.split(',')]
                self.fields[field_name] = forms.ChoiceField(label=campo.nome_campo, required=campo.is_required, choices=choices, widget=RadioSelect, initial=initial_value)
            elif campo.tipo_campo == 'checkbox':
                initial_bool = initial_value.lower() == 'true' if initial_value else False
                self.fields[field_name] = forms.BooleanField(label=campo.nome_campo, required=False, initial=initial_bool, widget=CheckboxInput())