from funciones import *
import argparse


def main():
    """Principal Program"""
    # Options #
    parser = argparse.ArgumentParser(
        description='Automatic export virtual machine RHEV',
        prog='export_vm', usage='%(prog)s [options]')
    parser.add_argument('-m', '--manager', metavar='rhevm.i-t-m.local',
                        help='FQDN Manager RHEV', required=True)
    parser.add_argument('-n', '--name', metavar='VM01',
                        help='Name of virtual machine', required=True)
    parser.add_argument('-u', '--user', metavar='admin@internal',
                        help='username with admin privileges DEFAULT=admin',
                        default='admin@internal')
    parser.add_argument('-p', '--password', metavar='p4ssw0rd',
                        help='password for the user', required=True)
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 0.1')
    args = parser.parse_args()
    # Mandatory Params #
    server = args.manager
    name = args.name
    username = args.user
    password = args.password
    rhevm_url = "https://%s" % (server)

    api = connect(rhevm_url, username, password)
    vm = api.vms.get(name)

    export = get_export_domain(api, vm)
    export_vm(name, api, export)
    wait(api, name, '1')
    print("Export Virtual Machine as %s Finished...") % name
    print_info(api, name)
    del_new_vm(name, api)
    print("Delete Temporal Virtual Machine %s ") % name

    api.disconnect()
    exit(0)


if __name__ == '__main__':
    main()
