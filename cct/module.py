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

class Change(object):
    name = None
    description = None
    environment = {}
    modules = {}


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
                self.module.instance = cls(self.module.name, self.module.operations)
         
    def run(self):
        if not self.module.instance:
            logger.debug("Runner has no module instace, creating one")
            self.setup()
            logger.debug("created %s" % self.module.instance)
        for operation in self.module.operations:
            #FIXME inject environment
            try:
                logger.debug("executing module %s operation %s with args %s" % (self.module.name, operation.command, operation.args))
                self.module.instance.run(operation)
            except:
                logger.error("module %s cannot execute %s with args %s" % (self.module.name, operation.command, operation.args))
                raise


class Module(object):
    name = None
    environment = {}
    operations = []
    instance = None

    def __init__(self, name, operations):
        self.name = name
        self.operations = operations

    def run(self):
        pass
                
class Operation(object):
    """
    Object representing single operation
    """
    command = None
    args = {}

    def __init__(self, command, args):
        self.command = command
        self.args = args


        
    
