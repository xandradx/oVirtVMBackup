from ovirtvmbackup.ovirtbackup import OvirtBackup

oVirt = OvirtBackup('https://rhevm.i-t-m.local', 'lperez@itmlabs.local', 'lab2016.')
print("Conectando...")
oVirt.connect()
#oVirt.create_snap('Inicial', 'centos')
#print("Eliminando snapshot...")
#oVirt.delete_snap('InstallOK', 'Guacamole')
oVirt.get_ovf('Guacamole', 'lab2016')