from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.hashers import make_password
from django.contrib import messages

from django.contrib.auth import get_user_model
User = get_user_model()

from accounts.forms import AccountSignupForm

# Create your views here.
class AccountCreateView(CreateView):
    model = User
    template_name = 'registration/signup_form.html'
    form_class = AccountSignupForm
    success_url = reverse_lazy('login')
    success_message = 'Usuário criado com sucesso!'

    def form_valid(self, form) -> HttpResponse:
        form.instance.password = make_password(form.instance.password)
        form.save()
        messages.success(self.request, self.success_message)

        return super(AccountCreateView, self).form_valid(form)