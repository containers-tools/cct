"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""

import logging
import subprocess

from cct.module import Module
logger = logging.getLogger('cct')

class Shell(Module):
    def run(self, operation):
        if operation.command == "shell":
            self._execute_shell(operation.args)
        else:
            logger.info("unsuported operation %s with args %s" % (operation.command, operation.args ))

    def _execute_shell(self, command):
        logger.debug("executing shell command: %s" % command)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        
        if stdout:
            logger.debug("command stdout: %s", stdout)
        if stderr:
            logger.error("command stderr: %s", stderr)
        
        
