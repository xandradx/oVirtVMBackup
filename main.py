from ovirtvmbackup.ovirtbackup import OvirtBackup
from colorama import init, Fore
import argparse

init(autoreset=True)

def get_args():
    '''Function parses and return arguments passed in'''

    parser = argparse.ArgumentParser(
        description='Automatic export/import virtual machine RHEV',
        prog='ovirtbackup')

    parser.add_argument('-v', '--version',
                        action='version', version='%(prog)s 0.2')
    parser.add_argument('--import', action="store_true", dest="imp",
                        help="import virtual machine")
    parser.add_argument('--export', help="export virtual machine",
                        action="store_true")
    parser.add_argument('vmname')
    requiredNamed = parser.add_argument_group("required named arguments")
    requiredNamed.add_argument('--manager', help='FQDN manager oVirt/RHEV',
                               required=True)
    requiredNamed.add_argument('--username', help='username with admin privileges',
                               default='admin@internal')
    requiredNamed.add_argument('--password', help='password for the user',
                               required=True)

    args = parser.parse_args()

    import_vm = args.imp
    export = args.export
    vm_name = args.vmname
    manager = args.manager
    user = args.username
    password = args.password
    return import_vm, export, vm_name, manager, user, password

def export(url, user, password, name, new_name, description):
    print("Export virtual machine {}".format(name))

    oVirt = OvirtBackup(url, user, password)
    print("trying auth...")
    if (oVirt.connect()):
        print(Fore.GREEN + "auth OK")
    if (oVirt.if_exists_vm(name)):
        if (oVirt.if_exists_vm(new_name)):
            print(Fore.RED + "Virtual Machine {} Backup already exists".format(new_name))
        else:
            print(Fore.YELLOW + "creating snapshot")
            oVirt.create_snap(description, name)
            print(Fore.GREEN + "\ncreate snapshot successful")
            print(Fore.YELLOW + "creating new virtual machine {}".format(new_name))
            oVirt.create_vm_to_export(name, new_name, description)
            print(Fore.GREEN + "\ncreate virtual machine {} successful".format(new_name))
            print(Fore.YELLOW + "delete snapshot {}".format(description))
            oVirt.delete_snap(description, name)
            print(Fore.GREEN + "\ndelete snapshot {} successful".format(new_name))

    else:
        print(Fore.RED + "Virtual Machine {} doesn't exists".format(name))

def vm_import(name):
    print("Import virtual machine {}".format(name))
    pass

def main():
    is_import, is_export, name, manager, user, password = get_args()
    new_name = name + "-snap"
    description = "oVirtBackup"
    url = "https://" + manager
    if (is_import is not True) and (is_export is not True):
        print(Fore.RED + "Export/Import option is necesary")
        exit(1)
    if (is_import) and (is_export):
        print(Fore.RED + "Export or Import NOT must be combined")
        exit(1)
    elif (is_import):
        vm_import(name)
    elif (is_export):
        export(url, user, password, name, new_name, description)

if __name__ == '__main__':
    main()
