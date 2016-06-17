"""
Django settings for shopelectro project.

Generated by 'django-admin startproject' using Django 1.9.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
from datetime import datetime

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'gl9syc68r%rmb*1&yzz(4%cotfpb$dy&wkb_y5_d0*be0pfulq'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'mptt',
    'blog',
    'catalog',
    'seo',
    'ecommerce',
    'shopelectro',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'shopelectro.urls'

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
                'django.core.context_processors.static',
                'ecommerce.context_processors.cart'
            ],
        },
    },
]

WSGI_APPLICATION = 'shopelectro.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'refarm.sqlite3'
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'front/build'),
    os.path.join(BASE_DIR, 'static/assets'),
]

# refarm-blog config
# Each post type can have it's own alias
# For config below, page types will have different urls:
# - article: /blog/1/
# - news: /blog/news/1/
# - navigation: /blog/navigation/1/
# All aliases in config will be trimmed with "/" symbol
APP_BLOG_POST_TYPES = {
    'navigation': {'name': 'Контакты, реквизиты, услуги', 'alias': '', 'default': True},
    'article': {'name': 'Статьи', 'alias': 'article'},
    'news': {'name': 'Новости', 'alias': 'news'},
}

PRODUCTS_TO_LOAD = 30

CRUMBS = {
    'main': 'Главная',
    'catalog': 'Каталог',
    'blog': 'Список страниц',
}

SITE_CREATED = datetime(2013, 1, 1)

LOCALHOST = 'http://127.0.0.1:8000/'
BASE_URL = 'https://www.shopelectro.ru'

IMAGE_THUMBNAIL = 'images/logo.png'

PRODUCT_MODEL = 'shopelectro.Product'
CART_ID = 'cart'
SHOP_EMAIL = ''  # Fill it in local.py
PAYMENT_OPTIONS = (
    ('cash', 'Наличные'),
    ('cashless', 'Безналичные и денежные переводы')
)


from .local import *
