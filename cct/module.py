"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""
import hashlib
import imp
import inspect
import glob
import logging
import multiprocessing
import os
import re
import shlex
import string
import subprocess
import traceback
import yaml

from cct import cfg
from cct.errors import CCTError
from cct.lib.git import clone_repo, get_tag_or_branch

try:
    import urllib.request as urlrequest
except ImportError:
    import urllib as urlrequest

logger = logging.getLogger('cct')


class ModuleManager(object):
    modules = {}
    artifacts_dir = ""

    def __init__(self, modules_dir, artifacts_dir):
        self.directory = modules_dir
        self.artifacts_dir = artifacts_dir
        self.version = None
        self.override = False

    def discover_modules(self, directory=None):
        directory = directory if directory is not None else self.directory
        module_dirs = []
        for root, _, files in os.walk(directory):
            if 'module.yaml' in files:
                module_dirs.append(root)

        for mod_dir in module_dirs:
            try:
                with open(os.path.join(mod_dir, "module.yaml")) as stream:
                    config = yaml.load(stream)
                    if 'dependencies' in config:
                        self.process_module_deps(config['dependencies'])
                    self.find_modules(mod_dir, config['language'])
            except Exception as ex:
                logger.error("Cannot setup module: %s" % ex, exc_info=True)
                raise ex

    def install_module(self, url, version, override=False):
        if override and not version:
            raise CCTError('Cannot override vesrion without specifying it!')
        self.version = version
        self.override = override
        repo_dir = "%s/%s" % (self.directory, os.path.basename(url))
        if repo_dir.endswith('git'):
            repo_dir = repo_dir[:-4]
        clone_repo(url, repo_dir, self.version, self.override)
        self.discover_modules(repo_dir)

    def process_module_deps(self, deps):
        for dep in deps:
            logger.debug("Fetching module from %s" % dep['url'])
            self.install_module(dep['url'], str(dep['version']) if 'version' in dep else None,
                                self.override)

    def find_modules(self, directory, language):
        """
        Finds all modules in the subdirs of directory
        """
        if not os.path.exists(directory):
            return {}

        logger.debug("Discovering modules in %s" % directory)
        if 'bash' in language:
            pattern = os.path.join(os.path.abspath(directory), '*.sh')
            for candidate in glob.glob(pattern):
                self.check_module_sh(candidate)
        elif 'script' in language:
            for candidate in filter(lambda f: os.path.isdir(os.path.join(directory, f)), os.listdir(directory)):
                if candidate != '.git':
                    self.check_module_script(os.path.join(directory, candidate))
        else:
            pattern = os.path.join(os.path.abspath(directory), '*.py')
            for candidate in glob.glob(pattern):
                self.check_module_py(candidate)

    def check_module_py(self, candidate):
        module_name = "cct.module." + os.path.dirname(candidate).split('/')[-1]
        logger.debug("importing module %s to %s" % (os.path.abspath(candidate), module_name))
        module = imp.load_source(module_name, os.path.abspath(candidate))
        # Get all classes from our module
        for name, clazz in inspect.getmembers(module, inspect.isclass):
            # Check that class is from our namespace
            if module_name == clazz.__module__:
                # Instantiate class
                self.check_module_version(name)
                cls = getattr(module, name)
                if issubclass(cls, Module):
                    name = module_name.split('.')[-1] + "." + cls.__name__
                    self.modules[name] = cls(name, os.path.dirname(candidate), self.artifacts_dir)
                    self.modules[name].version = self.version
                    self.modules[name].override = self.override

    def check_module_sh(self, candidate):
        module_name = "cct.module." + os.path.dirname(candidate).split('/')[-1]
        logger.debug("Importing module %s to %s" % (os.path.abspath(candidate), module_name))
        name = module_name.split('.')[-1] + "." + os.path.basename(candidate)[:-3]
        if self.check_module_version(name):
            return
        self.modules[name] = ShellModule(name, os.path.dirname(candidate), self.artifacts_dir, candidate)
        self.modules[name].version = self.version
        self.modules[name].override = self.override

    def check_module_script(self, candidate):
        name = "%s.%s" % (os.path.dirname(candidate).split('/')[-1], candidate.split('/')[-1])
        logger.debug("Importing script from %s to %s" % (os.path.abspath(candidate), name))
        self.modules[name] = ScriptModule(name, os.path.dirname(candidate), self.artifacts_dir)
        self.modules[name].version = self.version
        self.modules[name].override = self.override

    def check_module_version(self, name):
        # if we override version we dont care about overwriting modules
        if self.override:
            return False
        # if the module doesnt exists just create it
        if name not in self.modules:
            return False
        # if module was froced we will not override it
        if self.modules[name].override:
            return True
        # check if the version are not conflicting
        # FIXME - tag in branch vs branch is considered incompatible
        if self.modules[name].version != self.version:
            msg = "Conflicting module '%s' version found, installed version '%s', required version '%s'" % (name, self.modules[name].version, self.version)
            logger.error(msg)
            raise Exception(msg)
        return True

    def list(self):
        print("available cct modules:")
        for name, module in self.modules.iteritems():
            mod_dir = os.path.basename(inspect.getabsfile(module.__class__))
            if isinstance(module, ShellModule):
                mod_dir = os.path.dirname(module.script)
            elif isinstance(module, ScriptModule):
                mod_dir = module.directory
            version = get_tag_or_branch(mod_dir)[:-1]
            print("  %s:%s" % (name, version))

    def list_module_oper(self, name):
        module = None
        if name not in self.modules:
            print("Module %s cannot be found!" % name)
            exit(1)
        else:
            module = self.modules[name]
        print("Module %s contains commands: " % name)

        if getattr(module, "setup").__doc__:
            print("  setup: %s " % getattr(module, "setup").__doc__)

        for method in dir(module):
            if callable(getattr(module, method)):
                if method[0] in string.ascii_lowercase and method not in ['setup', 'teardown']:
                    print("  %s: %s" % (method, getattr(module, method).__doc__))

        if getattr(module, "teardown").__doc__:
            print("  teardown: %s " % getattr(module, "teardown").__doc__)


