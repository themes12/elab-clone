#
# This file is slightly modified from
# WebPyMail - IMAP python/django web mail client 
# by Helder Guerreiro <helder@paxjulia.com> 
#
# WebPyMail can be found at: http://code.google.com/p/webpymail
# 

## As the original source is licensed under GNU GPL 3, this file and
## the project should be licensed under the same term.
## See <http://www.gnu.org/licenses/>.

import imaplib

from django.conf import settings
from django.contrib.auth.models import User, check_password
from django.db import models

class ImapBackend:
    """Authenticate using IMAP
    """
    def authenticate(self, username=None, password=None):
        try:
            host = settings.IMAP_SERVER
            port = settings.IMAP_PORT

            if host==None or host=='':    # IMAP authen disabled
                return None

            M = imaplib.IMAP4_SSL(host, port)  # always use SSL
            M.login(username, password)
            M.logout()
            valid = True
        except:
            valid = False

        if valid:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Since user has to be added to section before using
                # any functionality, we do not create new IMAP user on
                # the fly
                return None 
                # Create a new user
                #password = generatePassword()
                #user = User(username='%s@%s' % (username,host), 
                #    password=password)
                #user.is_staff = False
                #user.is_superuser = False
                #user.save()
                
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
