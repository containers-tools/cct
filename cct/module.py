"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""
import hashlib
import imp
import inspect
import logging
import os
import shlex
import string
import yaml

from pkg_resources import resource_string, resource_filename

from cct.errors import CCTError
from cct.lib import file_utils
from cct.lib.git import clone_repo

try:
    import urllib.request as urlrequest
except ImportError:
    import urllib as urlrequest

logger = logging.getLogger('cct')


class ModuleManager(object):
    modules = {}

    def __init__(self, directory):
        self.directory = directory

    def discover_modules(self, directory=None):
        directory = directory if directory is not None else self.directory
        module_dirs = []
        for root, _, files in os.walk(self.directory):
            if 'module.yaml' in files:
                module_dirs.append(root)

        for mod_dir in module_dirs:
            try:
                with open(os.path.join(mod_dir, "module.yaml")) as stream:
                    config = yaml.load(stream)
                    if 'deps' in config:
                        self.process_module_deps(config)
                    self.find_modules(mod_dir, config['language'])
            except Exception as ex:
                logger.debug("Cannot process module.yaml %s" % ex, exc_info=True)

    def install_module(self, url, version):
        repo_dir = "%s/%s" % (self.directory, os.path.basename(url))
        logger.debug("Fetching into %s" % repo_dir)
        clone_repo(url, repo_dir, version)
        self.discover_modules(repo_dir)

    def process_module_deps(self, deps):
        for dep in deps:
            print dep
            logger.debug("Fetching module from %s" % dep['url'])
            self.install_module(dep['url'], dep['version'] if 'version' in deps else None)

    def find_modules(self, directory, language):
        """
        Finds all modules in the subdirs of directory
        """
        if not os.path.exists(directory):
            return {}

        if language is 'python':
            extension = 'py'
        elif language is 'bash':
            extension = 'sh'
        else:
            extension = 'py'

        logger.debug("discovering modules in %s" % directory)

        def dirtest(x):
            if x.startswith('.') or x.startswith('tests'):
                logger.debug("find_modules: skipping {}".format(x))
                return False
            return True

        def fileaction(candidate):
            if candidate.endswith(extension) and os.path.isfile(candidate):
                logger.debug("inspecting %s" % candidate)
                try:
                    self.check_module(candidate)
                except Exception as e:
                    logging.error("Cannot import module %s" % e, exc_info=True)

        file_utils.find(directory, dirtest, fileaction)

    def check_module(self, candidate):
        module_name = "cct.module." + os.path.dirname(candidate).split('/')[-1]
        logger.debug("importing module %s to %s" % (os.path.abspath(candidate), module_name))
        module = imp.load_source(module_name, os.path.abspath(candidate))
        # Get all classes from our module
        for name, clazz in inspect.getmembers(module, inspect.isclass):
            # Check that class is from our namespace
            if module_name == clazz.__module__:
                # Instantiate class
                cls = getattr(module, name)
                if issubclass(cls, Module):
                    print(module_name)
                    print(cls)
                    self.modules[module_name.split('.')[-1] + "." + cls.__name__] = cls(module_name.split('.')[-1] + "." + cls.__name__)

    def list(self):
        print("available cct modules:")
        for module, _ in self.modules.iteritems():
            print("  %s" % module)

    def list_module_oper(self, name):
        module = Module(name, None)
        if module.name in self.modules.keys():
            module.instance = self.modules[module.name]
        else:
            print("Module %s cannot be found!" % name)
            return
        print("Module %s contains commands: " % name)
        module.instance = module.instance(name, None)

        if getattr(module.instance, "setup").__doc__:
            print("  setup: %s " % getattr(module.instance, "setup").__doc__)

        for method in dir(module.instance):
            if callable(getattr(module.instance, method)):
                if method[0] in string.ascii_lowercase and method not in ['run', 'setup', 'url', 'version', 'teardown']:
                    print("  %s: %s" % (method, getattr(module.instance, method).__doc__))

        if getattr(module.instance, "teardown").__doc__:
            print("  teardown: %s " % getattr(module.instance, "teardown").__doc__)


class ModuleRunner(object):
    def __init__(self, module):
        self.module = module
        self.state = "Processing"

    def run(self):
        self.module.instance.setup()
        for operation in self.module.operations:
            if operation.command in ['setup', 'run', 'url', 'version', 'teardown']:
                continue
            self.module._process_environment(operation)
            try:
                logger.debug("executing module %s operation %s with args %s" % (self.module.name, operation.command, operation.args))
                self.module.instance.run(operation)
                self.state = "Passed"
            except Exception as e:
                self.state = "Error"
                logger.error("module %s cannot execute %s with args %s" % (self.module.name, operation.command, operation.args))
                logger.debug(e, exc_info=True)
                raise e
        self.module.instance.teardown()
        self.state = "Passed"


