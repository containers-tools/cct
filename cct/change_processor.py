"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""

import logging

logger = logging.getLogger('cct')
from cct.module import Operation, ModuleRunner, Module

class ChangeProcessor(object):
    config = None
    
    def __init__(self, config):
        self.config = config

    def process(self):
        logger.debug("processing change %s" % self.config)
        for change in self.config:
            self._process_change(change)

    def _process_change(self, change):
        logger.info("executing change %s" % change['name'])
        for modules in change['changes']:
            operations = []
            module = None
            for name, ops in modules.items():
                module = Module(name, operations)
                for op in ops:
                    for name, args in op.items():
                        operation = Operation(name, args)
                        operations.append(operation)
            runner = ModuleRunner(module)
            runner.run()