class Process(multiprocessing.Process):
    def __init__(self, *args, **kwargs):
        multiprocessing.Process.__init__(self, *args, **kwargs)
        self._pconn, self._cconn = multiprocessing.Pipe()
        self._exception = None

    def run(self):
        try:
            multiprocessing.Process.run(self)
            self._cconn.send(None)
        except Exception as e:
            tb = traceback.format_exc()
            self._cconn.send((e, tb))
            # raise e  # You can still rise this exception if you need to

    @property
    def exception(self):
        if self._pconn.poll():
            self._exception = self._pconn.recv()
        return self._exception


class ModuleRunner(object):
    def __init__(self, module):
        self.module = module
        self.state = "Processing"

    def run(self):
        self.module.instance.setup()
        for operation in self.module.operations:
            if operation.command in ['setup', 'teardown']:
                continue
            if operation.command == 'user':
                logger.info("setting uid to %s" % operation.args[0])
                self.module.uid = operation.args[0]
                continue
            self.module.instance._process_environment(operation)
            try:
                logger.debug("executing module %s operation %s with args %s" % (self.module.name, operation.command, operation.args))
                proc = Process(target=self.module.instance._run, args=(operation, self.module.uid))
                proc.start()
                proc.join()
                if proc.exception:
                    err, tb = proc.exception
                    raise Exception(err)
                self.state = "Passed"
            except Exception as e:
                self.state = "Error"
                logger.error("module %s cannot execute %s with args %s" % (self.module.name, operation.command, operation.args))
                raise e
        self.module.instance.teardown()
        self.state = "Passed"


