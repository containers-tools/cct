"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import logging

from cct.module import ModuleManager, ModuleRunner, Module

logger = logging.getLogger('cct')


class ChangeProcessor(object):
    config = None

    def __init__(self, config, modules_dir, artifacts_dir):
        self.config = config
        self.modules_dir = modules_dir
        self.artifacts_dir = artifacts_dir

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
        mr = ModuleManager(self.modules_dir, self.artifacts_dir)

        if 'modules' in change_cfg:
            for module in change_cfg['modules']:
                url = module['url']
                ver = module['version'] if 'version' in module else None
                override = module['override'] if 'override' in module else False
                mr.install_module(url, ver, override)

        steps = []
        for modules in change_cfg['changes']:
            for module_name, operations in modules.items():
                if module_name not in mr.modules:
                        raise Exception("Module %s cannot be found" % module_name)
                module = Module(module_name, None, None)
                module.instance = mr.modules[module_name]
                module._update_env(change_env)
                module._process_operations(operations)
                steps.append(module)
        change = Change(change_cfg['name'], steps, change_cfg['description'],
                        change_env)
        if not fetch_only:
            runner = ChangeRunner(change, self.modules_dir, self.artifacts_dir)
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

    def __init__(self, change, modules_dir, artifacts_dir):
        self.change = change
        self.modules = ModuleManager(modules_dir, artifacts_dir)
        self.results = []
        self.cct_resource = {}

    def run(self):
        for module in self.change.modules:
            try:
                runner = ModuleRunner(module)
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
