from __future__ import print_function
from xml.dom import minidom


file_name_old = "/opt/testxml/696121ff-d098-4b3b-bd23-f357037608b1.ovf"
file_name_new = "/opt/testxml/b2f27e88-71a9-4934-8ad1-8b933a7e7ff4.ovf"


xml_doc = minidom.parse(file_name_old)
xml_doc_new = minidom.parse(file_name_new)

disks_old = xml_doc.getElementsByTagName('Disk')
disks_new = xml_doc_new.getElementsByTagName('Disk')

st_id = '5ae04d0f-93c7-48a8-810c-4c124e40802c'
disks = list()


for item in xml_doc.getElementsByTagName("Device"):
    StorageId = xml_doc.createElement("rasd:StorageId")
    content = xml_doc.createTextNode(st_id)
    StorageId.appendChild(content)
    if item.firstChild.nodeValue == "disk":
        disks.append(item)
        parent = item.parentNode
        parent.appendChild(StorageId)

print(xml_doc.toxml())
