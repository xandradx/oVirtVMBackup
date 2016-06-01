from ovirtvmbackup.ovirtbackup import OvirtBackup

ovirt = OvirtBackup('https://rhevm.i-t-m.local', 'lperez@itmlabs.local', 'lab2016.')
ovirt.connect()

print(ovirt.get_vm_status('db01'))
