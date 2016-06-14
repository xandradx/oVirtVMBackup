from __future__ import print_function
from xml.dom import minidom
from ovirtvmbackup import OvirtBackup

ovbackup = OvirtBackup(
    "https://rhevm.i-t-m.local",
    'lperez@itmlabs.local', 'lab2016.'
)
ovbackup.connect()


def get_storage_xml(xml_export):
    xml_tag = xml_export.getElementsByTagName("rasd:StorageId")
    storage_ids = list()
    for storage_id in xml_tag:
        storage_ids.append(storage_id.firstChild.nodeValue)
    return storage_ids


def add_line_storage_xml(xml_original, xml_export):

    xml_doc = minidom.parse(xml_original)
    xml_doc_new = minidom.parse(xml_export)

    count = 0

    for item in xml_doc.getElementsByTagName("Device"):
        if item.firstChild.nodeValue == "disk":
            st_id = get_storage_xml(xml_doc_new)
            StorageId = xml_doc.createElement("rasd:StorageId")
            content = xml_doc.createTextNode(st_id[count])
            StorageId.appendChild(content)
            parent = item.parentNode
            parent.appendChild(StorageId)
            count += 1
    with open('new-a583ffd9-3a88-4347-b9b2-5bbce28414f7.ovf', 'a') as newfile:
        newfile.write(xml_doc.toxml())
    print(xml_doc.toprettyxml())


ovbackup.save_ovf("Web01", "oVirtBackup")

original_ovf = '/tmp/a583ffd9-3a88-4347-b9b2-5bbce28414f7.ovf'
export_ovf = '/tmp/b2f27e88-71a9-4934-8ad1-8b933a7e7ff4.ovf'
add_line_storage_xml(original_ovf, export_ovf)
