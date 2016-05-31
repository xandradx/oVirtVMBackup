from __future__ import print_function

from lxml import etree
from time import sleep

from ovirtsdk.api import API
from ovirtsdk.infrastructure.errors import ConnectionError, RequestError
from ovirtsdk.xml import params


class OvirtBackup():
    """Class for export and import Virtual Machine in oVirt/RHEV environment"""
    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password

    def print_info(self):
        print(self.url)
        print(self.user)
        print(self.password)

    def connect(self):
        """Connect to oVirt/RHEV API"""
        try:
            self.api = API(url=self.url, username=self.user,
                           password=self.password, insecure='True')
            return self.api
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(0)

    def create_snap(self, desc, vm):
        """Create a snapshot from a virtual machine with params:
            @param desc: Description of Snapshot
            @param vm: Virtual Machine Name
        """
        try:
            self.api.vms.get(vm).snapshots.add(params.Snapshot(description=desc, vm=self.api.vms.get(vm)))
            self.snapshot = self.api.vms.get(vm).snapshots.list(description=desc)[0]
            self.__wait_snap(vm, self.snapshot.id)
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(-1)

    def __wait_snap(self, vm, id_snap):
        """ Time wait while delete spanshot of a Virtual Machine"""
        while self.api.vms.get(vm).snapshots.get(id=id_snap).snapshot_status != "ok":
            print("waiting for snapshot to finish...")
            sleep(10)


    def __wait(self, vm, status):
        """Time wait while create and export of a Virtual Machine"""
        if status == '0':
            action = "creation"
        elif status == '1':
            action = "export"
        while self.api.vms.get(vm).status.state != 'down':
            print("waiting for vm %s...") % action
            sleep(10)

    def delete_snap(self, desc, vm):
        """Delete a snapshot from a virtual machine with params:
            @param desc: Description of Snapshot
            @param vm: Virtual Machine Name
        """
        try:
            self.snapshot = self.api.vms.get(vm).snapshots.list(description=desc)[0]
            self.snapshot.delete()
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(-1)

    def get_ovf(self, vm, desc):
        """Get ovf info from snapshot"""
        try:
            self.snapshot = self.api.vms.get(vm).snapshots.list(
                all_content=True, description=desc)[0]
            self.ovf = self.snapshot.get_initialization().get_configuration().get_data()
            self.root = etree.fromstring(self.ovf)
            with open(vm + '.ovf', 'w') as ovfFile, open( vm + ".xml", 'w') as xmlFile:
                ovfFile.write(self.ovf)
                xmlFile.write(etree.tostring(self.root, pretty_print=True))
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(-1)

    def create_vm_to_export(vm, id_snap, api, new_name):
        try:
            snapshots = params.Snapshots(snapshot=[params.Snapshot(id=id_snap)])
            cluster = api.clusters.get(id=vm.cluster.id)
            api.vms.add(
                params.VM(
                    name=new_name, snapshots=snapshots,
                    cluster=cluster, template=api.templates.get(name="Blank")))
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(-1)

    def get_export_domain(self, vm):
        """Create a snapshot from a virtual machine with params:
            @param vm: Virtual Machine Name
        """
        self.cluster = self.api.clusters.get(id=self.api.vms.get(vm).cluster.id)
        self.dc = self.api.datacenters.get(id=self.cluster.data_center.id)

        self.export = None

        for self.sd in self.dc.storagedomains.list():
            if self.sd.type_ == "export":
                self.export = self.sd
        return self.export

    def if_exists_vm(self, vm):
        """Verify if virtual machine and new virtual machine already exists"""
        if (self.api.vms.get(vm)):
            return 1
        else:
            return 0


if __name__ == '__main__':
    print("This file is intended to be used as a library of functions and it's not expected to be executed directly")
