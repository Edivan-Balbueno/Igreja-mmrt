from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    data_nascimento = models.DateField(
        "Data de nascimento",
        null=True,
        blank=True
    )
    cpf = models.CharField(
        "CPF",
        max_length=11,
        null=True,
        blank=True
    )