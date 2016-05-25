from xml.dom import minidom

file_name = "/home/binary/87a6f03e-e368-437b-8348-abed48b3a69e.ovf"
xml_doc = minidom.parse(file_name)
Content = xml_doc.getElementsByTagName('Content')
for node in Content:
    section = node.getElementsByTagName('Section')
    for sect in section:
        item = sect.getElementsByTagName('Item')
        print(item.childNodes[0].nodeValue)
