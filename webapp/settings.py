
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-2h_zdb6#%kz0_n6vrozkm@mhri1)e#!c%w!#2*f%+kjnhf#a7s'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['coisasuteis.pythonanywhere.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites', # Requerido pelo allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms', # Certifique-se de que crispy-forms está aqui
    'crispy_bootstrap5', # Certifique-se de que crispy-bootstrap5 está aqui
    'qrcode_app', # O nome do seu app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware', # Adicione o middleware do allauth
]

ROOT_URLCONF = 'qrcode_generator_project.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # Este é o seu diretório de templates global na raiz do projeto
            os.path.join(BASE_DIR, 'templates'),
            # Adicione o diretório de templates do ALLAUTH para sobrescrever os padrões
            # Isso é crucial para que o Django encontre seus templates em 'templates/account/'
            os.path.join(BASE_DIR, 'templates', 'account'), # OU, se o problema for a raiz de allauth:
            # os.path.join(BASE_DIR, 'templates', 'allauth') # Depende de como vc organizou
        ],
        'APP_DIRS': True, # Mantenha True para templates específicos de seus próprios apps (qrcode_app)
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'qrcode_generator_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'coisasuteis$balbueno',      # O nome do seu DB (usuario$nomedb)
        'USER': 'coisasuteis',              # Seu nome de usuário do PythonAnywhere
        'PASSWORD': 'di09lu16',   # A senha que você definiu para o MySQL!
        'HOST': 'coisasuteis.mysql.pythonanywhere-services.com', # O host MySQL do PythonAnywhere
        'PORT': '',                         # Deixe vazio para a porta padrão
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static', # Onde você colocará seu CSS/JS personalizado
    os.path.join(BASE_DIR, 'static'), # Se você tiver um diretório 'static' na raiz do projeto
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SITE_ID = 1 # Importante para o allauth

LOGIN_REDIRECT_URL = '/' # Para onde redirecionar após o login
ACCOUNT_LOGOUT_REDIRECT_URL = '/' # Para onde redirecionar após o logout
ACCOUNT_SIGNUP_REDIRECT_URL = '/' # Para onde redirecionar após o cadastro

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email' # Permite login com nome de usuário ou e-mail
ACCOUNT_EMAIL_VERIFICATION = 'none' # Ou 'optional'/'mandatory' para verificação de e-mail
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300 # 5 minutos

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
