import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = False 

ALLOWED_HOSTS = ['__HOST_NAME__']

SITE_NAME = '__SITE_NAME__'

SITE_PREFIX = "/__ELAB_NAME__"
FORCE_SCRIPT_NAME = SITE_PREFIX

SECRET_KEY = 'u@3u=_o9+xr54$*ic0jstqsb&q@+l6a#+wiqm3h_b$kvv6mg_w_new__ELAB_NAME__'
SESSION_COOKIE_PATH = SITE_PREFIX + "/"
SESSION_COOKIE_NAME = 'sessionid___ELAB_NAME__'
CSRF_COOKIE_PATH = SITE_PREFIX + '/'

ADMINS = (
        ('Chaiporn Jaikaeo', 'chaiporn.j@ku.ac.th'),
        ('Jittat Fakcharoenphol', 'jtf@ku.ac.th'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '__ELAB_NAME__',
        'USER': '__ELAB_NAME__',
        'PASSWORD': '__DB_PASSWD__',
        'OPTIONS': {
            'autocommit': True,
        },
        'HOST': '__DB_HOST__',   # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '__DB_PORT__',   # Set to empty string for default. Not used with sqlite3.
    },
}

STATIC_URL = '/__ELAB_NAME___static/'
STATIC_ROOT = os.path.join(BASE_DIR,'public','static')

MEDIA_URL = '/__ELAB_NAME___media/'
MEDIA_ROOT = os.path.join(BASE_DIR,'public','media')

USE_BOX_IN_SANDBOX = True

HTTPS_LOGIN = True

LOGIN_URL = SITE_PREFIX + '/accounts/login'
LOGIN_REDIRECT_URL = SITE_PREFIX + '/'
LOGOUT_REDIRECT_URL = SITE_PREFIX + '/'

SEPARATE_GRADING = True

GRADER_OUTPUT_LOG = False

SEND_BROKEN_LINK_EMAILS = True

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'lab.backends.tqfauthen.WebBackend',
    #'django_auth_ldap.backend.LDAPBackend',
)

# Uncomment the following and modify proper settings for LDAP authentication
############################
# LDAP Settings
############################
#import ldap
#from django_auth_ldap.config import LDAPSearch
#AUTH_LDAP_SERVER_URI = "ldap://ldap.ku.ac.th"
#
#AUTH_LDAP_BIND_DN = ""
#AUTH_LDAP_BIND_PASSWORD = ""
#AUTH_LDAP_USER_SEARCH = LDAPSearch("dc=ku,dc=ac,dc=th",
#    ldap.SCOPE_SUBTREE, "(uid=%(user)s)")
#AUTH_LDAP_USER_ATTR_MAP = {"first_name": "first-name", "last_name": "last-name"}
