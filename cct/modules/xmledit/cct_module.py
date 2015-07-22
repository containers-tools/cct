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
        """
        setups xmledit module

        Args:
            xmlfile: path to an xml file
            namespaces: list of namespaces in xml file (optional - namespaces are detected automatically and default namespace name is set to "ns" for xpath purposes
        """   
        self.xmledit = XMLEdit(xmlfile, namespaces)

    def insert(self, xpath, snippet):
        """
        inserts xml snippet into xpath location

        Args:
            xpath: xpath to locate place for inserting snippet
            snippet: xml snippet to insert
        """
        self.xmledit.add_element(xpath, snippet)

    def delete(self, xpath):
        """
        deletes element and all of its child from an xml file

        Args:
           xpath: xpath to locate an element to be removed
        """
        self.xmledit.delete_element(xpath)

    def replace_attribute(self, xpath, attrib, value):
        """
        replaces/defines an attribute in element by defined value

        Args:
            xpath: xpath to locate element for attribute update
            attrib: name of attribute to define/replace
            value: value for attribute
        """
        self.xmledit.update_attrib(xpath, attrib, value)

    def replace_attribute_regex(self, xpath, attrib, pattern, value):
        """
        updates attribute with regex pattern/value combo

        Args:
            xpath: xpath to locate element for attribute update
            attrib: name of attribute to define/replace
            pattern: pattern to locate part of the attribute value to replace
            value: value for regex
        """

        self.xmledit.update_regex(xpath, attrib, pattern, value)

    def exist(self, xpath):
        """
        checks if element exists

        Args:
            xpath: xpath expression
        """
        self.xmledit.exists(xpath)
