"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import subprocess

from cct.errors import CCTError
from cct.module import Module
from cct.lib.file_utils import create_dir


class git(Module):

    def _run_cmd(self, command):
        self.logger.debug("Executing shell command: '%s'" % " ".join(command))
        process = subprocess.Popen(
            " ".join(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
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

    def checkout(self, giturl, path, commit=None):
        """
        Checkouts git repository.

        Args:
            giturl: url for git repository
            path: the path a repository is cloned to
            commit: git commit to be checkouted, default is tip of default branch
        """
        create_dir(path)
        command = "git clone " + giturl + " " + path
        try:
            self._run_cmd(command.split())
        except:
            raise
        if commit:
            command = "cd " + path + " && git checkout " + commit
            try:
                self._run_cmd(command.split())
            except:
                raise
