"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""
import imp
import inspect
import logging
import os

logger = logging.getLogger('cct')


class ChangeRunner(object):
    change = None

    def __init__(self, change):
        self.change = change

    def run(self):
        for module in self.change.changes:
            runner = ModuleRunner(module)
            runner.run()

class ModuleRunner(object):
    module = None

    def __init__(self, module):
        self.module = module

    def setup(self):
        #FIXME look through all .py files in that dir and take one which inherits correct interface
        directory = os.path.join(os.path.dirname(__file__), 'modules')
        filename = directory + "/" + self.module.name + "/cct_module.py"
        module_name = "cct.module." + self.module.name
        logger.debug("importing module %s to %s" % (filename, module_name ))
        module = imp.load_source(module_name, filename)
        # Get all classes from our modul
        for name, clazz in inspect.getmembers(module, inspect.isclass):
            # Check that class is from our namespace
            if module_name == clazz.__module__:
                # Instantiate class
                cls = getattr(module, name)
                self.module.instance = cls(self.module.name, self.module.operations, self.module.environment)
         
    def run(self):
        if not self.module.instance:
            logger.debug("Runner has no module instace, creating one")
            self.setup()
            logger.debug("created %s" % self.module.instance)
        for operation in self.module.operations:
            self.module.process_environment(operation)
            #FIXME inject environment
            try:
                logger.debug("executing module %s operation %s with args %s" % (self.module.name, operation.command, operation.args))
                self.module.instance.run(operation)
            except Exception, e:
                logger.error("module %s cannot execute %s with args %s" % (self.module.name, operation.command, operation.args))
                logger.debug(e, exc_info=True)

class Change(object):
    name = None
    description = None
    environment = {}
    modules = {}

    def __init__(self, name, changes, description=None, environment=None):
        self.name = name
        self.description = description
        self.changes = changes
        self.environment = environment

class Module(object):
    name = None
    environment = {}
    operations = []
    instance = None

    def __init__(self, name, operations, environment={}):
        self.name = name
        self.operations = operations
        self.environment = environment

    def _replace_variables(self, string):
        result = ""
        for token in string.split(" "):
            logger.debug("processing token %s", token)
            if token.startswith("$"):
                var_name = token[1:]
                # set value from environment
                if os.environ.get(var_name):
                    logger.info("Using host variable %s" %token)
                    token = os.environ[var_name]
                elif self.environment.get(var_name):
                    logger.info("Using yaml file variable %s" %token)
                    token = self.environment[var_name]
            result += token + " "
        return result

    def process_environment(self, operation):
        if '$' in operation.command:
            operation.command = self._replace_variables(operation.command)
        for i in xrange(len(operation.args)):
            if '$' in operation.args[i]:
                operation.args[i] = self._replace_variables(operation.args[i])

    def run(self, operation):
        try:
            logger.debug("invoking command %s", operation.command)
            method = getattr(self, operation.command)
            method(*operation.args)
        except:
            logger.error("%s is not supported by module", operation.command)
            raise

class Operation(object):
    """
    Object representing single operation
    """
    command = None
    args = []

    def __init__(self, command, args):
        self.command = command
        self.args=[]
        for arg in args:
            self.args.append(arg.rstrip())


        
    
