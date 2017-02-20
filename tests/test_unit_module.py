import cct.module
import os
import unittest
import shutil
import tempfile

from cct.errors import CCTError
from cct.module import Module
from cct.module import ModuleManager


class TestModules(unittest.TestCase):

    def test_find_modules(self):
        path = os.path.abspath(os.path.dirname(cct.module.__file__)) + "/modules"
        module_manager = ModuleManager(path)
        module_manager.discover_modules()

    def test_module_getenv_none(self):
        dummy = Module("dummy", "")
        self.assertIsNone(dummy.getenv("bar"))

    def test_module_getenv(self):
        dummy = Module("dummy", "")
        dummy.environment = {"foo": "foovalue"}
        self.assertEquals(dummy.getenv("foo"), "foovalue")

    def test_module_getenv_form_host(self):
        dummy = Module("dummy", "")
        os.environ['foo'] = "foovalue"
        self.assertEquals(dummy.getenv("foo"), "foovalue")

    def test_module_getenv_override(self):
        dummy = Module("dummy", "")
        dummy.environment = {"foohost": "barvalue"}
        os.environ['foohost'] = "foovalue"
        self.assertEquals(dummy.getenv("foohost"), "foovalue")

    def get_artifact(self, url, chksum):
        artifacts = {
            "artifacts": [
                {
                    "url": url,
                    "chksum": chksum,
                    "name": "cct",
                }
            ]
        }
        module = Module("foo", "/tmp")
        module._get_artifacts(artifacts['artifacts'], "/tmp")
        os.remove(module.cct_resource['cct'].path)

    def test_artifacts_fetching(self):
        url = "https://github.com/containers-tools/cct/archive/0.0.1.zip"
        chksum = "md5:d3c3fbf21935119d808bfe29fa33509c"
        self.get_artifact(url, chksum)

    def test_artifacts_fetching_wrong_url(self):
        url = "https://github.com/containers-tools/cct/archive/0.0.1.zip33"
        chksum = "md5:must_be_wrong_too"
        with self.assertRaises(CCTError):
            self.get_artifact(url, chksum)

    def test_artifacts_fetching_wrong_chksum(self):
        url = "https://github.com/containers-tools/cct/archive/0.0.1.zip"
        chksum = "md5:foo"
        with self.assertRaises(CCTError):
            self.get_artifact(url, chksum)

    def test_moudule_deps(self):
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
        mod_dir = tempfile.mkdtemp()
        module_manager = ModuleManager(mod_dir)
        module_manager.process_module_deps(deps['dependencies'])
        shutil.rmtree((mod_dir))
