"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""

import logging
import shlex

logger = logging.getLogger('cct')
from cct.module import Operation, ChangeRunner, Module, Change

class ChangeProcessor(object):
    config = None

    def __init__(self, config):
        self.config = config

    def process(self):
        logger.debug("processing change %s" % self.config)
        for change in self.config:
            self._process_change(change)

    def _merge_environemnt(self, change_env, module_env):
        if change_env is None:
            return module_env
        if module_env is None:
            return change_env
        combined = {}
        combined.update(change_env)
        combined.update(module_env)
        return combined

    def _create_env_dict(self, env):
        env_dict = {}
        if env is None:
            return env_dict
        for variable in env:
            for key, value in variable.items():
                env_dict[key]=value
        return env_dict

    def _process_change(self, change_cfg):
        logger.info("executing change %s" % change_cfg['name'])
        changes = []
        if 'environment' not in change_cfg:
            change_cfg['environment'] = None
        if 'description' not in change_cfg:
            change_cfg['description'] = None
        change = Change(change_cfg['name'], changes, change_cfg['description'],
                        self._create_env_dict(change_cfg['environment']))
        for modules in change_cfg['changes']:
            environment = change.environment
            operations = []
            module = None
            for module_name, ops in modules.items():
                for op in ops:
                    for name, args in op.items():
                        logger.debug(name)
                        if name == "environment":
                            environment = self._merge_environemnt(change.environment, self._create_env_dict(args))
                        else:
                            if args:
                                operation = Operation(name, shlex.split(args))
                            else:
                                operation = Operation(name, None)
                            operations.append(operation)
                module = Module(module_name, operations, environment)
                changes.append(module)
        runner = ChangeRunner(change)
        try:
            runner.run()
        except:
            raise
        finally:
            runner.print_result_report()
