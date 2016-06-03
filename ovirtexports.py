from __future__ import print_function

from ovirtvmbackup.ovirtbackup import OvirtBackup
import os
from time import sleep
from progress.spinner import Spinner

virtual_machine = 'Guacamole'

manage = OvirtBackup("https://rhevm.i-t-m.local", 'lperez@itmlabs.local', 'lab2016.')

manage.connect()

count = 0
option = "S"

def validIP(address):
    parts = address.split(".")
    if len(parts) != 4:
        return False
    for item in parts:
        if not 0 <= int(item) <= 255:
            return False
    return True

def validPath(path):
    if os.path.isabs(path):
        return 1
    else:
        return 0

for storage_domain in manage.get_storage_domains(virtual_machine):
    if storage_domain.get_type() == "export":
        count += 1
        print(storage_domain.name)


# if count == 0:
#    while option != "N":
#         option = raw_input("Desea agregar un export Domain S/N: ")
#         if option.upper() != "S" and option.upper() != "N":
#             print("invalid character")
#         elif option.upper() == "S":
#             break
#         else:
#             option = option.upper()
#             exit(1)

dc = manage.get_dc('Guacamole')

# ip_address = raw_input("Ingrese la ip ")

# if validIP(ip_address):
#     print("{} is a valid ip".format(ip_address))
#     share = raw_input("Please enter share path: ")
#     if validPath(share):
#         print("{} is a valid path".format(share))
#         if manage.api.datacenters.get(id=dc.id).storagedomains.add(manage.api.storagedomains.get('LabExport')):
#             print 'Export Domain was attached successfully'
#     else:
#         print("{} is not a valid path".format(share))
# else:
#     print("{} is not a valid ip".format(ip_address))
#     exit(1)

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