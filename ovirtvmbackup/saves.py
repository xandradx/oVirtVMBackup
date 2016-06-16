from __future__ import print_function
from ovirtvmbackup import OvirtBackup
import fnmatch
import os

path_export = "/exportdomain/"
vms_path = "/master/vms/"
images_path = "/images/"

virtual_machine="Web01"
description="oVirtBackup"

ovbackup = OvirtBackup(
    "https://rhevm.i-t-m.local",
    'lperez@itmlabs.local', 'lab2016.'
)
ovbackup.connect()

# procedure for save new ovf
ovbackup.get_running_ovf(vm=virtual_machine, desc=description, path=path_export)
export_xml = ovbackup.export_xml_path(path=path_export, vm=virtual_machine, find_path=vms_path)
original_xml = ovbackup.export_xml_path(path=path_export, vm=virtual_machine)
xml_obj = ovbackup.add_storage_id_xml(original_xml, export_xml)
ovf_final = os.path.basename(original_xml)[8:]
vms_path_save = path_export + virtual_machine + vms_path
print(vms_path_save)
ovbackup.save_new_ovf(path=vms_path_save, name=ovf_final, xml=xml_obj)
ovbackup.delete_tmp_ovf(path=path_export + virtual_machine + "/running-" + ovf_final)
ovbackup.change_owner(path=path_export + virtual_machine)
