import cct.module
import os
import unittest

from cct.module import Modules

class TestModules(unittest.TestCase):

    def test_find_modules(self):
        modules = Modules()
        path = os.path.abspath(os.path.dirname(cct.module.__file__)) + "/modules"
        modules.find_modules(path)
