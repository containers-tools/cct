import cct.module
import logging
import os
import unittest
import shutil
import tempfile
import yaml

from cct.errors import CCTError
from cct.module import Module
from cct.module import ModuleManager

logging.basicConfig(level=logging.DEBUG)


class TestModules(unittest.TestCase):

    def test_find_modules(self):
        path = os.path.abspath(os.path.dirname(cct.module.__file__)) + "/modules"
        module_manager = ModuleManager(path, '/tmp')
        module_manager.discover_modules()

    def test_module_getenv_none(self):
        dummy = Module("dummy", "", "/tmp")
        self.assertIsNone(dummy.getenv("bar"))

    def test_module_getenv(self):
        dummy = Module("dummy", "", "/tmp")
        dummy.environment = {"foo": "foovalue"}
        self.assertEquals(dummy.getenv("foo"), "foovalue")

    def test_module_getenv_form_host(self):
        dummy = Module("dummy", "", "/tmp")
        os.environ['foo'] = "foovalue"
        self.assertEquals(dummy.getenv("foo"), "foovalue")

    def test_module_getenv_override(self):
        dummy = Module("dummy", "", "/tmp")
        dummy.environment = {"foohost": "barvalue"}
        os.environ['foohost'] = "foovalue"
        self.assertEquals(dummy.getenv("foohost"), "foovalue")

    def get_artifact(self, url, chksum):
        artifacts = {
            "artifacts": [
                {
                    "artifact": url,
                    "md5": chksum,
                    "name": "cct",
                }
            ]
        }
        module = Module("foo", None, "/tmp")
        module._get_artifacts(artifacts['artifacts'], "/tmp")
        os.remove(module.artifacts['cct'].path)

    def test_artifacts_fetching(self):
        url = "https://github.com/containers-tools/cct/archive/0.2.0.zip"
        chksum = "607468ba87490a2b8daa4b6a73168620"
        self.get_artifact(url, chksum)

    def test_artifacts_fetching_wrong_url(self):
        url = "https://github.com/containers-tools/cct/archive/0.0.1.zip33"
        chksum = "must_be_wrong_too"
        with self.assertRaises(CCTError):
            self.get_artifact(url, chksum)

    def test_artifacts_fetching_wrong_chksum(self):
        url = "https://github.com/containers-tools/cct/archive/0.2.0.zip"
        chksum = "foo"
        with self.assertRaises(CCTError):
            self.get_artifact(url, chksum)

    def test_moudule_deps(self):
        url = "https://github.com/containers-tools/test-module-dep"
        version = "master"
        deps = {
            "dependencies": [
                {
                    "url": url,
                    "version": version
                }
            ]
        }
        mod_dir = tempfile.mkdtemp()
        module_manager = ModuleManager(mod_dir, '/tmp')
        module_manager.process_module_deps(deps['dependencies'])
        shutil.rmtree(mod_dir)

    def test_module_version_override(self):
        url = "https://github.com/containers-tools/test-module-dep"
        mod_dir = tempfile.mkdtemp()
        mm = ModuleManager(mod_dir, '/tmp')
        mm.install_module(url, '1.0', override=True)
        mm.install_module(url, 'master')
        self.assertEquals(mm.modules['test-module-dep.dummy'].version, '1.0')
        self.assertTrue(mm.modules['test-module-dep.dummy'].override)
        shutil.rmtree(mod_dir)

    def test_module_version_conflict(self):
        url = "https://github.com/containers-tools/test-module-dep"
        mod_dir = tempfile.mkdtemp()
        mm = ModuleManager(mod_dir, '/tmp')
        mm.install_module(url, 'master')
        with self.assertRaisesRegexp(Exception, 'Conflicting module.*'):
            mm.install_module(url, '1.0')
        shutil.rmtree(mod_dir)

    def test_module_script(self):
        mod_dir = os.path.join(tempfile.mkdtemp(), 'scripts')
        mm = ModuleManager(mod_dir, '/tmp')
        script = os.path.join(mod_dir, 'test', 'script')
        module = os.path.join(mod_dir, 'module.yaml')
        modconfig =  { 'language' : [ 'script']}
        os.makedirs(os.path.dirname(script))
        with open(module, 'w') as modfile:
            yaml.dump(modconfig, modfile, default_flow_style=False)
        shutil.copy(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'script'), script)
        mm.discover_modules(mod_dir)
        mod =  mm.modules['scripts.test']
        mod.script()
