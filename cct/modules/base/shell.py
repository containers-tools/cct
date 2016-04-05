"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import os
import pwd
import subprocess

from cct.errors import CCTError
from cct.module import Module


class Shell(Module):
    env = {}

    def set_env(self, *environ):
        """
        Sets envrionment variables for shell commands in a form of ENV=value
        """
        for env in environ:
            self.logger.debug("processing variable %s" %env)
            key,value = env.split('=',1)
            self.env[key] = value
        self.logger.debug("set environ %s" %self.env)

    def shell(self, *command):
        """
        Runs given comman in a shell
        """
        self.shell_as_user( None, *command)

    def shell_as_user(self, user=None, *command):
        user_uid = os.getuid()
        if user:
            user_uid = pwd.getpwnam(user).pw_uid

        self.logger.debug("Executing shell command: '%s'" % " ".join(command))
        process = subprocess.Popen(
            " ".join(command), preexec_fn=self._demote(user_uid), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=self.env, shell=True)
        stdout, stderr = process.communicate()
        retcode = process.wait()

        if stdout:
            self.logger.debug("Captured stdout: %s" % stdout)
        if stderr:
            self.logger.error("Captured stderr: %s" % stderr)

        if retcode == 0:
            self.logger.debug(
                "Command '%s' executed successfully" % " ".join(command))
        else:
            raise CCTError("Command '%s' failed" % " ".join(command))


    def _demote(self, user_uid):
        def set_ids():
            os.setuid(user_uid)
        return set_ids