class Module(object):

    def __init__(self, name):
        self.name = name
        self.environment = {}
        self.deps = []
        self.operations = []
        self.instance = None
        self.state = "NotRun"
        self.logger = logger
        self.cct_resource = {}

    def getenv(self, name, default=None):
        if os.environ.get(name):
            return os.environ.get(name)
        if name in self.environment:
            return self.environment[name]
        return default

    def _get_artifacts(self, artifacts, path):
        for artifact in artifacts:
            cct_resource = CctResource(**artifact)
            cct_resource.fetch(path)
            self.cct_resource[cct_resource.name] = cct_resource

    def _update_env(self, env):
        self.environment.update(env)

    def _process_operations(self, ops):
        for op in ops:
            for name, args in op.items():
                logger.debug("processing operation %s with args '%s'" % (name, args))
                if name == "environment":
                    self._update_env(self._create_env_dict(args))
                else:
                    self._add_operation(name, args)

    def _add_operation(self, name, args):
        operation = Operation(name, shlex.split(str(args)) if args else None)
        self.operations.append(operation)

    def _replace_variables(self, string):
        result = ""
        for token in string.split(" "):
            logger.debug("processing token %s", token)
            if token.startswith("$"):
                var_name = token[1:]
                # set value from environment
                if os.environ.get(var_name):
                    logger.info("Using host variable %s" % token)
                    token = os.environ[var_name]
                elif self.environment.get(var_name):
                    logger.info("Using yaml file variable %s" % token)
                    token = self.environment[var_name]
            result += token + " "
        return result

    def setup(self):
        pass

    def teardown(self):
        pass

    def _get_resource(self, resource):
        return resource_string(inspect.getmodule(self.__class__).__name__, resource)

    def _get_resource_path(self, resource):
        return resource_filename(inspect.getmodule(self.__class__).__name__, resource)

    def _process_environment(self, operation):
        if '$' in operation.command:
            operation.command = self._replace_variables(operation.command)
        for i in range(len(operation.args)):
            if '$' in operation.args[i]:
                operation.args[i] = self._replace_variables(operation.args[i])

    def run(self, operation):
        try:
            logger.debug("invoking command %s", operation.command)
            method = getattr(self, operation.command)
            method_params = inspect.getargspec(method)
            args = []
            kwargs = {}
            for arg in operation.args:
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    if key in method_params.args:
                        kwargs[key] = value
                    else:
                        args.append(arg.strip())
                else:
                    args.append(arg.strip())
            method(*args, **kwargs)
            logger.debug("operation '%s' Passed" % operation.command)
            operation.state = "Passed"
        except Exception as e:
            logger.error("%s is not supported by module %s", operation.command, e, exc_info=True)
            operation.state = "Error"
            self.state = "Error"
            raise e


class CctResource(object):
    """
    Object representing resource file for changes
    name - name of the file
    md5sum - md5sum
    """
    def __init__(self, name, chksum, url):
        self.name = name
        self.chksum = chksum
        self.url = url
        self.filename = os.path.basename(url)
        self.path = None

    def fetch(self, directory):
        logger.debug("fetch to dir %s" % inspect.getmodule(self.__class__).__name__)
        logger.debug("Fetching %s as a resource for module %s" % (self.url, self.name))
        self.path = os.path.join(directory, self.filename)
        try:
            urlrequest.urlretrieve(self.url, self.path)
        except Exception as ex:
            raise CCTError("Cannot download artifact from url %s, error: %s" % (self.url, ex))
        self.check_sum()

    def check_sum(self):
        logger.error(self.chksum[:self.chksum.index(':')])
        hash = getattr(hashlib, self.chksum[:self.chksum.index(':')])()
        with open(self.path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                hash.update(block)
        if self.chksum[self.chksum.index(':') + 1:] == hash.hexdigest():
            return True
        raise CCTError("Resource from %s doenst match required chksum %s" % (self.url, self.chksum))


class Operation(object):
    """
    Object representing single operation
    """
    command = None
    args = []
    state = "NotRun"

    def __init__(self, command, args):
        self.command = command
        self.args = []
        if args:
            for arg in args:
                self.args.append(arg.rstrip())
