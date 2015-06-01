"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""
from __future__ import print_function
import logging
from cct.lib.xmlutils import add_element, does_element_exists, update_attrib, update_regex, delete_element


from cct.module import Module
logger = logging.getLogger('cct')


class AMQ(Module):
    activemq_xml = "activemq.xml"
    ini_file = "users.ini"
    
    def setup(self, args):
        self.activemq_xml = args[0]
        self.ini_file = args[1]

    def configure_transport(self, args):
        transport_template = '<transportConnector name="%s" uri="%s://0.0.0.0:%s?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>'
        transports = []
        for transport in args[0].split(","):
            transport = transport.strip()
            if transport == "openwire":
                transports.append(transport_template % (transport, "tcp", "61616"))
                transports.append(transport_template % (transport+"+ssl", "ssl" , "61617"))                             
            if transport == "stomp":
                transports.append(transport_template % (transport, transport, "61613"))
                transports.append(transport_template % (transport+"+ssl", transport+"+ssl", "61612"))  
            if transport == "amqp":
                transports.append(transport_template % (transport, transport, "5672"))
                transports.append(transport_template % (transport+"+ssl", transport+"+ssl", "5671"))  
            if transport == "mqtt":
                transports.append(transport_template % (transport, transport, "1833"))
                transports.append(transport_template % (transport+"+ssl", transport+"+ssl", "8883"))  
        if transports:
            delete_element(self.activemq_xml, ".//*[local-name()='transportConnector']")
            for transport in transports:
                add_element(self.activemq_xml, ".//*[local-name()='transportConnectors']", transport)

       
    def update_key_store_pwd(self, args):
        password = args[0]
        update_attrib(self.activemq_xml, ".//*[local-name()='sslContext' and @keyStorePassword]", "keyStorePassword", password)

    def update_trust_store_pwd(self, args):
        password = args[0]
        update_attrib(self.activemq_xml, ".//*[local-name()='sslContext' and @trustStorePassword]", "trustStorePassword", password)

    def update_framesize(self, args):
        max_framesize = args[0]
        update_regex(self.activemq_xml, ".//*[local-name()='transportConnector' and @uri]", "uri", "(wireFormat\\.maxFrameSize=)([0-9]*)", "\g<1>"+max_framesize)

    def update_max_connections(self, args):
        max_connection = args[0]
        update_regex(self.activemq_xml, ".//*[local-name()='transportConnector' and @uri]", "uri",  "(maximumConnections=)([0-9]*)", "\g<1>"+max_connection)

    def update_storage(self, args):
        limit = args[0]
        update_attrib(self.activemq_xml, ".//*[local-name()='storeUsage' and @limit]", "limit", limit)

    def define_queue(self, args):
        if not does_element_exists(self.activemq_xml, ".//*[local-name()='destinations']"):
            add_element(self.activemq_xml, ".//*[local-name()='broker']", "<destinations></destinations>")

        for q_name in args[0].split(","):
            queue = ('<queue physicalName="%s"/>' % q_name)
            add_element(self.activemq_xml, ".//*[local-name()='destinations']", queue)
            
    def define_topic(self, args):
        if not does_element_exists(self.activemq_xml, ".//*[local-name()='destinations']"):
            add_element(self.activemq_xml, ".//*[local-name()='broker']", "<destinations></destinations>")

        for t_name in args[0].split(","):
            topic = ('<topic physicalName="%s"/>' % t_name)
            add_element(self.activemq_xml, ".//*[local-name()='destinations']", topic)
            
    def setup_authentication(self, args):
        username = args[0]
        password = args[1]
        user_ini_file='''#################################################################################
#
#    Licensed to the Apache Software Foundation (ASF) under one or more
#    contributor license agreements.  See the NOTICE file distributed with
#    this work for additional information regarding copyright ownership.
#    The ASF licenses this file to You under the Apache License, Version 2.0
#    (the "License"); you may not use this file except in compliance with
#    the License.  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
################################################################################
#
#
# This file contains the valid users who can log into JBoss A-MQ.
# Each line has to be of the format:
#
# USER=PASSWORD
#
# You must have at least one users to be able to access JBoss A-MQ resources
#
#Mon Jun 01 13:36:51 CEST 2015
%s=%s'''
        with open(self.ini_file, "w") as in_file:
            print(user_ini_file % (username, password), file=in_file)
        add_element("activemq.xml",
                    ".//*[local-name()='broker']/*[local-name()='plugins']",
                    '<jaasAuthenticationPlugin configuration="activemq"/>') 
        


