"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""
from __future__ import print_function
from cct.lib.xmlutils import add_element, does_element_exists, update_attrib, update_regex, delete_element

from cct.module import Module
from cct.errors import CCTError

class AMQ(Module):
    activemq_xml = "activemq.xml"
    ini_file = "users.ini"

    def setup(self, activemq_xml, ini_file):
        self.activemq_xml = activemq_xml
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
            delete_element(
                self.activemq_xml, ".//*[local-name()='transportConnector']")
            for transport in transports:
                add_element(
                    self.activemq_xml, ".//*[local-name()='transportConnectors']", transport)

        self.logger.info("Transports configured!")

    def update_key_store_pwd(self, password):
        self.logger.info("Updating key store password...")
        update_attrib(
            self.activemq_xml, ".//*[local-name()='sslContext' and @keyStorePassword]", "keyStorePassword", password)

    def update_trust_store_pwd(self, password):
        self.logger.info("Updating trust store password...")
        update_attrib(
            self.activemq_xml, ".//*[local-name()='sslContext' and @trustStorePassword]", "trustStorePassword", password)

    def update_framesize(self, max_framesize):
        self.logger.info("Updating maxFrameSize parameter...")
        update_regex(self.activemq_xml, ".//*[local-name()='transportConnector' and @uri]",
                     "uri", "(wireFormat\\.maxFrameSize=)([0-9]*)", "\g<1>" + max_framesize)

    def update_max_connections(self, max_connection):
        self.logger.info("Updating maximumConnections parameter...")
        update_regex(self.activemq_xml, ".//*[local-name()='transportConnector' and @uri]",
                     "uri",  "(maximumConnections=)([0-9]*)", "\g<1>" + max_connection)

    def update_storage(self, limit):
        update_attrib(
            self.activemq_xml, ".//*[local-name()='storeUsage' and @limit]", "limit", limit)

    def define_queue(self, queues):
        if not does_element_exists(self.activemq_xml, ".//*[local-name()='destinations']"):
            add_element(
                self.activemq_xml, ".//*[local-name()='broker']", "<destinations></destinations>")

        for name in queues.split(","):
            name = name.strip()
            self.logger.info("Adding '%s' queue..." % name)
            queue = ('<queue physicalName="%s"/>' % name)
            add_element(
                self.activemq_xml, ".//*[local-name()='destinations']", queue)

    def define_topic(self, topics):
        if not does_element_exists(self.activemq_xml, ".//*[local-name()='destinations']"):
            add_element(
                self.activemq_xml, ".//*[local-name()='broker']", "<destinations></destinations>")

        for name in topics.split(","):
            name = name.strip()
            self.logger.info("Adding '%s' topic..." % name)
            topic = ('<topic physicalName="%s"/>' % name)
            add_element(
                self.activemq_xml, ".//*[local-name()='destinations']", topic)

    def setup_authentication(self, username, password):
        self.logger.debug("Configuring authentication...")
        
        if not (username and password):
            raise CCTError, "Username or password not provided, we cannot proceed with setting up AMQ authentication without it"

        username = username.strip()
        password = password.strip()

        with open(self.ini_file, "w") as ini_file:
            ini_file.write("%s=%s\n" % (username, password))

        add_element(self.activemq_xml,
                    ".//*[local-name()='broker']/*[local-name()='plugins']",
                    '<jaasAuthenticationPlugin configuration="activemq"/>')

        self.logger.debug("Authentication configured")

