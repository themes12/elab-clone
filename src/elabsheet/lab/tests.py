import unittest
import doctest
from . import admin_views
from . import views

def suite():
    # An easy way of finding all the unittests in this module
    suite = unittest.TestLoader().loadTestsFromName(__name__)
    suite.addTest(doctest.DocTestSuite(views))
    suite.addTest(doctest.DocTestSuite(admin_views))
    return suite
