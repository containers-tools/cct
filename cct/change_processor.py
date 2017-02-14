"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import logging

from cct.module import ModuleManager, ModuleRunner
from cct.errors import CCTError

logger = logging.getLogger('cct')


class ChangeProcessor(object):
    config = None

    def __init__(self, config, modules_dir):
        self.config = config
        self.modules_dir = modules_dir

    def process(self, fetch_only=False):
        logger.debug("processing change %s" % self.config)
        for change in self.config:
            self._process_change(change, fetch_only)

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

    def _process_change(self, change_cfg, fetch_only):
        logger.info("processing change %s" % change_cfg['name'])
        change_env = self._create_env_dict(change_cfg.get('environment'))
        if 'description' not in change_cfg:
            change_cfg['description'] = None
        mr = ModuleManager(self.modules_dir)
        mr.discover_modules()
        for modules in change_cfg['changes']:
            for module_name, operations in modules.items():
                url = None
                ver = None
                for op in operations:
                    if 'url' in op:
                        url = op['url']
                    elif 'version' in op:
                        ver = op['version']
                if url:
                    mr.install_module(url, ver)
                else:
                    if module_name not in mr.modules:
                        raise Exception("Module %s cannot be found" % module_name)
                module = mr.modules[module_name]
                module._update_env(change_env)
                module._process_operations(operations)

        change = Change(change_cfg['name'], modules, change_cfg['description'],
                        change_env)
        if not fetch_only:
            runner = ChangeRunner(change, self.modules_dir)
            try:
                runner.run()
            except:
                raise
            finally:
                runner.print_result_report()


class Change(object):
    def __init__(self, name, modules, description=None, environment=None):
        self.name = name
        self.modules = modules
        self.description = description
        self.environment = environment


class ChangeRunner(object):

    def __init__(self, change, modules_dir):
        self.change = change
        self.modules_dir = modules_dir
        self.modules = ModuleManager(self.modules_dir)
        self.results = []
        self.cct_resource = {}

    def run(self):
        for name in self.change.modules:
            if name in self.modules.modules:
                module = self.modules.modules[name]
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
