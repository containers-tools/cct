"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""

import logging
import xml.etree.ElementTree as ET


from cct.module import Module
logger = logging.getLogger('cct')

class XML(Module):

    def add_element(self, args):
        xmlfile = args[1]
        xpath = args[2]
        snipplet = args[3]

        tree = ET.parse(xmlfile)
        root = tree.getroot
        result = root.find(xpath)
        print (result)
        

