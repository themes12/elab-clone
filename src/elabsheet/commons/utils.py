import re
import ipaddress

from sandbox import Sandbox

def staff_check(user):
    return user.is_staff


def username_from_student_id(student_id):
    """
    >>> username_from_student_id('36052850')
    'b3605285'
    >>> username_from_student_id('51551111')
    'b5155111'
    >>> username_from_student_id('5355123456')
    'b5355123456'
    """
    # starting from year 2553, all digits are used in the user ID
    if (int(student_id[:2]) >= 53):
        return 'b' + student_id
    else:
        return 'b' + student_id[:-1]


def get_svn_revision():
    try:
        import os.path
        import pysvn
        client = pysvn.Client()
        path = os.path.join(os.path.dirname(__file__),'..')
        entry = client.info(path)
        return entry.revision.number
    except:
        return 0


def find_extension(lang):
    lang_extensions = Sandbox.get_languages_with_extensions()
    for l in lang_extensions:
        if l[0]==lang:
            return l[1]
    return ''


IP_ADDR_PATTERN = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
IP_RANGE_PATTERN = IP_ADDR_PATTERN + "-" + IP_ADDR_PATTERN
IP_ADDR_RE = re.compile('^' + IP_ADDR_PATTERN + '$')
IP_RANGE_RE = re.compile('^' + IP_RANGE_PATTERN + '$')

def parse_address_list(text):
    '''
    Take multi-line text and convert into a list of IP address ranges or
    single IP addresses, with each IP represented by a single 32-bit
    integer.  Entries may be separated by either commas or newlines.

    Currently, only IPv4 addresses are supported.

    >>> parse_address_list("158.108.2.71")
    [2657878599]

    >>> parse_address_list("158.108.2.71,158.108.4.10")
    [2657878599, 2657879050]

    >>> parse_address_list("158.108.2.71, 158.108.4.10, 10.16.0.0 - 10.16.255.255")
    [2657878599, 2657879050, (168820736, 168886271)]
    '''
    text = text.replace(',','\n').replace(' ','')
    addr_list = []
    for line in text.split('\n'):
        line = line.strip()
        if line == '' or line.startswith('#'):
            continue

        # try address range first
        m = IP_RANGE_RE.match(line)
        if m:
            ip1 = int(ipaddress.IPv4Address(m.group(1)))
            ip2 = int(ipaddress.IPv4Address(m.group(2)))
            if ip2 < ip1:
                raise Exception("Invalid IP range: {}".format(line))
            addr_list.append((ip1,ip2))
            continue

        # then try a single address
        m = IP_ADDR_RE.match(line)
        if m:
            ip = int(ipaddress.IPv4Address(m.group(1)))
            addr_list.append(ip)
            continue

        # should not reach here
        raise Exception("Invalid IP or IP range: {}".format(line))

    return addr_list


def address_in_list(addr,addr_list):
    '''
    Check whether the given address falls inside the given address list

    >>> alist = parse_address_list("158.108.2.71, 158.108.4.10, 10.16.0.0 - 10.16.255.255")
    >>> address_in_list("158.108.2.71",alist)
    True
    >>> address_in_list("158.108.2.72",alist)
    False
    >>> address_in_list("10.16.0.0",alist)
    True
    >>> address_in_list("10.16.5.8",alist)
    True
    >>> address_in_list("10.16.255.255",alist)
    True
    >>> address_in_list("10.17.2.5",alist)
    False
    '''
    addr_n = int(ipaddress.IPv4Address(addr))
    for entry in addr_list:
        if isinstance(entry,tuple):
            lower,upper = entry
            if lower <= addr_n <= upper:
                return True
        elif isinstance(entry,int):
            if addr_n == entry:
                return True
        else:
            assert(False)
    return False
            

def get_remote_addr_from_request(request):
    """
    Returns remote IP address from request
    """
    try:
        if 'HTTP_X_ELAB_CLIENT_IP' in request.META:    
            return request.META['HTTP_X_ELAB_CLIENT_IP']
        elif 'HTTP_X_REAL_IP' in request.META:    
            return request.META['HTTP_X_REAL_IP']
        return request.META['REMOTE_ADDR']
    except:
        return None
