import cct.module
import os
import unittest
import shutil
import tempfile

from cct.errors import CCTError
from cct.module import Modules
from cct.module import Module


class TestModules(unittest.TestCase):

    def test_find_modules(self):
        modules = Modules("dummy")
        path = os.path.abspath(os.path.dirname(cct.module.__file__)) + "/modules"
        modules.find_modules(path)

    def test_module_getenv_none(self):
        dummy = Module("dummy")
        self.assertIsNone(dummy.getenv("bar"))

    def test_module_getenv(self):
        dummy = Module("dummy")
        dummy.environment = {"foo": "foovalue"}
        self.assertEquals(dummy.getenv("foo"), "foovalue")

    def test_module_getenv_form_host(self):
        dummy = Module("dummy")
        os.environ['foo'] = "foovalue"
        self.assertEquals(dummy.getenv("foo"), "foovalue")

    def test_module_getenv_override(self):
        dummy = Module("dummy")
        dummy.environment = {"foohost": "barvalue"}
        os.environ['foohost'] = "foovalue"
        self.assertEquals(dummy.getenv("foohost"), "foovalue")

    def fetch_artifact(self, url, chksum):
        artifacts = {
            "artifacts": [
                {
                    "url": url,
                    "chksum": chksum,
                    "name": "cct",
                }
            ]
        }
        module = Module("foo")
        module._process_artifacts(artifacts['artifacts'], "/tmp")
        os.remove(module.cct_resource['cct'].path)

    def test_artifacts_fetching(self):
        url = "https://github.com/containers-tools/cct/archive/0.0.1.zip"
        chksum = "md5:d3c3fbf21935119d808bfe29fa33509c"
        self.fetch_artifact(url, chksum)

    def test_artifacts_fetching_wrong_url(self):
        url = "https://github.com/containers-tools/cct/archive/0.0.1.zip33"
        chksum = "md5:d3c3fbf21935119d808bfe29fa33509c"
        with self.assertRaises(CCTError):
            self.fetch_artifact(url, chksum)

    def test_artifacts_fetching_wrong_chksum(self):
        url = "https://github.com/containers-tools/cct/archive/0.0.1.zip"
        chksum = "md5:foo"
        with self.assertRaises(CCTError):
            self.fetch_artifact(url, chksum)

    def test_module_deps(self):
        url = "https://github.com/containers-tools/base"
        version = None
        deps = {
            "dependencies": [
                {
                    "url": url,
                    "version": version
                }
            ]
        }
        module = Module('foo')
        module.directory = tempfile.mkdtemp()
        module._process_deps(deps['dependencies'])
        shutil.rmtree((module.directory))
