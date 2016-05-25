from funciones import print_info, connect

api = connect('https://url-to-ovirt-manager', 'admin@internal', 'P4ssw0rd')
print_info(api, name='vm01')
