from django.conf import settings
from django.contrib.auth.models import User
from lab.models import DirectToLabAccount

class DirectToLabBackend:
    """
    Authenticate against the direct-to-lab accounts

    Once authenticated, the backend will log in with the corresponding user,
    then store the reference to the direct-to-lab account instance as a session
    variable.
    """

    def authenticate(self, request, username=None, password=None):
        try:
            da = DirectToLabAccount.objects.get(username=username)
            if da.password == password:
                request.session['DIRECT-TO-LAB'] = {
                        'labinsec' : da.labinsec.id,
                        }
                return da.user
        except DirectToLabAccount.DoesNotExist:
            pass

        if 'DIRECT-TO-LAB' in request.session:
            del request.session['DIRECT-TO-LAB']
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
