from __future__ import print_function

from ovirtvmbackup.ovirtbackup import OvirtBackup
import os
from time import sleep
from progress.spinner import Spinner

virtual_machine = 'Guacamole'

manage = OvirtBackup("https://rhevm.i-t-m.local", 'lperez@itmlabs.local', 'lab2016.')

manage.connect()

export_name = "LabExport"

dc = manage.get_dc(virtual_machine)

export_attached = manage.get_export_domain(virtual_machine)

def verify_valid_export(vm, dc_id, export, current):
    if current == export:
        if manage.api.datacenters.get(id=dc_id).storagedomains.get(
                export).get_status().get_state() == "active":
            return 1
        else:
            return 2
    elif current != export:
        return 0

def detach_export(dc_id, export):
    if manage.api.datacenters.get(id=dc_id).storagedomains.get(export).delete():
        print("Detach OK")

def do_export_maintenance(dc_id, export):
    manage.api.datacenters.get(id=dc_id).storagedomains.get(export).deactivate()
    spinner = Spinner("waiting for maintenance Storage... ")
    while manage.api.datacenters.get(id=dc.id).storagedomains.get(
            export).get_status().get_state() != "maintenance":
        spinner.next()

def attach_export(dc_id, export_ok):
    if manage.api.datacenters.get(id=dc.id).storagedomains.add(manage.api.storagedomains.get(export_ok)):
        print('Export Domain was attached successfully')


def do_export_up(dc_id, export):
    if manage.api.datacenters.get(id=dc_id).storagedomains.get(export).activate():
        print('Export Domain was activate successfully')

def prepare_export(dc_id, vm, name_export):
    print("Distinto")
    do_export_maintenance(dc_id, name_export)
    detach_export(dc_id, name_export)

status_export = verify_valid_export(virtual_machine, dc.id, export_name, export_attached.name)

if export_attached is not None:
    if status_export == 1:
        print("Export {} is OK".format(export_name))
    elif status_export == 0:
        prepare_export(dc.id, virtual_machine, export_attached.name)
        attach_export(dc.id, export_name)
    elif status_export == 2:
        do_export_up(dc.id, export_name)
elif export_attached is None:
    attach_export(dc.id, export_name)


"""
dc = manage.get_dc('Guacamole')

print(manage.api.storagedomains.get(name="LabExport"))

# do attach
if manage.api.datacenters.get(id=dc.id).storagedomains.add(manage.api.storagedomains.get('LabExport')):
    print('Export Domain was attached successfully')

sleep(25)

# do maintenance storage domain
manage.api.datacenters.get(id=dc.id).storagedomains.get("LabExport").deactivate()
spinner = Spinner("waiting for maintenance Storage... ")
while manage.api.datacenters.get(id=dc.id).storagedomains.get("LabExport").get_status().get_state() != "maintenance":
    spinner.next()


# do detach storage domain
if manage.api.datacenters.get(id=dc.id).storagedomains.get("LabExport").delete():
    print("Detach OK")
"""
