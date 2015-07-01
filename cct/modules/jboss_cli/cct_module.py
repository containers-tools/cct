"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""
import logging
from cct.errors import CCTError
from cct.module import Module
from subprocess import PIPE, Popen

logger = logging.getLogger('cct')

class jboss_cli(Module):
    jboss_home = '/opt/eap'
    jboss_process = None
    jboss_cli_runner = None

    def setup(self, jboss_home='/opt/eap/'):
        self.jboss_home = jboss_home
        logger.debug('launching standalone jboss: "%s"' % (jboss_home + "/bin/standalone.sh"))
        self.jboss_process = Popen(jboss_home + "/bin/standalone.sh", stdout=PIPE, stdin=PIPE)

    def _run_jboss_cli(self, command):
        logger.debug('launching cli: "%s"' % (self.jboss_home + "/bin/jboss-cli.sh"))
        self.jboss_cli_runner = Popen(self.jboss_home + "/bin/jboss-cli.sh", stdout=PIPE, stdin=PIPE)
        logger.info("running jboss-cli command %s" %command)
        line = self.jboss_cli_runner.communicate(input= "connect \n" +  command + "\nexit \n")
        logger.debug("command '%s' returned: %s" %(command, line))

    def run_cli(self, *command):
        logger.debug(command)
        self._run_jboss_cli(' '.join(command))

    def teardown(self):
        if self.jboss_process:
            logger.debug("stopping jboss AS")
            self.jboss_process.send_signal(15)
