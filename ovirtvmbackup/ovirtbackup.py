from __future__ import print_function

import fnmatch
import itertools
import os
import re
import shutil
import sys
import time
from xml.dom import minidom
from lxml import etree
from ovirtsdk.api import API
from ovirtsdk.infrastructure.errors import RequestError
from ovirtsdk.xml import params


class OvirtBackup:
    """Class for export and import Virtual Machine in oVirt/RHEV environment"""

    def __init__(self, url, user, password, virtual_machine=None, export_path=None):
        self.url = url
        self.user = user
        self.password = password
        self.virtual = virtual_machine
        self.export_path = export_path

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
            exit(1)

    def vm_state(self, vm):
        return self.api.vms.get(vm).get_status().get_state()

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
            self.api.vms.get(vm).snapshots.add(
                params.Snapshot(
                    description=desc,
                    vm=self.api.vms.get(vm)
                )
            )
            self.snapshot = self.api.vms.get(vm).snapshots.list(description=desc)[0]
            self.__wait_snap(vm, self.snapshot.id)
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(1)

    def snapshot_status(self, vm, snap_id):
        snapshot = self.api.vms.get(vm).snapshots.get(id=snap_id)
        if snapshot:
            return True
        else:
            return False

    def __wait_snap(self, vm, id_snap):
        """ Time wait while create a snapshot of a Virtual Machine"""
        spinner = Spinner()
        print("waiting for snapshot to finish... ")
        while self.api.vms.get(vm).snapshots.get(id=id_snap).snapshot_status != "ok":
            spinner.update()
        spinner.clear()

    def __wait(self, vm, action):
        """Time wait while create and export of a Virtual Machine"""
        if action == 0:
            self.action = "creation"
        elif action == 1:
            self.action = "export"
        spinner = Spinner()
        print("waiting for vm {}... ".format(self.action))
        while self.get_vm_status(vm) != 'down':
            spinner.update()
        spinner.clear()

    def delete_snap(self, desc, vm):
        """Delete a snapshot from a virtual machine with params:
            @param desc: Description of Snapshot
            @param vm: Virtual Machine Name
        """
        try:
            snapshot = self.api.vms.get(vm).snapshots.list(description=desc)[0]
            snapshot.delete()
            spinner = Spinner()
            print("waiting for delete old snapshot... ")
            while self.snapshot_status(vm, snap_id=snapshot.id):
                spinner.update()
            spinner.clear()
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(1)

    def create_vm_to_export(self, vm, new_name, desc):
        try:
            self.snapshot = self.api.vms.get(vm).snapshots.list(description=desc)[0]
            self.snapshots = params.Snapshots(snapshot=[params.Snapshot(id=self.snapshot.id)])
            self.cluster = self.api.clusters.get(id=self.api.vms.get(vm).cluster.id)
            self.api.vms.add(
                params.VM(
                    name=new_name, snapshots=self.snapshots,
                    cluster=self.cluster,
                    template=self.api.templates.get(name="Blank"),
                    delete_protected=False
                )
            )
            self.__wait(new_name, 0)
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(1)

    def get_storage_domains(self, vm):
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
        if self.api.vms.get(vm):
            return 1
        else:
            return 0

    def get_vm_status(self, vm):
        """Verify status of virtual machine"""
        self.state = self.api.vms.get(vm).status.state
        return self.state

    def delete_tmp_vm(self, name):
        try:
            self.api.vms.get(name=name).delete()
            return 1
        except Exception as e:
            print(e.message)
            return 0

    def export_vm(self, new_name, export, collapse):
        try:
            if collapse == 'False':
                self.api.vms.get(name=new_name).export(
                    params.Action(
                        storage_domain=export,
                        force=True
                    )
                )
                self.__wait(new_name, 1)
            elif collapse == 'True':
                self.api.vms.get(name=new_name).export(
                    params.Action(
                        storage_domain=export,
                        force=True,
                        discard_snapshots=True
                    )
                )
                self.__wait(new_name, 1)
        except Exception as e:
            print(e.message)
            exit(1)

    def clean_export_domain(self, name, export):
        snap_name = name + "-SNAP"
        export_vms = list()
        for vm in self.api.storagedomains.get(export).vms.list():
            if (vm.get_name() == name) or (vm.get_name() == snap_name):
                export_vms.append(vm.get_name())

        try:
            for list_vm in export_vms:
                print("Delete exported virtual machine {} from {} ".format(list_vm, export))
                self.api.storagedomains.get(export).vms.get(list_vm).delete()
            return 1
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            return 0

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
        spinner = Spinner()
        print("waiting for maintenance Storage {}... ".format(export))
        while self.api.datacenters.get(id=dc_id).storagedomains.get(
                export).get_status().get_state() != "maintenance":
            spinner.update()
        spinner.clear()

    def attach_export(self, dc_id, export):
        try:
            if self.api.datacenters.get(id=dc_id).storagedomains.add(self.api.storagedomains.get(export)):
                print("Export Domain was attached successfully")
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(0)

    def do_export_up(self, dc_id, export):
        if self.api.datacenters.get(id=dc_id).storagedomains.get(export).activate():
            print('Export Domain was activate successfully')

    def prepare_export(self, dc_id, name_export):
        print("Different Export Attached")
        self.do_export_maintenance(dc_id, name_export)
        self.detach_export(dc_id, name_export)

    def active_export(self, vm, export_name):
        self.export_attached = self.get_export_domain(vm)
        dc = self.get_dc(vm)
        if self.export_attached is not None:
            status_export = self.verify_valid_export(dc.id, export_name, self.export_attached.name)
            if status_export == 1:
                print("Export {} is OK".format(export_name))
            elif status_export == 0:
                self.prepare_export(dc.id, self.export_attached.name)
                self.attach_export(dc.id, export_name)
            elif status_export == 2:
                self.do_export_up(dc.id, export_name)
        elif self.export_attached is None:
            self.attach_export(dc.id, export_name)

        # Seccion de funciones para movimiento de archivos

    def create_dirs(self, vm_name, export_path, images, vms):
        try:
            os.makedirs(export_path + vm_name + vms)
            os.makedirs(export_path + vm_name + images)
        except OSError as e:
            print(e)
            exit(1)

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

        old_name = ''
        if "-" in vm:
            old_name = vm.split("-")[0]
        elif not "-" in vm:
            old_name = vm

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
            ovf_path = os.path.join(complete_path, "running-" + self.api.vms.get(vm).id + '.ovf')
            with open(ovf_path, 'w') as ovfFile:
                ovfFile.write(self.ovf)
            return ovf_path
        except RequestError as err:
            print("Error: {} Reason: {}".format(err.status, err.reason))
            exit(1)

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
            directory = os.path.splitext(name)[0]
            os.mkdir(path + directory)
            save_name = path + directory + "/" + name
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

    def change_dirname(self, path, vm, timestamp):
        try:
            new_dir = os.path.join(path, vm + "-" + timestamp)
            old_dir = os.path.join(path, vm)
            print("change from {} to {}".format(old_dir, new_dir))
            shutil.move(old_dir, new_dir)
        except OSError as e:
            print(e.errno)
            return e.errno

    def log_event(self, vm, msg, severity):
        try:
            vm_obj = self.api.vms.get(vm)
            self.api.events.add(
                params.Event(
                    vm=vm_obj,
                    origin='vm-backup',
                    description=msg,
                    severity=severity,
                    custom_id=int(time.time())
                )
            )
        except:
            pass

    def delete_local_folder(self, path):
        try:
            shutil.rmtree(path)
            return 1
        except OSError as err:
            self.log_event(vm=self.virtual, msg=err, severity='error')
            return 0

    def clean_dir(self, path, vm):
        pattern = vm + '-\d*|' + vm
        try:
            for f in os.listdir(path):
                if re.search(pattern, f):
                    folder = os.path.join(path, f)
                    if os.path.isdir(folder):
                        shutil.rmtree(folder)
                        self.log_event(vm=vm, msg="delete old backup " + folder, severity='info')
            return 1
        except OSError as err:
            self.log_event(vm=self.virtual, msg=err, severity='error')
            return 0

    def verify_path(self, path):
        try:
            if os.path.isdir(path):
                return 1
            else:
                return 0
        except OSError as err:
            return 0

    def verify_environment(self, path, vm, export):
        if self.verify_path(path=path):
            print("Verify exists path {}: [ OK ]".format(path))
            #path_backup = os.path.join(path, vm)
            storage_list = list()
            for storage in self.api.storagedomains.list():
                storage_list.append(storage.name)
            if export in storage_list:
                print("Verify exists export domain {}: [ OK ]".format(export))
                if self.clean_dir(path=path, vm=vm):
                    print("Delete old backup directory for {} if exist's: [ OK ]".format(vm))
                    return 1
                else:
                    print("Delete old backup for {}: [ FAIL ]".format(vm))
                    return 0
            else:
                print("Verify exists export domain {}: [ FAIL ]".format(export))
                return 0
        else:
            print("Verify exists path {}: [ FAIL ]".format(path))
            return 0

