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
from cct.lib.xmlutils import XMLEdit
from cct.module import Module
logger = logging.getLogger('cct')

class XML(Module):
    xmledit = None

    def setup(self, xmlfile, *namespaces):
        self.xmledit = XMLEdit(xmlfile, namespaces)

    def insert(self, xpath, snippet):
        self.xmledit.add_element(xpath, snippet)


    
