"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""
import imp
import inspect
import logging
import os
import string
import shlex
import yaml

from cct.errors import CCTError
from cct.lib import file_utils
from cct.lib.git import clone_repo
from pkg_resources import resource_string, resource_filename

logger = logging.getLogger('cct')


class ChangeRunner(object):

    def __init__(self, change, modules_dir):
        self.change = change
        self.modules_dir = modules_dir
        self.modules = Modules(self.modules_dir)
        self.results = []

    def run(self):
        for module in self.change.modules:
            if module.name in self.modules.modules.keys():
                module.instance = self.modules.modules[module.name]
                runner = ModuleRunner(module)
            else:
                raise CCTError("no such module %s" % module.name)
            try:
                runner.run()
                logger.info("module %s successfully processed all steps" % module.name)
                self.results.append(module)
            except:
                logger.error("module %s failed processing steps" % module.name)
                self.results.append(module)
                raise

    def print_result_report(self):
        for module in self.results:
            print("Processed module: %s" % module.name)
            for operation in module.operations:
                print("  %-30s: %s" % (operation.command, operation.state))


class ModuleRunner(object):

    def __init__(self, module):
        self.module = module
        self.state = "Processing"

    def run(self):
        self.module.instance = self.module.instance(self.module.name)
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


class Change(object):

    def __init__(self, name, modules, description=None, environment=None):
        self.name = name
        self.description = description
        self.modules = modules
        self.environment = environment


class Module(object):

    def __init__(self, name):
        self.name = name
        self.environment = {}
        self.deps = []
        self.operations = []
        self.instance = None
        self.state = "NotRun"
        self.logger = logger

    def getenv(self, name, default=None):
        if os.environ.get(name):
            return os.environ.get(name)
        if name in self.environment:
            return self.environment[name]
        return default

    def _update_env(self, env):
        self.environment.update(env)

    def _process_module_config(self, config):
        self._process_artifacts(config['artifacts'])
        self.deps = config['dependencies']

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

    def _install(self, directory):
        url = None
        version = None
        for op in self.operations:
            if op.command == 'url':
                url = "".join(op.args)
            if op.command == 'version':
                version = "".join(op.args)
        if url:
            repo_dir = "%s/%s" % (directory, os.path.basename(url))
            clone_repo(url, repo_dir, version)
        try:
            with open(os.path.join(os.path.dirname(inspect.getabsfile(self.__class__)),
                      "module.yml")) as stream:
                self._process_module_config(yaml.load(stream))
        except:
            pass

    def _process_artifacts(self, artifacts):
        for artifact in artifacts:
            cct_resource = CctResource(artifact['name'],
                                       artifact['md5sum'])
            if 'handle' in artifact:
                self.artifacts[artifact['handle']] = cct_resource
            else:
                self.artifacts[artifact['name']] = cct_resource

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
    name = None
    md5sum = None

    def __init__(self, name, md5sum):
        self.name = name
        self.md5sum = md5sum


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


class Modules(object):
    modules = {}  # contains module name + its instance

    def __init__(self, modules_dir):
        # first we get builtin modules
        self.find_modules(os.path.join(os.path.dirname(__file__), 'modules'))
        # then fetched modules
        self.find_modules(modules_dir)

    def find_modules(self, directory):
        """
        Finds all modules in the subdirs of directory
        """
        if not os.path.exists(directory):
            return

        logger.debug("discovering modules in %s" % directory)

        def dirtest(x):
            if x.startswith('.') or x.startswith('tests'):
                logger.debug("find_modules: skipping {}".format(x))
                return False
            return True

        def fileaction(candidate):
            if candidate.endswith(".py") and os.path.isfile(candidate):
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
                    logger.info("found %s" % cls)
                    self.modules[module_name.split('.')[-1] + "." + cls.__name__] = cls

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
