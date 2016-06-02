from ovirtvmbackup.ovirtbackup import OvirtBackup
import os

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

def check_names(infile):
    if os.path.isdir(infile):
        return True
    else:
        return False
for storage_domain in manage.get_storage_domains(virtual_machine):
    if storage_domain.type_ == "export":
        count += 1

if count:
    print(storage_domain.name)
else:
    while option != "N":
        option = raw_input("Desea agregar un export Domain S/N: ")
        if option.upper() != "S" and option.upper() != "N":
            print("invalid character")
        elif option.upper() == "S":
            break
        else:
            option = option.upper()
            exit(0)

ip_address = raw_input("Ingrese la ip ")

if validIP(ip_address):
    print("{} is a valid ip".format(ip_address))
    share = raw_input("Please enter share path: ")
    if check_names(share):
        print("{} is a valid path".format(share))
    else:
        print("{} is not a valid path".format(share))
else:
    print("{} is not a valid ip".format(ip_address))