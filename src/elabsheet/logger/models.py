from django.db import models
from django.contrib.auth.models import User, AnonymousUser
from django.utils import timezone
from commons.utils import get_remote_addr_from_request
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

class Log(models.Model):
    user = models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL)
    request_ip = models.GenericIPAddressField(blank=True,null=True)
    event = models.CharField(max_length=50,db_index=True)
    comment = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True,db_index=True)

    def __str__(self):
        if self.comment=="":
            return "%s: [%s] (%s/%s)" % (self.event.upper(), 
                                         timezone.localtime(self.created_at),
                                         self.user,
                                         self.request_ip)
        else:
            return "%s: %s [%s] (%s/%s)" % (self.event.upper(), 
                                            self.comment,
                                            timezone.localtime(self.created_at),
                                            self.user,
                                            self.request_ip)

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def create(event,request=None,comment="",user=None,request_ip=None):
        if request!=None:
            if user==None:
                if not isinstance(request.user, AnonymousUser):
                    user = request.user
            if request_ip==None:
                request_ip = get_remote_addr_from_request(request)

        log = Log(user=user, 
                  request_ip=request_ip,
                  event=event, 
                  comment=comment)
        log.save()


@receiver(user_logged_in)
def log_user_logged_in(sender, request, user, **kwargs):
    Log.create("login", request, user=user)

@receiver(user_logged_out)
def log_user_logged_out(sender, request, user, **kwargs):
    Log.create("logout", request, user=user)

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    Log.create("failed-login", request,
               comment=("user: %s" % request.POST['username']))
