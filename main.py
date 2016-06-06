from ovirtvmbackup import OvirtBackup
from colorama import init, Fore
import argparse
from time import sleep

init(autoreset=True)

def get_args():
    '''Function parses and return arguments passed in'''

    parser = argparse.ArgumentParser(
        description='Automatic export/import virtual machine RHEV',
        prog='ovirtbackup')

    parser.add_argument('-v', '--version',
                        action='version', version='%(prog)s 0.3')
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
    requiredNamed.add_argument('--export-domain', metavar="EXPORT", dest="export_name",
                               help='Export Domain Name', required=True)

    args = parser.parse_args()

    return args.imp, args.export, args.vmname, args.manager, args.username, args.password, args.export_name


def export(conn, vm_name, new_name, description, export_domain):
    print(Fore.LIGHTGREEN_EX + "Export virtual machine {}".format(vm_name))

    if (conn.if_exists_vm(vm_name)):
        if (conn.if_exists_vm(new_name)):
            print(Fore.RED + "Virtual Machine {} Backup already exists".format(new_name))
        else:
            print(Fore.YELLOW + "creating snapshot")
            conn.create_snap(description, vm_name)
            print(Fore.LIGHTGREEN_EX + "\ncreate snapshot successful")
            print(Fore.YELLOW + "creating new virtual machine {}".format(new_name))
            conn.create_vm_to_export(vm_name, new_name, description)
            print(Fore.LIGHTGREEN_EX + "\ncreate virtual machine {} successful".format(new_name))

            print(Fore.YELLOW + "Starting Export for Virtual Machine {}".format(new_name))
            export_dom = conn.get_export_domain(vm_name)
            if verify_export_domain(export_domain, export_dom.name):
                conn.export_vm(new_name, export_dom)
                conn.save_ovf(vm_name, description)
                print(Fore.YELLOW + "delete snapshot {}".format(description))
                conn.delete_snap(description, vm_name)
            else:
                print(Fore.RED + "Export domain {} doesnt exists".format(export_domain))
                exit(1)

            print(Fore.YELLOW + "\ndelete virtual machine {}".format(new_name))
            conn.delete_tmp_vm(new_name)
            print(Fore.LIGHTGREEN_EX + "process finished successful")
    else:
        print(Fore.RED + "Virtual Machine {} doesn't exists".format(vm_name))

def vm_import(name):
    print("Import virtual machine {}".format(name))
    pass

def verify_export_domain(name, extract_domain):
    if extract_domain == name:
        return 1
    else:
        return 0

def main():
    is_import, is_export, name, manager, user, password , export_domain = get_args()
    new_name = name + "-snap"
    description = "oVirtBackup"
    url = "https://" + manager
    if (is_import is not True) and (is_export is not True):
        print(Fore.RED + "Export/Import option is necesary")
        exit(1)
    if (is_import) and (is_export):
        print(Fore.RED + "Export or Import NOT must be combined")
        exit(1)
    else:
        oVirt = OvirtBackup(url, user, password)
        print(Fore.YELLOW + "trying auth...")
        if (oVirt.connect()):
            print(Fore.LIGHTGREEN_EX + "auth OK")
        if (is_import):
            vm_import(name)
        elif (is_export):
            export(oVirt, name, new_name, description, export_domain)

if __name__ == '__main__':
    main()
