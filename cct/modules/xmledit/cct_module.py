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
from cct.lib.xmlutils import add_element
from cct.module import Module
logger = logging.getLogger('cct')

class XML(Module):

    def insert_element(self, xmlfile, xpath, snippet):
        add_element(xmlfile, xpath, snippet)

        

