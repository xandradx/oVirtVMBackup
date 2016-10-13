#!/bin/env python
from __future__ import print_function

import re
from subprocess import check_call, CalledProcessError, check_output

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
    try:
        check_output(["sudo", "dsmc", "retrieve", os.path.join(path, directory) + "/", "-subdir=yes"])
        return 1
    except CalledProcessError as error:
        return error.returncode

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

def export_path_id(path):
    pattern = '[\w]{8}(-[\w]{4}){3}-[\w]{12}$'
    for f in os.listdir(path):
        if re.search(pattern, f):
            folder = os.path.join(path, f)
            if os.path.isdir(folder):
                return folder


def restore(path, directory):
    try:
        path_export = export_path_id(path=path)
        imgs = os.path.join(path, directory, "images")
        vms = os.path.join(path, directory, "master", "vms")
        export_imgs = os.path.join(path_export, "images")
        ovf, dir_vm = ovf_get(vms)
        disksg = parse_xml(ovf)
        restore_imgs(disksg=disksg, imgs=imgs, export_imgs=export_imgs)
        export_vms = os.path.join(path_export, "master", "vms")
        shutil.move(dir_vm, export_vms)
    except OSError as e:
        print(e)


def main():
    path, directory = args()
    if not os.path.exists(path):
        print("path {} doesn't exists".format(path))
    else:
        print("Get {} from TSM".format(directory))
        if get_tsm(path=path, directory=directory):
            restore(path=path, directory=directory)
            shutil.rmtree(os.path.join(path, directory))
        else:
            print("TSM not find {} backup".format(directory))
            exit(1)

if __name__ == '__main__':
    main()