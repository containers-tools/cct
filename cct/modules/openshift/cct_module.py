
"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.
This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""
import fileinput
import glob
import os
import shutil
import subprocess

from cct.errors import CCTError
from cct.module import Module

class Openshift(Module):
    jboss_home = os.getenv("JBOSS_HOME")
    sources_dir = None

    def setup(self, sources_dir="."):
        self.sources_dir = sources_dir

    def setup_jolokia(self, version):
        """ setup jolokia agent for jboss """
        # Add Jolokia (http://www.jolokia.org/) to expose all MBeans
        shutil.copy("%s/jolokia-jvm-%s-agent.jar" %(self.sources_dir, version),
                    "%s/jolokia.jar" %self.jboss_home)
        # Start Jolokia agent on boot
        with open('%s/bin/standalone.conf' %self.jboss_home, 'w') as f:
            for line in fileinput.input(self._get_resource_path(__name__, "data/standalone.conf")):
                f.write(line)

    def add_ose_layer(self):
        """ """
        shutil.copytree(self._get_resource_path(__name__, "data/modules"), "%s/" %self.jboss_home)
        for module in ['org/jgroups',
                       'org/jboss/as/clustering/common',
                       'org/jboss/as/clustering/jgroups',
                       'org/jboss/as/ee']:
                for jar in glob.glob("%s/modules/system/layers/base/.overlays/*/%s/main/*.jar"
                                     %(self.jboss_home, module)):
                    os.symlink(os.basename(jar), jar)

    def add_custom_launch_script(self):
        shutil.copy(self._get_resource_path(__name__, "data/openshift-launch.sh"),
                    "%s/bin/" %self.jboss_home)
        shutil.copytree(self._get_resource_path(__name__, "data/launch"),
                        "%s/bin/launch" %self.jboss_home)

    def setup_liveness_probe(self):
        shutil.copy(self._get_resource_path(__name__, "data/livenessProbe.sh"),
                    "%s/bin/" %self.jboss_home)

    def setup_readiness_probe(self):
        shutil.copy(self._get_resource_path(__name__, "data/readinessProbe.sh"),
                    "%s/bin/" %self.jboss_home)


    def teardown(self):
        self.shell("chmod a+x $JBOSS_HOME/bin/*.sh")
        self.shell("chmod -R a+rwX ${SCRIPT_DIR} ${JBOSS_HOME} ${HOME} $DEPLOYMENTS_DIR")


    def setup_logging(self):
        """"""
        # Configure logging
        # (TODO: Move org/jboss/logmanager/ext from "base" to "openshift" layer, and override org/jboss/logging as we do for modules above)
        os.makedirs("%s/modules/system/layers/base/org/jboss/logmanager/ext/main/" %self.jboss_home)
        shutil.copy(self._get_resource_path(__name__, "data/logging.properties"),
                    "%s/standalone/configuration/" %self.jboss_home)
        shutil.copy("%s/javax.json-1.0.4.jar" %self.sources_dir,
                    "%s/modules/system/layers/base/org/jboss/logmanager/ext/main/" %self.jboss_home)
        shutil.copy("%s/jboss-logmanager-ext-1.0.0.Alpha2-redhat-1.jar" %self.sources_dir,
                    "%s/modules/system/layers/base/org/jboss/logmanager/ext/main/" %self.jboss_home)
        self.shell("sed -i 's|org.jboss.logmanager|org.jboss.logmanager.ext|' $JBOSS_HOME/modules/system/layers/base/org/jboss/logging/main/module.xml")

    def add_custom_configfile(self):
        shutil.copy(self._get_resource_path(__name__, "data/standalone-openshift.xml"),
                    "%s/standalone/configuration/" %self.jboss_home)

    def add_amq_rar(self):
        shutil.copy("%s/activemq-rar-5.11.1.rar" %self.sources_dir,
                    "%s/standalone/deployments/activemq-rar.rar" %self.jboss_home)

    def inject_maven_settings(self):
        os.makedirs("%s/.m2" %os.getenv("HOME"))
        shutil.copy(self._get_resource_path(__name__,  "data/jboss-settings.xml"),
                "%s/.m2/settings.xml" %os.getenv("HOME"))

    def link_java_db_drivers(self):
        # Link mysql java driver from rpm
        os.makedirs("%s/modules/system/layers/openshift/com/mysql/main/" %self.jboss_home)
        os.symlink("/usr/share/java/mysql-connector-java.jar",
                   "%s/modules/system/layers/openshift/com/mysql/main/mysql-connector-java.jar" %self.jboss_home)
        # Link postgres java driver from rpm
        os.makedirs("%s/modules/system/layers/openshift/org/postgresql/main/" %self.jboss_home)
        os.symlink("/usr/share/java/postgresql-jdbc.jar",
                   "%s/modules/system/layers/openshift/org/postgresql/main/postgresql-jdbc.jar" %self.jboss_home)

        # Link mongo java driver from rpms
        os.makedirs("%s/modules/system/layers/openshift/org/mongodb/main/" %self.jboss_home)
        os.symlink("/opt/rh/mongodb24/root/usr/share/java/mongo.jar",
                   "%s/modules/system/layers/openshift/org/mongodb/main/mongo.jar" %self.jboss_home)

    def remove_console(self):
        shutil.rmtree("%s/modules/system/layers/base/org/jboss/as/console" %self.jboss_home)
        for console in glob.glob("%s/modules/system/layers/base/.overlays/*/org/jboss/as/console" %self.jboss_home):
            shutil.rmtree(console)

    def setup_jdk(self, version):
        self.shell("alternatives --install /usr/bin/java java /usr/lib/jvm/java-%s/jre/bin/java 1" %version)
        self.shell("alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-%s/bin/javac 1" %version)
        self.shell("alternatives --set java /usr/lib/jvm/java-%s/jre/bin/java" %version)
        self.shell("alternatives --set javac /usr/lib/jvm/java-%s/bin/javac" %version)

    def setup_s2i(self):
        """ copies s2i scripts to image """
        s2i = self._get_resource_path(__name__, 'data/s2i')
        shutil.copytree(s2i, "/usr/local/s2i")
        for root, dirs, files in os.walk("/usr/loca/s2i"):
            for d in dirs:
                target = os.path.join(root, d)
                os.chown(target, "jboss", "jboss")
                os.chmod(target, 0o755)

    def add_openshift_ping(self, version):
        """Adds openshift ping implementation"""
        os.makedirs("%s/modules/system/layers/openshift/org/openshift/ping/main/" %self.jboss_home)
        os.makedirs("%s/modules/system/layers/openshift/net/oauth/core/main/" %self.jboss_home)
        for name in ['common',
                     'dns',
                     'kube']:
            shutil.copy("%s/openshift-ping-%s-%s.jar" %(self.sources_dir, name, version),
                    "%s/modules/system/layers/openshift/org/openshift/ping/main/" %self.jboss_home)
        shutil.copy("%s/oauth-20100527.jar" %self.sources_dir,
                    "%s/modules/system/layers/openshift/net/oauth/core/main/" %self.jboss_home)

    def setup_deployment_dir(self, directory="/deployments"):
        shutil.move("%s/standalone/deployments" %self.jboss_home,
                    directory)
        os.symlink(directory, "%s/standalone/deployments" %self.jboss_home)
        os.chown(directory, 185, 185)


    def shell(self, *command):
        """
        Runs given comman in a shell
        """
        self.logger.debug("Executing shell command: '%s'" % " ".join(command))
        process = subprocess.Popen(
            " ".join(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True)
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
