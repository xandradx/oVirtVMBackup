from __future__ import print_function
import configargparse
import os, shutil

def args():
    p = configargparse.ArgParser(
        default_config_files=['/etc/restore.cfg']
    )
    p.add_argument('-c', '--config', is_config_file=True, help='config file path')
    p.add_argument('-e', '--export-domain', required=True, help='name of export domain')
    p.add_argument('vm', help='name of virtual machine')


    options = p.parse_args()
    export_domain = options.export_domain
    virtual_machine = options.vm
    return export_domain, virtual_machine

def restore(export_name, vm_name):
    print(export_name)
    print(vm_name)

def main():
    export, virtual_machine = args()
    restore(export_name=export, vm_name=virtual_machine)

if __name__ == '__main__':
    main()