# EXPORT'S LOGIC
    def have_export(self, name):
        vm_cluster = self.api.clusters.get(id=self.api.vms.get(name=name).cluster.id)
        vm_datacenter = self.api.datacenters.get(id=vm_cluster.data_center.id)

        for storage in vm_datacenter.storagedomains.list():
            if storage.get_type() == 'export':
                return storage, vm_datacenter
        return None, vm_datacenter

    def status_export(self, export_obj):
        return export_obj.get_status().get_state()


    def find_export(self, export_name):
        attached_dc = None
        for data_center in self.api.datacenters.list():
            for storage in data_center.storagedomains.list():
                if storage.get_name() == export_name:
                    attached_dc = data_center
                    return attached_dc, storage
        if attached_dc is None:
            for storage in self.api.storagedomains.list():
                if storage.get_type() == 'export':
                    if storage.get_name() == export_name:
                        return attached_dc, storage
                    
    def manage_export(self, name, export):
        vm_export, vm_datacenter = self.have_export(name)

        if vm_export is not None:
            print('VM {} have Export "{}"'.format(name, vm_export.get_name()))
            if self.status_export(export_obj=vm_export) == 'active':
                print('State of domain "{}" active'.format(vm_export.get_name()))
                if vm_export.get_name() == export:
                    print('Everything with Exports [ OK ]')
                if vm_export.get_name() != export:
                    print('Domain "{}" is not BK Domain'.format(vm_export.get_name()))
                    print('Export "{}" do maintenance'.format(vm_export.get_name()))
                    self.do_export_maintenance(dc_id=vm_datacenter.id, export=vm_export.get_name())
                    print('Trying to Detach Export "{}" from {}'.format(vm_export.get_name(), vm_datacenter.get_name()))
                    self.detach_export(dc_id=vm_datacenter.id, export=vm_export.get_name())
                    print('Trying to Locate BK Domain "{}"'.format(export))
                    # Buscando export domain Backup
                    data_center, export_backup = self.find_export(export_name=export)
                    if data_center is None:
                        print('Export "{}" is not attached to any datacenter'.format(export))
                        print('Trying to Attach Domain "{}" to {}'.format(export, vm_datacenter.get_name()))
                        self.attach_export(dc_id=vm_datacenter.id, export=export)
                    elif data_center is not None:
                        if self.status_export(export_obj=export_backup) == 'active':
                            print('Export "{}" is attached to datacenter {}'.format(export_backup.get_name(),
                                                                                    data_center.get_name()))
                            print('Export "{}" do maintenance'.format(export_backup.get_name()))
                            self.do_export_maintenance(dc_id=data_center.id, export=export_backup.get_name())
                            print('Trying to Detach Export "{}" from {}'.format(export_backup.get_name(),
                                                                                data_center.get_name()))
                            self.detach_export(dc_id=data_center.id, export=export_backup.get_name())
                            print(
                                'Trying to Attach Domain "{}" to {}'.format(export_backup.get_name(),
                                                                            vm_datacenter.get_name()))
                            self.attach_export(dc_id=vm_datacenter.id, export=export_backup.get_name())
                        if self.status_export(export_obj=export_backup) == 'maintenance':
                            print('State of domain "{}" maintenance'.format(export_backup.get_name()))
                            print('Trying to Detach Export "{}" from {}'.format(export_backup.get_name(),
                                                                                data_center.get_name()))
                            self.detach_export(dc_id=data_center.id, export=export_backup.get_name())
                            print(
                                'Trying to Attach Domain "{}" to {}'.format(export_backup.get_name(),
                                                                            vm_datacenter.get_name()))
                            self.attach_export(dc_id=vm_datacenter.id, export=export_backup.get_name())
            elif self.status_export(export_obj=vm_export) == 'maintenance':
                print('State of domain "{}" maintenance'.format(vm_export.get_name()))
                if vm_export.get_name() == export:
                    print('Trying to activate Export "{}"'.format(export))
                    self.do_export_up(dc_id=vm_datacenter.id, export=vm_export.get_name())
                if vm_export.get_name() != export:
                    print('Domain "{}" is not BK Domain'.format(vm_export.get_name()))
                    print('Trying to Detach Export "{}" from {}'.format(vm_export.get_name(), vm_datacenter.get_name()))
                    self.detach_export(dc_id=vm_datacenter.id, export=vm_export.get_name())
                    print('Trying to Locate BK Domain "{}"'.format(export))

                    # Buscando export domain Backup
                    data_center, export_backup = self.find_export(export_name=export)
                    if data_center is None:
                        print('Export "{}" is not attached to any datacenter'.format(export))
                        print('Trying to Attach Domain "{}" to {}'.format(export, vm_datacenter.get_name()))
                        self.attach_export(dc_id=vm_datacenter.id, export=export)
                    elif data_center is not None:
                        if self.status_export(export_obj=export_backup) == 'active':
                            print('Export "{}" is attached to datacenter {}'.format(export_backup.get_name(),
                                                                                    data_center.get_name()))
                            print('Export "{}" do maintenance'.format(export_backup.get_name()))
                            self.do_export_maintenance(dc_id=data_center.id, export=export_backup.get_name())
                            print('Trying to Detach Export "{}" from {}'.format(export_backup.get_name(),
                                                                                data_center.get_name()))
                            self.detach_export(dc_id=data_center.id, export=export_backup.get_name())
                            print(
                                'Trying to Attach Domain "{}" to {}'.format(export_backup.get_name(),
                                                                            vm_datacenter.get_name()))
                            self.attach_export(dc_id=vm_datacenter.id, export=export_backup.get_name())
                        if self.status_export(export_obj=export_backup) == 'maintenance':
                            print('State of domain "{}" maintenance'.format(export_backup.get_name()))
                            print('Trying to Detach Export "{}" from {}'.format(export_backup.get_name(),
                                                                                data_center.get_name()))
                            self.detach_export(dc_id=data_center.id, export=export_backup.get_name())
                            print(
                                'Trying to Attach Domain "{}" to {}'.format(export_backup.get_name(),
                                                                            vm_datacenter.get_name()))
                            self.attach_export(dc_id=vm_datacenter.id, export=export_backup.get_name())
        elif vm_export is None:
            # Buscando export domain Backup
            data_center, export_backup = self.find_export(export_name=export)
            if data_center is None:
                print('VM {} in datacenter "{}" without Export'.format(name, vm_datacenter.get_name()))
                print('Export "{}" is not attached to any datacenter'.format(export))
                print('Trying to Attach Domain "{}" to {}'.format(export, vm_datacenter.get_name()))
                self.attach_export(dc_id=vm_datacenter.id, export=export)
            elif data_center is not None:
                if self.status_export(export_obj=export_backup) == 'active':
                    print('VM {} in datacenter "{}" without Export'.format(name, vm_datacenter.get_name()))
                    print('Export "{}" is attached to datacenter {}'.format(export_backup.get_name(),
                                                                            data_center.get_name()))
                    print('Export "{}" do maintenance'.format(export_backup.get_name()))
                    self.do_export_maintenance(dc_id=data_center.id, export=export_backup.get_name())
                    print(
                        'Trying to Detach Export "{}" from {}'.format(export_backup.get_name(), data_center.get_name()))
                    self.detach_export(dc_id=data_center.id, export=export_backup.get_name())
                    print(
                        'Trying to Attach Domain "{}" to {}'.format(export_backup.get_name(), vm_datacenter.get_name()))
                    self.attach_export(dc_id=vm_datacenter.id, export=export_backup.get_name())
                if self.status_export(export_obj=export_backup) == 'maintenance':
                    print('VM {} in datacenter "{}" without Export'.format(name, vm_datacenter.get_name()))
                    print(
                        'Trying to Detach Export "{}" from {}'.format(export_backup.get_name(), data_center.get_name()))
                    self.detach_export(dc_id=data_center.id, export=export_backup.get_name())
                    print(
                        'Trying to Attach Domain "{}" to {}'.format(export_backup.get_name(), vm_datacenter.get_name()))
                    self.attach_export(dc_id=vm_datacenter.id, export=export_backup.get_name())


class Spinner:
    """Class for implement Spinner in other process"""

    def __init__(self):
        self.spinner = itertools.cycle(['-', '/', '|', '\\'])

    def update(self):
        """Update the icon for spinner"""
        sys.stdout.write(self.spinner.next())
        sys.stdout.flush()
        sys.stdout.write('\b')
        time.sleep(0.3)

    def clear(self):
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


if __name__ == '__main__':
    print("This file is intended to be used as a library of functions and it's not expected to be executed directly")
