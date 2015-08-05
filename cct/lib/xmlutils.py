import re
from lxml import etree

class XMLEdit(object):
    namespaces = {}
    root = None
    xmlfile = None

    def __init__(self, xmlfile, namespaces=None):
        self.xmlfile = xmlfile
        self.tree = etree.parse(xmlfile)
        self.root = self.tree.getroot()
        if namespaces:
            for namespace in namespaces.split('|'):
                name, value = namespace.split(':',1)
                self.namespaces[name] = value
        else:
            self._getnamespaces()

    def _getnamespaces(self):
        for k,v in self.root.nsmap.iteritems():
            if k:
                self.namespaces[k] = v
            else:
                self.namespaces["ns"] =v

    def _writexml(self):
        with open(self.xmlfile, "w") as openfile:
            self.tree.write(openfile)

    def add_element(self, xpath, snippet):
        xmlsnippet = etree.fromstring(snippet)
        result = self.root.xpath(xpath, namespaces=self.namespaces)
        for element in result:
            element.append(xmlsnippet)
        self._writexml()

    def does_element_exists(self, xpath):
        if self.root.xpath(xpath, namespaces=self.namespaces):
            return True
        return False

    def update_attrib(self, xpath, attrib,  value):
        print  self.root.xpath(xpath, namespaces=self.namespaces)
        for element in self.root.xpath(xpath, namespaces=self.namespaces):
            element.attrib[attrib] = value
        self._writexml()

    def update_regex(self, xpath, attrib, pattern, value):
        for element in self.root.xpath(xpath, namespaces=self.namespaces):
            element.set(attrib, re.sub(pattern, value, element.get(attrib)))
        self._writexml()

    def delete_element(self, xpath):
        for element in self.root.xpath(xpath, namespaces=self.namespaces):
            element.getparent().remove(element)
        self._writexml()