class Module(object):
    artifacts = {}
    modules_dirs = {}

    def __init__(self, name, directory, artifacts_dir, version=None):
        self.name = name
        self.environment = {}
        self.deps = []
        self.operations = []
        self.instance = None
        self.state = "NotRun"
        self.logger = logger
        self.version = version
        self.override = False
        self.uid = os.getuid()
        if not directory:
            return
        self.modules_dirs[os.path.splitext(name)[0]] = directory
        with open(os.path.join(directory, "module.yaml")) as stream:
            config = yaml.load(stream)
            if 'artifacts' in config:
                self._get_artifacts(config['artifacts'], artifacts_dir)

    def getenv(self, name, default=None):
        if os.environ.get(name):
            return os.environ.get(name)
        if name in self.environment:
            return self.environment[name]
        return default

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
                    logger.debug("Using host variable %s" % token)
                    token = os.environ[var_name]
                elif self.environment.get(var_name):
                    logger.debug("Using yaml file variable %s" % token)
                    token = self.environment[var_name]
            result += token + " "
        return result

    def _get_artifacts(self, artifacts, destination):
        for artifact in artifacts:
            if cfg.dogen:
                if artifact not in cfg.artifacts:
                    cfg.artifacts.append(artifact)
            else:
                cct_artifact = CctArtifact(**artifact)
                cct_artifact.fetch(destination)
                self.artifacts[cct_artifact.name] = cct_artifact

    def setup(self):
        pass

    def teardown(self):
        pass

    def _process_environment(self, operation):
        if '$' in operation.command:
            operation.command = self._replace_variables(operation.command)
        for i in range(len(operation.args)):
            if '$' in operation.args[i]:
                operation.args[i] = self._replace_variables(operation.args[i])

    def _run(self, operation, uid):
        try:
            os.setuid(int(uid))
            logger.debug("invoking command %s as uid: %s", operation.command, uid)
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
            logger.error("%s operation failed with: %s", operation.command, e, exc_info=True)
            operation.state = "Error"
            self.state = "Error"
            raise e


class CctArtifact(object):
    """
    Object representing artifact file for changes
    name - name of the file
    md5 - hash of artifact
    sha256 - hash of artifact
    sha1 - has of artifact
    """
    def __init__(self, name, md5=None, sha1=None, sha256=None, artifact="", hint=""):
        self.name = name
        self.sums = {'sha1': sha1,
                     'sha256': sha256,
                     'md5': md5}
        self.artifact = self.replace_variables(artifact) if '$' in artifact else artifact
        self.filename = os.path.basename(artifact)
        self.path = None
        self.hint = hint

    def fetch(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

        self.path = os.path.join(directory, self.filename)

        url = self.artifact
        if self.check_sum():
            logger.info("Using cached artifact for %s" % self.filename)
            return

        logger.info("Fetching %s from  %s." % (self.filename, url))

        try:
            if os.path.basename(url) == url:
                raise CCTError("Artifact is referenced by filename - can't download it.")
            urlrequest.urlretrieve(url, self.path)
        except Exception as ex:
            if self.hint:
                raise CCTError('artifact: "%s" was not found. %s' % (self.path, self.hint))
            else:
                raise CCTError("cannot download artifact from url %s, error: %s" % (url, ex))

        if not self.check_sum():
            if self.hint:
                raise CCTError('hash is not correct for artifact: "%s". %s' % (self.path, self.hint))
            else:
                raise CCTError("artifact from %s doesn't match required chksum" % url)

    def check_sum(self):
        if not os.path.exists(self.path):
            return False
        for alg, sum in self.sums.items():
            hash = getattr(hashlib, alg)()
            with open(self.path, "rb") as f:
                for block in iter(lambda: f.read(65536), b""):
                    hash.update(block)
            if sum is not None and sum != hash.hexdigest():
                return False
        return True

    def replace_variables(self, string):
        var_regex = re.compile('\$\{.*\}')
        variable = var_regex.search(string).group(0)[2:-1]
        if os.environ.get(variable):
            logger.debug("Using host variable %s" % variable)
            string = var_regex.sub(os.environ[variable], string)
        return string


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


class ScriptModule(Module):

    def __init__(self, name, directory, artifacts_dir):
        Module.__init__(self, name, directory, artifacts_dir)
        self.directory = directory
        pattern = os.path.join(directory, name.split('.')[1], '*')
        self.names = {}
        for script in filter(lambda f: os.path.isfile(f), glob.glob(pattern)):
            self.names[os.path.basename(script).replace('-', '_').replace('.', '_')] = script

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            if name in self.names:
                self._run_script(self.names[name], *args)
            else:
                raise AttributeError("No such method %s" % name)
        return wrapper

    def _run_script(self, script, *args):
        cmd = 'bash -x %s %s' % (script, " ".join(args))
        try:
            env = dict(os.environ)
            mod_dir = os.path.dirname(os.path.dirname(script))
            env['CCT_MODULE_PATH'] = mod_dir
            logger.info('Created CCT_MODULE_PATH environment variable for module %s' % mod_dir)

            for name, mod_dir in self.modules_dirs.items():
                var_name = 'CCT_MODULE_PATH_%s' % name.upper().replace('-', '_')
                env[var_name] = mod_dir
                logger.info('Created %s environment variable for module %s.' % (var_name, mod_dir))

            for name, artifact in self.artifacts.items():
                var_name = 'CCT_ARTIFACT_PATH_' + name.upper().replace('-', '_')
                logger.info('Created %s environment variable pointing to %s.' % (var_name, artifact.path))
                env[var_name] = artifact.path
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env, shell=True)
            self.logger.debug("Step ended with output: %s" % out)
        except subprocess.CalledProcessError as e:
            raise CCTError(e.output)


