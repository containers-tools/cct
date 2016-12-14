"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import logging
import shlex
import os

from cct.lib.git import clone_repo
from cct.module import Change, ChangeRunner, Module, Operation

logger = logging.getLogger('cct')


class ChangeProcessor(object):
    config = None

    def __init__(self, config, modules_dir):
        self.config = config
        self.modules_dir = modules_dir

    def process(self):
        logger.debug("processing change %s" % self.config)
        for change in self.config:
            self._process_change(change)

    def fetch_modules(self):
        for changes in self.config:
            for modules in changes['changes']:
                for name, ops in modules.items():
                    for op in ops:
                        if 'url' in op:
                            repo_dir = "%s/%s" % (self.modules_dir, os.path.basename(op['url']))
                            version = op['version'] if 'version' in op else None
                            clone_repo(op['url'], repo_dir, version)

    def _merge_environment(self, change_env, module_env):
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
            env_dict[variable] = env[variable]
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
                            environment = self._merge_environment(change.environment, self._create_env_dict(args))
                        else:
                            if args:
                                operation = Operation(name, shlex.split(str(args)))
                            else:
                                operation = Operation(name, None)
                            operations.append(operation)
                module = Module(module_name, operations, environment)
                changes.append(module)
        runner = ChangeRunner(change, self.modules_dir)
        try:
            runner.run()
        except:
            raise
        finally:
            runner.print_result_report()
