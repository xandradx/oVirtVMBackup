from funciones import print_info, connect

api = connect('https://rhevm-r.itmlabs.local', 'admin@internal', 'S0p0rt3.')
print_info(api, name='vm01-rhel6')
