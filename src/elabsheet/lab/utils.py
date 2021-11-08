
def generate_random_password(password_len=40):
    """
    Generates a password password_len characters in lenght.

    @param password_len: lenght of the generated password
    @type password_len: int
    """
    VALID_CHARS = '1234567890qwertyuiopasdfghjklzxcvbnm,.-\'' \
                  '+!"#$%&/()=?QWERTYUIOP*ASDFGHJKL^ZXCVBNM;:_'
    from random import choice
    return ''.join([ choice(VALID_CHARS) for i in range(password_len) ])
