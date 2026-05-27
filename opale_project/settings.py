import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ===========================================================================
# SECURITY — Quick-start settings
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/
# ===========================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-4831zv5p^7l*%mqj5z1s*f(=c4h9x#)%q%lf-z=n+yg%#2t#lj'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost 127.0.0.1').split()


# ===========================================================================
# APPLICATION DEFINITION
# ===========================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Micro-applications
    'accounts',
    'organizations',
    'catalogue',
    'audit',
    'poc_apps',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise: serve static files in production (position 2, right after SecurityMiddleware)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'opale_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'opale_project.wsgi.application'


# ===========================================================================
# DATABASE — PostgreSQL 16 on port 5433
# ===========================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'opale_db'),
        'USER': os.environ.get('DB_USER', 'opale_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'opale_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5434'),
    }
}


# ===========================================================================
# CUSTOM USER MODEL
# ===========================================================================

AUTH_USER_MODEL = 'accounts.Utilisateur'


# ===========================================================================
# ACTIVE DIRECTORY & SSO CONFIGURATION
# ===========================================================================

AUTHENTICATION_BACKENDS = [
    'accounts.backends.ActiveDirectoryBackend',
    'django.contrib.auth.backends.ModelBackend',
]

ACTIVE_DIRECTORY = {
    'SERVER': 'ldap://localhost:389',
    'DOMAIN': 'art.cm',
    'BASE_DN': 'dc=art,dc=cm',
    'MOCK_MODE': False,  # Désactivé pour interroger le vrai serveur LDAP Docker en local
    'MOCK_USERS': {
        'j.dupont': {
            'password': 'password123',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'email': 'j.dupont@art.cm',
            'department': 'Direction Technique',
            'role': 'MANAGER',
        },
        'm.tech': {
            'password': 'password123',
            'first_name': 'Michel',
            'last_name': 'Technique',
            'email': 'm.tech@art.cm',
            'department': 'Direction Technique',
            'role': 'EMPLOYE',
        },
        'a.finance': {
            'password': 'password123',
            'first_name': 'Alice',
            'last_name': 'Comptable',
            'email': 'a.finance@art.cm',
            'department': 'Direction Financière',
            'role': 'MANAGER',
        },
        's.rh': {
            'password': 'password123',
            'first_name': 'Sarah',
            'last_name': 'Recrutement',
            'email': 's.rh@art.cm',
            'department': 'Ressources Humaines',
            'role': 'MANAGER',
        },
        # Utilisateur inédit présent dans l'AD mais inexistant dans la base locale Django au départ
        'g.ndono': {
            'password': 'password123',
            'first_name': 'Guillaume',
            'last_name': 'Ndono',
            'email': 'g.ndono@art.cm',
            'department': 'Direction Technique',
            'role': 'EMPLOYE',
        }
    }
}


# ===========================================================================
# AUTHENTICATION — Login / Logout URLs
# ===========================================================================

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/catalogue/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'


# ===========================================================================
# PASSWORD VALIDATION
# ===========================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ===========================================================================
# INTERNATIONALIZATION
# ===========================================================================

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Douala'
USE_I18N = True
USE_TZ = True


# ===========================================================================
# STATIC FILES — WhiteNoise for production
# ===========================================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise: compressed + hashed static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ===========================================================================
# DEFAULT PRIMARY KEY
# ===========================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ===========================================================================
# SECURITY HEADERS — Phase 6
# ===========================================================================

# Prevent clickjacking
X_FRAME_OPTIONS = 'DENY'

# Activate browser XSS filter
SECURE_BROWSER_XSS_FILTER = True

# Prevent MIME-type sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# Referrer policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# HttpOnly cookies — JS cannot access session or CSRF cookies
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# In production (DEBUG=False), enforce HTTPS-only cookies and HSTS
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000       # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

