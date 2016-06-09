from __future__ import print_function
import os
from ovirtvmbackup import OvirtBackup
import shutil

path_export = '/exportdomain/'
vms_path = '/master/vms/'
images_path = '/images/'
export_name = 'LabExport'

def create_dirs(vm_name, export_path):
    try:
        os.makedirs(export_path + vm_name + vms_path)
        os.makedirs(export_path + vm_name + images_path)
    except OSError as e:
        print(e)

def mv_data(new_name, export, source, destination):
    st = manage.get_export_domain(new_name)
    if export_name == st.name:
        dest = path_export + new_name + destination
        os.chdir(export + st.id + destination)
        shutil.move(source, dest)

manage = OvirtBackup('https://rhevm.i-t-m.local', 'lperez@itmlabs.local', 'lab2016.')
manage.connect()

disks = manage.api.vms.get('Web01-snap').disks.list()
vm = manage.api.vms.get('Web01-snap')

objects = { "Disks": list(), "Vms": list() }

objects["Vms"].append(vm.id)

for disk in disks:
    print("Disk {} ID: {}".format(disk.name, disk.id))
    objects["Disks"].append(disk.id)

print("VM {} ID: {}".format(vm.name, vm.id))
print(objects)

vm_new = vm.name

create_dirs(vm.name, path_export)

for disk in objects["Disks"]:
    mv_data(vm_new, path_export, disk, images_path)

for vm in objects["Vms"]:
    mv_data(vm_new, path_export, vm, vms_path)