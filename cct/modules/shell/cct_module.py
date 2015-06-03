"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import subprocess

from cct.errors import CCTError
from cct.module import Module


class Shell(Module):

    def shell(self, *command):
        self.logger.debug("Executing shell command: '%s'" % " ".join(command))
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
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
            raise CCTError, "Command '%s' failed" % " ".join(command)
