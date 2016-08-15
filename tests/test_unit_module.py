import cct.module
import os
import unittest

from cct.module import Modules
from cct.module import Module

class TestModules(unittest.TestCase):

    def test_find_modules(self):
        modules = Modules()
        path = os.path.abspath(os.path.dirname(cct.module.__file__)) + "/modules"
        modules.find_modules(path)

    def test_module_getenv_none(self):
        dummy = Module("dummy", None)
        self.assertIsNone(dummy.getenv("bar"))

    def test_module_getenv(self):
        dummy = Module("dummy", None)
        dummy.environment = { "foo": "foovalue"}
        self.assertEquals(dummy.getenv("foo"), "foovalue")

    def test_module_getenv_form_host(self):
        dummy = Module("dummy", None)
        os.environ['foo'] = "foovalue"
        self.assertEquals(dummy.getenv("foo"), "foovalue")

    def test_module_getenv_override(self):
        dummy = Module("dummy", None)
        dummy.environment = { "foohost": "barvalue"}
        os.environ['foohost'] = "foovalue"
        self.assertEquals(dummy.getenv("foohost"), "foovalue")

