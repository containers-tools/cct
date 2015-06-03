import re
from lxml import etree


def _writexml(xmlfile, tree):
    with open(xmlfile, "w") as openfile:
        tree.write(openfile)

def add_element(xmlfile, xpath, snippet):
    xmlsnippet = etree.fromstring(snippet)
    tree = etree.parse(xmlfile)
    root = tree.getroot()
    result = root.xpath(xpath)
    for element in result:
        element.append(xmlsnippet)
    _writexml(xmlfile, tree)
        
def does_element_exists(xmlfile, xpath):
    tree = etree.parse(xmlfile)
    root = tree.getroot()
    if root.xpath(xpath):
        return True
    return False

def update_attrib(xmlfile, xpath, attrib,  value):
    tree = etree.parse(xmlfile)
    root = tree.getroot()
    for element in root.xpath(xpath):
        element.set(attrib, value)
    _writexml(xmlfile, tree)
        
def update_regex(xmlfile, xpath, attrib, pattern, value):
    tree = etree.parse(xmlfile)
    root = tree.getroot()
    for element in root.xpath(xpath):
        element.set(attrib, re.sub(pattern, value, element.get(attrib)))
    _writexml(xmlfile, tree)

def delete_element(xmlfile, xpath):
    tree = etree.parse(xmlfile)
    root = tree.getroot()
    for element in root.xpath(xpath):
        element.getparent().remove(element)
    _writexml(xmlfile, tree)
