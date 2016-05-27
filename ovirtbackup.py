import cmd
from ovirtsdk.api import API
from ovirtsdk.infrastructure.errors import ConnectionError
from ovirtsdk.xml import params


class OvirtBackup():
    """Class for export and import Virtual Machine in oVirt/RHEV environment"""
    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password

    def print_info(self):
        print self.user
        print self.password

    def connect(self):
        """Connect to oVirt/RHEV API"""
        try:
            self.api = API(url=self.url, username=self.user, password=self.password,
                      insecure='True')
            return self.api
        except ConnectionError as err:
            print("Connection failed: %s") % err
            exit(-1)

    def create_snap(self, desc, vm):
        """Create a snapshot from a virtual machine with params:
        @param description: description of snapshot
        @param id: vm name
        """
        try:
            self.api.vms.get(vm).snapshots.add(params.Snapshot(description=desc, vm=vm))
        except Exception as e:
            print(e.message)
            exit(-1)

if __name__ == '__main__':
    oVirt = OvirtBackup('https://rhevm.xxxx.internal', 'admin@internal', 'P4ssw0rd')
    oVirt.print_info()
    oVirt.connect()
    oVirt.create_snap('Inicial', 'centos')