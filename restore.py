from __future__ import print_function
import configargparse
import os, shutil

from xml.dom import minidom


def args():
    p = configargparse.ArgParser(
        default_config_files=['/etc/restore.cfg']
    )
    p.add_argument('-c', '--config', is_config_file=True, help='config file path')
    p.add_argument('-e', '--export-domain', required=True, help='name of export domain')
    p.add_argument('-P', '--path-export', required=True, help='path of export domain')
    p.add_argument('vm', help='name of virtual machine')


    options = p.parse_args()
    export_domain = options.export_domain
    virtual_machine = options.vm
    export_path = options.path_export
    return export_domain, export_path, virtual_machine

def ovf_get(vm_path):
    for root, dirs, files in os.walk(vm_path):
        for file in files:
            if file.endswith(".ovf"):
                return os.path.join(root, file)

def parse_xml(xml_path):
    xml_ovf = minidom.parse(xml_path)
    disks = xml_ovf.getElementsByTagName('Disk')
    dgroups = list()
    for disk in range(len(disks)):
        disk_split = disks[disk].attributes["ovf:fileRef"].value
        dgroups.append(disk_split.split("/")[0])
    return dgroups


def restore(export_name, path, vm_name):
    imgs = os.path.join(path, vm_name, "images")
    vms = os.path.join(path, vm_name, "master", "vms")
    export_vms = os.path.join(path, "master", "vms")
    export_imgs = os.path.join(path, "images")
    ovf = ovf_get(vms)
    disksg = parse_xml(ovf)
    for disk in disksg:
        print(os.path.join(imgs, disk))
        print(export_vms)
        disk_src = os.path.join(imgs, disk)
        shutil.move(disk_src, export_vms)
    print(disksg)


def main():
    export, path, virtual_machine = args()
    restore(export_name=export, path=path, vm_name=virtual_machine)

if __name__ == '__main__':
    main()