from __future__ import print_function

import fnmatch
import shutil
from lxml import etree
from progress.spinner import Spinner
from ovirtsdk.api import API
from ovirtsdk.infrastructure.errors import ConnectionError, RequestError
from ovirtsdk.xml import params
from colorama import Fore
import os

from xml.dom import minidom


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
        spinner = Spinner(Fore.YELLOW + "waiting for snapshot to finish... ")
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
            self.api.vms.get(name=new_name).export(params.Action(storage_domain=export, force=True))
            self.__wait(new_name, 1)
        except Exception as e:
            print(e.message)
            exit(1)
            
# Funciones de manejo de Exports Domains

    def get_export_domain(self, vm):
        """Return Export Domain
            :param vm: Virtual Machine Name
        """
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
        try:
            if self.api.datacenters.get(id=dc_id).storagedomains.add(self.api.storagedomains.get(export_ok)):
                print("Export Domain was attached successfully")
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(0)

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

# Seccion de funciones para movimiento de archivos

    def create_dirs(self, vm_name, export_path, images, vms):
        try:
            os.makedirs(export_path + vm_name + vms)
            os.makedirs(export_path + vm_name + images)
        except OSError as e:
            print(e)

    def mv_data(self, new_name, export, source, destination, stid):
            self.dest = export + new_name + destination
            os.chdir(export + stid + destination)
            shutil.move(source, self.dest)

    def do_mv(self, vm, export_path, images, vms):
        obj_vm = self.api.vms.get(vm)
        # disks = self.api.vms.get(new_vm).disks.list()
        storage_id = self.get_export_domain(vm)
        disks = obj_vm.disks.list()
        objects = {"Disks": list(), "Vms": list()}
        objects["Vms"].append(obj_vm.id)

        for disk in disks:
            objects["Disks"].append(disk.id)

        old_name = vm.split("-")[0]

        for disk in objects["Disks"]:
            self.mv_data(old_name, export_path, disk, images, storage_id.id)

        for vm_iter in objects["Vms"]:
            self.mv_data(old_name, export_path, vm_iter, vms, storage_id.id)

# Seccion funciones modificacion del xml

    def get_running_ovf(self, vm, desc, path):
        """Get ovf info from snapshot"""
        try:
            self.snapshot = self.api.vms.get(vm).snapshots.list(
                all_content=True, description=desc)[0]
            self.ovf = self.snapshot.get_initialization().get_configuration().get_data()
            self.root = etree.fromstring(self.ovf)
            complete_path = path + vm
            ovf_path = os.path.join(complete_path, "running-" +  self.api.vms.get(vm).id + '.ovf')
            with open(ovf_path, 'w') as ovfFile:
                ovfFile.write(self.ovf)
            return ovf_path
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(-1)

    def get_vm_export_xml(self, xml_export):
        xml_tag = xml_export.getElementsByTagName("rasd:StorageId")
        storage_ids = list()
        for storage_id in xml_tag:
            storage_ids.append(storage_id.firstChild.nodeValue)
        return storage_ids

    def add_storage_id_xml(self, xml_original, xml_export):
        xml_doc = minidom.parse(xml_original)
        xml_export_obj = minidom.parse(xml_export)

        count = 0

        for item in xml_doc.getElementsByTagName("Device"):
            if item.firstChild.nodeValue == "disk":
                st_id = self.get_vm_export_xml(xml_export_obj)
                StorageId = xml_doc.createElement("rasd:StorageId")
                content = xml_doc.createTextNode(st_id[count])
                StorageId.appendChild(content)
                parent = item.parentNode
                parent.appendChild(StorageId)
                count += 1
        return xml_doc

    def save_new_ovf(self, path, name, xml):
        try:
            dir = os.path.splitext(name)[0]
            os.mkdir(path + dir)
            save_name = path + dir + "/" + name
            print(save_name)
            with open(save_name, 'a') as new_ovf_file:
                new_ovf_file.write(xml.toxml())
        except OSError as e:
            print(e)

    def delete_tmp_ovf(self, path):
        try:
            os.remove(path)
        except OSError as e:
            print(e)

    def export_xml_path(self, path, vm, find_path=None):
        if find_path is not None:
            complete_path = path + vm + find_path
        else:
            complete_path = path + vm
        for root, dirs, filename in os.walk(complete_path):
            for name in filename:
                if fnmatch.fnmatch(name, "*.ovf"):
                    return os.path.join(root, name)

    def change_owner(self, path):
        uid = 36
        gid = 36
        for root, dirs, files in os.walk(path):
            for one_dir in dirs:
                os.chown(os.path.join(root, one_dir), uid, gid)
            for one_file in files:
                os.chown(os.path.join(root, one_file), uid, gid)

if __name__ == '__main__':
    print("This file is intended to be used as a library of functions and it's not expected to be executed directly")
