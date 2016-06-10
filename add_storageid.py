from __future__ import print_function
from xml.dom import minidom

# file_name = "/home/binary/a583ffd9-3a88-4347-b9b2-5bbce28414f7.ovf"
file_name_old = "/home/binary/696121ff-d098-4b3b-bd23-f357037608b1.ovf"
file_name_new = "/home/binary/b2f27e88-71a9-4934-8ad1-8b933a7e7ff4.ovf"


xml_doc = minidom.parse(file_name_old)
xml_doc_new = minidom.parse(file_name_new)

disks_old = xml_doc.getElementsByTagName('Disk')
disks_new = xml_doc_new.getElementsByTagName('Disk')
# print(disks)
# <rasd:StorageId>5ae04d0f-93c7-48a8-810c-4c124e40802c</rasd:StorageId>
st_id = '5ae04d0f-93c7-48a8-810c-4c124e40802c'
disks = list()

StorageId = xml_doc.createElement("rasd:StorageId")
content = xml_doc.createTextNode(st_id)
StorageId.appendChild(content)
print(StorageId.toxml())

for item in xml_doc.getElementsByTagName("Device"):
    if item.firstChild.nodeValue == "disk":
        disks.append(item)
        parent = item.parentNode
        print("Current")
        print("****************")
        print(item.toxml())
        print(parent.toxml())
        print("*/*/*/*/*/*/**/*/*")
        print("New")
        print("****************")
        parent.appendChild(StorageId)
        print(parent.toxml())
        print("*/*/*/*/*/*/**/*/*")