class ShellModule(Module):
    modules_dirs = {}

    def __init__(self, name, directory, artifacts_dir, path):
        Module.__init__(self, name, directory, artifacts_dir)
        self.script = path
        self.modules_dirs[os.path.splitext(name)[0]] = os.path.dirname(path)
        self._discover()

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            if name in self.names:
                self._run_function(name, *args)
            else:
                raise Exception("no such method")
        return wrapper

    def _discover(self):
        self.names = {}
        comment = ""
        param = re.compile("\$\d+")
        with open(self.script, "r") as f:
            name = ""
            for line in f:
                if line.startswith('#'):
                    comment += line[1:]
                elif 'function' in line:
                    name = line.split()[1][:-2]
                    function = {"name": name,
                                "comment": comment,
                                "params": {}}
                    self.names[name] = function
                elif param.search(line):
                    param_name = line.split('=')[0].split()[-1]
                    self.logger.debug("function: %s, param_id: %s, param_name: %s"
                                      % (name, param_name, param.search(line).group(0)))
                    self.names[name]["params"][param_name] = param.search(line).group(0)
                else:
                    comment = ""

    def _run_function(self, name, *args):
        cmd = '/bin/bash -c " source %s ; %s %s"' % (self.script, name, " ".join(args))
        try:
            env = dict(os.environ)
            mod_dir = os.path.dirname(self.script)
            env['CCT_MODULE_PATH'] = mod_dir
            logger.info('Created CCT_MODULE_PATH environment variable for module %s' % mod_dir)

            for name, mod_dir in self.modules_dirs.items():
                var_name = 'CCT_MODULE_PATH_%s' % name.upper().replace('-', '_')
                env[var_name] = mod_dir
                logger.info('Created %s environment variable for module %s.' % (var_name, mod_dir))

            for name, artifact in self.artifacts.items():
                var_name = 'CCT_ARTIFACT_PATH_' + name.upper().replace('-', '_')
                logger.info('Created %s environment variable pointing to %s.' % (var_name, artifact.path))
                env[var_name] = artifact.path
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env, shell=True)
            self.logger.debug("Step ended with output: %s" % out)
        except subprocess.CalledProcessError as e:
            raise CCTError(e.output)
