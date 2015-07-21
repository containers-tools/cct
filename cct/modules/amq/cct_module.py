"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""
from __future__ import print_function
from cct.lib.xmlutils import XMLEdit
from cct.module import Module
from cct.errors import CCTError


class AMQ(Module):
    ini_file = "users.ini"
    xmledit = None

    def setup(self, activemq_xml, ini_file):
        self.xmledit = XMLEdit(activemq_xml)
        self.ini_file = ini_file

    def configure_transport(self, transport_list):
        self.logger.info("Configuring transports...")
        transport_template = '<transportConnector name="%s" uri="%s://0.0.0.0:%s?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>'
        transports = []
        for transport in transport_list.split(","):
            transport = transport.strip()
            self.logger.info("Configuring '%s' transport..." % transport)
            if transport == "openwire":
                transports.append(transport_template %
                                  (transport, "tcp", "61616"))
                transports.append(transport_template %
                                  (transport + "+ssl", "ssl", "61617"))
            if transport == "stomp":
                transports.append(transport_template %
                                  (transport, transport, "61613"))
                transports.append(
                    transport_template % (transport + "+ssl", transport + "+ssl", "61612"))
            if transport == "amqp":
                transports.append(transport_template %
                                  (transport, transport, "5672"))
                transports.append(
                    transport_template % (transport + "+ssl", transport + "+ssl", "5671"))
            if transport == "mqtt":
                transports.append(transport_template %
                                  (transport, transport, "1833"))
                transports.append(
                    transport_template % (transport + "+ssl", transport + "+ssl", "8883"))
        if transports:
            self.xmledit.delete_element(".//*[local-name()='transportConnector']")
            for transport in transports:
                self.xmledit.add_element(".//*[local-name()='transportConnectors']", transport)

        self.logger.info("Transports configured!")

    def update_key_store_pwd(self, password):
        self.logger.info("Updating key store password...")
        self.xmledit.update_attrib(".//*[local-name()='sslContext' and @keyStorePassword]", "keyStorePassword", password)

    def update_trust_store_pwd(self, password):
        self.logger.info("Updating trust store password...")
        self.xmledit.update_attrib(".//*[local-name()='sslContext' and @trustStorePassword]", "trustStorePassword", password)

    def update_framesize(self, max_framesize):
        self.logger.info("Updating maxFrameSize parameter...")
        self.xmledit.update_regex(".//*[local-name()='transportConnector' and @uri]",
                     "uri", "(wireFormat\\.maxFrameSize=)([0-9]*)", "\g<1>" + max_framesize)

    def update_max_connections(self, max_connection):
        self.logger.info("Updating maximumConnections parameter...")
        self.xmledit.update_regex(".//*[local-name()='transportConnector' and @uri]",
                     "uri",  "(maximumConnections=)([0-9]*)", "\g<1>" + max_connection)

    def update_storage(self, limit):
        self.xmledit.update_attrib(".//*[local-name()='storeUsage' and @limit]", "limit", limit)

    def define_queue(self, queues):
        if not self.xmledit.does_element_exists(".//*[local-name()='destinations']"):
            self.xmledit.add_element(".//*[local-name()='broker']", "<destinations></destinations>")

        for name in queues.split(","):
            name = name.strip()
            self.logger.info("Adding '%s' queue..." % name)
            queue = ('<queue physicalName="%s"/>' % name)
            self.xmledit.add_element(".//*[local-name()='destinations']", queue)

    def define_topic(self, topics):
        """
        Configures topics.
        """
        if not topics:
            raise CCTError("No topic names provided, we cannot proceed with setting up AMQ topics without it")

        if not self.xmledit.does_element_exists(".//*[local-name()='destinations']"):
            self.xmledit.add_element(".//*[local-name()='broker']", "<destinations></destinations>")

        for name in topics.split(","):
            name = name.strip()
            topic = '<topic physicalName="%s"/>' % name

            # Add the element only if it does not exist
            if self.xmledit.does_element_exists(".//*[local-name()='destinations']/*[local-name()='topic' and @physicalName='%s']" % name):
                self.logger.info("Topic '%s' already exists..." % name)
                return

            self.logger.info("Adding '%s' topic..." % name)
            self.xmledit.add_element(".//*[local-name()='destinations']", topic)

    def setup_authentication(self, username, password):
        """
        Configures authentication for AMQ. Adds a user with spefied password and
        enables the jaas authentication.
        """
        self.logger.debug("Configuring authentication...")

        if not (username and password):
            raise CCTError("Username or password not provided, we cannot proceed with setting up AMQ authentication without it")

        username = username.strip()
        password = password.strip()

        with open(self.ini_file, "w") as ini_file:
            ini_file.write("%s=%s\n" % (username, password))

        self.xmledit.add_element(".//*[local-name()='broker']/*[local-name()='plugins']", '<jaasAuthenticationPlugin configuration="activemq"/>')

        self.logger.debug("Authentication configured")
