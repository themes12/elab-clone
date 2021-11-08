import doctest
from django.test import SimpleTestCase
from . import utils

class UtilsModuleTest(SimpleTestCase):
    def test_doctests(self):
        doctest.testmod(utils)
