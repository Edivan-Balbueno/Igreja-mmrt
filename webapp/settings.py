import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Carrega as variáveis do arquivo .env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# CONTROLE DE AMBIENTE (DESENVOLVIMENTO VS PRODUÇÃO)
# ==============================================================================
IS_PRODUCTION = os.getenv('DJANGO_ENV') == 'production'

if IS_PRODUCTION:
  # Configurações de Produção (PythonAnywhere)
  DEBUG = False
  ALLOWED_HOSTS = ['balbuen.pythonanywhere.com']
  BASE_URL = 'https://balbuen.pythonanywhere.com'
  MP_REDIRECT_URI = (
      'https://balbuen.pythonanywhere.com/eventos/perfil/mp/callback/'
  )
else:
  # Configurações de Desenvolvimento Local
  DEBUG = True
  ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '192.168.100.194']
  BASE_URL = 'http://127.0.0.1:8000'
  MP_REDIRECT_URI = os.getenv(
      'MP_REDIRECT_URI', 'http://127.0.0.1:8000/eventos/perfil/mp/callback/'
  )

# ==============================================================================
# CHAVES E INTEGRAÇÕES
# ==============================================================================
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-tf0gr--97sr5#g2r64fi*ij&6poik7za#^mqsj9zm444g9++ru',
)

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
MERCADO_PAGO_ACCESS_TOKEN = os.getenv('MERCADO_PAGO_ACCESS_TOKEN')
MP_CLIENT_ID = os.getenv('MP_CLIENT_ID', '4904084460965448')
MP_CLIENT_SECRET = os.getenv('MP_CLIENT_SECRET', 'WqOJKVUb274Ry56KkJH3cF2gw3YlROu2')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'blog.apps.BlogConfig',
    'accounts.apps.AccountsConfig',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'django_summernote',
    'eventos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'webapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'webapp.wsgi.application'

# ==============================================================================
# CONFIGURAÇÃO DE BANCO DE DADOS
# ==============================================================================
IS_PRODUCTION = os.getenv('DJANGO_ENV') == 'production'

if IS_PRODUCTION:
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.mysql',
          'NAME': os.getenv('MYSQL_DATABASE'),
          'USER': os.getenv('MYSQL_USER'),
          'PASSWORD': os.getenv('MYSQL_PASSWORD'),
          'HOST': os.getenv('MYSQL_HOST'),
          'PORT': os.getenv('MYSQL_PORT', '3306'),
          'OPTIONS': {
              
              'charset': 'utf8mb4',
          },
      }
  }
else:
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': BASE_DIR / 'db.sqlite3',
      }
  }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.NumericPasswordValidator'
        ),
    },
]

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static & Media files
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'public')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/index'
LOGOUT_REDIRECT_URL = '/perfil'
AUTH_USER_MODEL = 'accounts.CustomUser'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Configurações de E-mail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

QRCODE_LOGO_PATH = os.path.join(BASE_DIR, 'static', 'images', 'logoqrcode.JPEG')