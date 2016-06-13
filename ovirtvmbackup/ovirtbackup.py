from __future__ import print_function

from lxml import etree
from progress.spinner import Spinner
from ovirtsdk.api import API
from ovirtsdk.infrastructure.errors import ConnectionError, RequestError
from ovirtsdk.xml import params
from colorama import Fore


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
            snapshot = self.snapshot = self.api.vms.get(vm).snapshots.list()
            for snap in snapshot:
                if snap.description == desc:
                    self.delete_snap(desc=desc, vm=vm)

            self.api.vms.get(vm).snapshots.add(params.Snapshot(description=desc, vm=self.api.vms.get(vm)))
            self.snapshot = self.api.vms.get(vm).snapshots.list(description=desc)[0]
            self.__wait_snap(vm, self.snapshot.id)
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(-1)

    def snapshot_status(self, vm, snap_id):
        snapshot = self.api.vms.get(vm).snapshots.get(id=snap_id)
        if snapshot:
            return True
        else:
            return False

    def __wait_snap(self, vm, id_snap):
        """ Time wait while create a snapshot of a Virtual Machine"""
        spinner = Spinner(Fore.YELLOW + "\nwaiting for snapshot to finish... ")
        while self.api.vms.get(vm).snapshots.get(id=id_snap).snapshot_status != "ok":
            spinner.next()

    def __wait(self, vm, action):
        """Time wait while create and export of a Virtual Machine"""
        if action == 0:
            self.action = "creation"
        elif action == 1:
            self.action = "export"
        spinner = Spinner(Fore.YELLOW + "waiting for vm {}... ".format(self.action))
        while self.get_vm_status(vm) != 'down':
            spinner.next()

    def delete_snap(self, desc, vm):
        """Delete a snapshot from a virtual machine with params:
            @param desc: Description of Snapshot
            @param vm: Virtual Machine Name
        """
        try:
            snapshot = self.api.vms.get(vm).snapshots.list(description=desc)[0]
            snapshot.delete()
            spinner = Spinner(Fore.RED + "waiting for delete snapshot... ")
            while self.snapshot_status(vm, snap_id=snapshot.id):
                spinner.next()
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(-1)

    def save_ovf(self, vm, desc):
        """Get ovf info from snapshot"""
        try:
            self.snapshot = self.api.vms.get(vm).snapshots.list(
                all_content=True, description=desc)[0]
            self.ovf = self.snapshot.get_initialization().get_configuration().get_data()
            self.root = etree.fromstring(self.ovf)

            with open(self.api.vms.get(vm).id + '.ovf', 'w') as ovfFile:
                ovfFile.write(self.ovf)
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(-1)

    def create_vm_to_export(self, vm, new_name, desc):
        try:
            self.snapshot = self.api.vms.get(vm).snapshots.list(description=desc)[0]
            self.snapshots = params.Snapshots(snapshot=[params.Snapshot(id=self.snapshot.id)])
            self.cluster = self.api.clusters.get(id=self.api.vms.get(vm).cluster.id)
            self.api.vms.add(
                params.VM(
                    name=new_name, snapshots=self.snapshots,
                    cluster=self.cluster, template=self.api.templates.get(name="Blank")))
            self.__wait(new_name, 0)
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(0)

    def get_storage_domains(self,vm):
        self.datacenter = self.get_dc(vm)
        return self.datacenter.storagedomains.list()

    def get_dc(self, vm):
        """Return Datacenter object
            :param vm: Virtual Machine Name
        """
        self.dc = self.api.datacenters.get(id=self.get_cluster(vm).data_center.id)
        return self.dc

    def get_cluster(self, vm):
        """Return Cluster object
            :param vm: Virtual Machine Name
        """
        self.cluster = self.api.clusters.get(id=self.api.vms.get(vm).cluster.id)
        return self.cluster

    def if_exists_vm(self, vm):
        """Verify if virtual machine and new virtual machine already exists"""
        if (self.api.vms.get(vm)):
            return 1
        else:
            return 0

    def get_vm_status(self, vm):
        """Verify status of virtual machine"""
        self.state = self.api.vms.get(vm).status.state
        return self.state

    def delete_tmp_vm(self,new_name):
        try:
            self.api.vms.get(name=new_name).delete()
        except Exception as e:
            print(e.message)
            exit(-1)

    def export_vm(self, new_name, export):
        try:
            self.api.vms.get(name=new_name).export(params.Action(storage_domain=export))
            self.__wait(new_name, 1)
        except Exception as e:
            print(e.message)
            exit(1)
            
# Funciones de manejo de Exports Domains

    def get_export_domain(self, vm):
        """Return Export Domain
            :param vm: Virtual Machine Name
        """
        # self.cluster = self.api.clusters.get(id=self.api.vms.get(vm).cluster.id)
        # self.dc = self.api.datacenters.get(id=self.cluster.data_center.id)
        self.cluster = self.get_cluster(vm)
        self.dc = self.get_dc(vm)

        self.export = None

        for self.sd in self.dc.storagedomains.list():
            if self.sd.get_type() == "export":
                self.export = self.sd
        return self.export

    def verify_valid_export(self, dc_id, export, current):
        if current == export:
            if self.api.datacenters.get(id=dc_id).storagedomains.get(
                    export).get_status().get_state() == "active":
                return 1
            else:
                return 2
        elif current != export:
            return 0

    def detach_export(self, dc_id, export):
        if self.api.datacenters.get(id=dc_id).storagedomains.get(export).delete():
            print("Detach OK")

    def do_export_maintenance(self, dc_id, export):
        self.api.datacenters.get(id=dc_id).storagedomains.get(export).deactivate()
        spinner = Spinner("waiting for maintenance Storage... ")
        while self.api.datacenters.get(id=dc_id).storagedomains.get(
                export).get_status().get_state() != "maintenance":
            spinner.next()

    def attach_export(self, dc_id, export_ok):
        if self.api.datacenters.get(id=dc_id).storagedomains.add(self.api.storagedomains.get(export_ok)):
            print("Export Domain was attached successfully")

    def do_export_up(self, dc_id, export):
        if self.api.datacenters.get(id=dc_id).storagedomains.get(export).activate():
            print('Export Domain was activate successfully')

    def prepare_export(self, dc_id, vm, name_export):
        print("Different Export Attached")
        self.do_export_maintenance(dc_id, name_export)
        self.detach_export(dc_id, name_export)

    def active_export(self, vm, export_name):
        export_attached = self.get_export_domain(vm)
        dc = self.get_dc(vm)
        if export_attached is not None:
            status_export = self.verify_valid_export(dc.id, export_name, export_attached.name)
            if status_export == 1:
                print("Export {} is OK".format(export_name))
            elif status_export == 0:
                self.prepare_export(dc.id, vm, export_attached.name)
                self.attach_export(dc.id, export_name)
            elif status_export == 2:
                self.do_export_up(dc.id, export_name)
        elif export_attached is None:
            self.attach_export(dc.id, export_name)


if __name__ == '__main__':
    print("This file is intended to be used as a library of functions and it's not expected to be executed directly")
