from ovirtvmbackup.ovirtbackup import OvirtBackup
import argparse

def main(manager, user, password):
    if manager is None:
        exit(0)
        url = "https://" + manager
    oVirt = OvirtBackup(url, 'lperez@itmlabs.local', 'lab2016.')
#    print("Conectando...")
#    oVirt.connect()
    # oVirt.create_snap('Inicial', 'centos')
    # print("Eliminando snapshot...")
    # oVirt.delete_snap('InstallOK', 'Guacamole')
#    oVirt.get_ovf('Guacamole', 'lab2016')
    print(url)
    print(user)
    print(password)

if __name__ == '__main__':
    main()
