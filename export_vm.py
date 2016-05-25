#!/bin/env python
__author__ = 'Luis Perez'

from funciones import *
import argparse
from time import strftime
import os

def main():
    """Principal Program"""
    ################# Options ###################
    parser = argparse.ArgumentParser(description='Automatic export virtual machine RHEV',
        prog='export_vm', usage='%(prog)s [options]')
    parser.add_argument('-m', '--manager', metavar='rhevm.i-t-m.local', help='FQDN Manager RHEV', required=True)
    parser.add_argument('-n', '--name', metavar='VM01', help='Name of virtual machine', required=True)
    parser.add_argument('-u', '--user', metavar='admin@internal', help='username with admin privileges DEFAULT=admin',
                        default='admin@internal')
    parser.add_argument('-p', '--password', metavar='p4ssw0rd', help='password for the user', required=True)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    args = parser.parse_args()
    #####################Mandatory Params########################
    time = strftime("%Y%m%d")
    desc_snap = "%s-%s" % (args.name, time)
    server = args.manager
    name = args.name
    username = args.user
    password = args.password
    rhevm_url = "https://%s" % (server)
    ########################################################

    api = connect(rhevm_url,username,password)
    vm = api.vms.get(name)
    new_name = "%s-backup" % vm.name

    ###CREANDO SNAPSHOT#####
    if api.vms.get(new_name):
        print "VM %s already exists please delete and run again" % new_name
        exit(1)

    if len(vm.snapshots.list(description=desc_snap)) != 0:
        print "Snapshot with description %s already exists please delete and run again" % desc_snap
        exit(1)

    create_snap(desc_snap, vm)
    id_snap = get_snap_id(desc_snap, vm)
    wait_snap(vm, id_snap)
    print("snapshot %s created...") % desc_snap
    ###CREANDO VM EXPORT#####
    create_vm_to_export(vm, id_snap, api, new_name)
    wait(api,new_name,'0')
    delete_snap(desc_snap,vm)
    print("Delete Snapshot...")
    print("Export Machine Created...")
    ###EXPORT VIRTUAL MACHINE###
    print("Export Virtual Machine as %s ...") % new_name
    export = get_export_domain(api,vm)
    export_vm(new_name,api,export)
    wait(api,new_name,'1')
    print("Export Virtual Machine as %s Finished...") % new_name
    print_info(api,new_name)
    del_new_vm(new_name,api)
    print("Delete Temporal Virtual Machine %s ") % new_name

    api.disconnect()
    exit(0)


if __name__ == '__main__':
    main()
