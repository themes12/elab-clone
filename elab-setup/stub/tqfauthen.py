from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

class WebBackend:
    """Authenticate using Web portal for tqf
    """
    def check_password(self, username, password):
        from urllib.request import urlopen
        from urllib.parse import urlencode
        username = username.split('@')[0]
        try:
            result = urlopen('https://tqf.cpe.ku.ac.th/authen/',
                             urlencode({'login': username,
                                        'password': password}).encode())
            if result:
                data = result.read().decode()
                return data == 'OK'
            else:
                return False
        except:
            return False

    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Since user has to be added to section before using
            # any functionality, we do not create new IMAP user on
            # the fly
            return None 

        if self.check_password(username, password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

