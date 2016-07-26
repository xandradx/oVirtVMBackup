from __future__ import print_function

from subprocess import check_call, CalledProcessError

import configargparse
import os, shutil

from xml.dom import minidom


def args():
    p = configargparse.ArgParser(
        default_config_files=['/etc/restore.cfg'],
        version='1.0'
    )
    p.add_argument('-c', '--config', is_config_file=True, help='config file path')
    p.add_argument('-P', '--path', help='path of export domain')
    p.add_argument('dir', help='name of dir is TSM')

    options = p.parse_args()
    directory = options.dir
    export_path = options.path
    return export_path, directory


def get_tsm(path,directory):
    dsmc = check_call(["sudo", "dsmc", "retrieve", os.path.join(path, directory) + "/", "-subdir=yes"])
    return dsmc

def ovf_get(vm_path):
    for root, dirs, files in os.walk(vm_path):
        for file in files:
            if file.endswith(".ovf"):
                return os.path.join(root, file), root

def parse_xml(xml_path):
    xml_ovf = minidom.parse(xml_path)
    disks = xml_ovf.getElementsByTagName('Disk')
    dgroups = list()
    for disk in range(len(disks)):
        disk_split = disks[disk].attributes["ovf:fileRef"].value
        dgroups.append(disk_split.split("/")[0])
    return dgroups


def restore_imgs(disksg, imgs, export_imgs):
    for disk in disksg:
        disk_src = os.path.join(imgs, disk)
        print("moving {} to {}".format(disk_src, export_imgs))
        shutil.move(disk_src, export_imgs)


def restore(path, directory):
    try:
        export_id = "e412a6d5-8d62-4df5-a71c-352c50287a55"
        imgs = os.path.join(path, directory, "images")
        vms = os.path.join(path, directory, "master", "vms")
        export_imgs = os.path.join(path, export_id, "images")
        ovf, dir_vm = ovf_get(vms)
        disksg = parse_xml(ovf)
        restore_imgs(disksg=disksg, imgs=imgs, export_imgs=export_imgs)
        export_vms = os.path.join(path, export_id, "master", "vms")
        shutil.move(dir_vm, export_vms)
    except OSError as e:
        print(e)


def main():
    path, directory = args()
    if not os.path.exists(path):
        print("path {} doesn't exists".format(path))
    else:
        if (get_tsm(path=path, directory=directory) == 0):
            restore(path=path, directory=directory)
        else:
            exit(1)

if __name__ == '__main__':
    main()
