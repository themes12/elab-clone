from django.template import Library
from commons.utils import get_remote_addr_from_request

register = Library()

def remote_addr(request):
    """
    Returns remote ip address
    """
    remote = get_remote_addr_from_request(request)
    if remote is not None:
        return remote
    else:
        return ""
remote_addr = register.simple_tag(remote_addr)
