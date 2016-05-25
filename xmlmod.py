__author__ = 'binary'
from xml.dom import minidom

xml_doc = minidom.parse('/home/binary/87a6f03e-e368-437b-8348-abed48b3a69e.ovf')
Content = xml_doc.getElementsByTagName('Content')
for node in Content:
    section = node.getElementsByTagName('Section')
    for sect in section:
        item = sect.getElementsByTagName('Item')
        print item.childNodes[0].nodeValue
        #for mac in item:
        #    macs = mac.getElementsByTagName('rasd:MACAddress')
        #    print macs
        #    macs = mac[0].nodeValue
        #    print macs

