from ovirtvmbackup import OvirtBackup
from colorama import init, Fore
import argparse
from time import sleep

init(autoreset=True)

path_export = "/exportdomain/"
vms_path = "/master/vms/"
images_path = "/images/"

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
    print(Fore.GREEN + "Export virtual machine {}".format(vm_name))

    if (conn.if_exists_vm(vm=vm_name)):
        if (conn.if_exists_vm(vm=new_name)):
            print(Fore.RED + "Virtual Machine {} Backup already exists".format(new_name))
        else:
            print(Fore.YELLOW + "creating snapshot")
            conn.create_snap(desc=description, vm=vm_name)
            print(Fore.GREEN + "\ncreate snapshot successful")
            print(Fore.YELLOW + "creating new virtual machine {}".format(new_name))
            conn.create_vm_to_export(vm=vm_name, new_name=new_name, desc=description)
            print(Fore.GREEN + "\ncreate virtual machine {} successful".format(new_name))
            print(Fore.YELLOW + "Activating Export Domain {}".format(export_domain))
            conn.active_export(vm=vm_name, export_name=export_domain)
            print(Fore.GREEN + "Export domain {} successful activated".format(export_domain))
            print(Fore.YELLOW + "Export Virtual Machine {}".format(new_name))
            export_dom = conn.get_export_domain(vm=vm_name)
            conn.export_vm(new_name, export_dom)
            print(Fore.GREEN + "Export Virtual Machine {} successful".format(export_domain))
            print(Fore.YELLOW + "Moving export to another location")


            print(Fore.GREEN + "process finished successful")
    else:
        print(Fore.RED + "Virtual Machine {} doesn't exists".format(vm_name))

def vm_import(name):
    print("Import virtual machine {}".format(name))
    pass


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
            print(Fore.GREEN + "auth OK")
        if (is_import):
            vm_import(name)
        elif (is_export):
            export(oVirt, name, new_name, description, export_domain)

if __name__ == '__main__':
    main()
