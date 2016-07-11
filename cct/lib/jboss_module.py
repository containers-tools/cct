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
import os
import tempfile
import shutil
from time import sleep, time
logger = logging.getLogger('cct')

class JBossCliModule(Module):
    jboss_timeout = None
    jboss_home = None
    jboss_process = None
    jboss_cli_runner = None

    def setup(self, jboss_home=None, jboss_timeout=120):
        self.jboss_timeout = jboss_timeout
        logger.debug("Got jboss home '%s'." %jboss_home)
        if jboss_home:
            self.jboss_home = jboss_home
        else:
            try:
                self.jboss_home = os.environ['JBOSS_HOME']
            except:
                logger.error("Cannot determine JBOSS_HOME location.")
                raise CCTError('Cannot determine JBOSS_HOME location.')
        logger.debug('launching standalone jboss: "%s"' % (self.jboss_home + "/bin/standalone.sh"))
        self.jboss_process = Popen(self.jboss_home + "/bin/standalone.sh", stdout=PIPE, stderr=PIPE)
        self._wait_for_as()

    def _wait_for_as(self):
        start = time()
        while time() < start + self.jboss_timeout:
            try:
                self._run_jboss_cli("connect")
                logger.debug("Application server is ready.")
                return
            except Exception as e:
                logger.debug("waiting for Application server to start. %s", e)
                sleep(5)
        logger.error("Cannot connect cli to application server.")
        raise CCTError("Cannot connect cli to application server.")

    def _run_jboss_cli(self, command):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write("%s \nexit" %command)
            tf.flush()
            logger.debug('launching cli: "%s %s"' % ((self.jboss_home + "/bin/jboss-cli.sh"), tf.name))
            cli = Popen([self.jboss_home + "/bin/jboss-cli.sh", "--connect", "--file=%s" %tf.name], stdout=PIPE, stderr=PIPE,)
            out, err = cli.communicate()
            if cli.returncode == 0:
                #success
                logger.debug('Command completed succesfully.')
                return
            else:
                logger.error('Command failed, msg: %s.' %(out + err))
                raise CCTError("Cannot run jboss_cli command return code: '%s'.", cli.returncode)

    def run_cli_batch(self, *command):
        """
        Runs any jboss comamnd in a batch.

        Args:
            command: jboss commands to run.
        """
        self._run_jboss_cli("batch \n%s\nrun-batch" %' '.join(command))

    def run_cli(self, *command):
        """
        Runs any jboss comamnd.

        Args:
            command: jboss commands to run.
        """
        logger.debug(command)
        self._run_jboss_cli(' '.join(command))

    def _clear(self):
        for part in ["log", "data", "tmp/vfs", "tmp/work", "configuration/standalone_xml_history"]:
            path = os.path.join(self.jboss_home, "standalone", part)
            if os.path.exists(path):
                shutil.rmtree(path)

    def teardown(self):
        if self.jboss_process:
            logger.debug("Stopping application server.")
            self._run_jboss_cli("shutdown")
            start = time()
            while self.jboss_process.poll() is None or time() > start + self.jboss_timeout :
                sleep(5)
                logger.debug("Waiting for application server to stop.")
            if self.jboss_process.poll():
                raise CCTError("Cannot stop application server.")
            else:
                if self.jboss_home:
                    self._clear()
