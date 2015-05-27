"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""

import logging
import sys
import xml.etree.ElementTree as ET
from lxml import etree

from cct.module import Module
logger = logging.getLogger('cct')

class XML(Module):

    def run(self, operation):
        if operation.command == "add_element":
            self.add_element(operation.args)
        else:
            logger.info("unsuported operation %s with args %s" % (operation.command, operation.args ))


    def add_element(self, args):
        xmlfile = args[0]
        xpath = args[1]
        snipplet = args[2]
        xmlsniplet = etree.fromstring(snipplet)
        tree = etree.parse(xmlfile)
        root = tree.getroot()
        result = root.xpath(xpath)
        for element in result:
            element.append(xmlsniplet)
        print etree.tostring(tree)
        
        

        

