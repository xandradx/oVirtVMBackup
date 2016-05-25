from time import sleep
from ovirtsdk.api import API
from ovirtsdk.xml import params
from ovirtsdk.infrastructure.errors import ConnectionError


def connect(url_rhevm, username, password):
    """Connect to RHEV API
    @param url_rhevm: url_rhevm
    @param username: username
    @param password: password
    """
    try:
        api = API(
                    url=url_rhevm, username=username,
                    password=password, insecure='True')
        return api
    except ConnectionError as err:
        print("Connection failed: %s") % err
        exit(-1)


def create_snap(desc, vm):
    """Create a snapshot from a virtual machine with params:
    @param description: desc
    @param id: vm
    """
    try:
        vm.snapshots.add(params.Snapshot(description=desc, vm=vm))
    except Exception as e:
        print(e.message)
        exit(-1)


def delete_snap(desc, vm):
    """Create a snapshot from a virtual machine with params:
    @param description: desc
    @param id: vm
    """
    try:
        snapshot = vm.snapshots.list(description=desc)[0]
        snapshot.delete()
    except Exception as e:
        print(e.message)
        exit(-1)


def get_snap_id(desc, vm):
    """Return id of Virtual Machine's snapshot
    @param description: desc
    @param id: vm
    """
    try:
        snapshot = vm.snapshots.list(description=desc)[0]
        return snapshot.id
    except Exception as e:
        print(e.message)
        exit(-1)


def wait_snap(vm, id_snap):
    while vm.snapshots.get(id=id_snap).snapshot_status != "ok":
        print("waiting for snapshot to finish...")
        sleep(10)


def wait(api, name, status):
    if status == '0':
        action = "creation"
    elif status == '1':
        action = "export"
    while api.vms.get(name).status.state != 'down':
        print("waiting for vm %s...") % action
        sleep(10)


def create_vm_to_export(vm, id_snap, api, new_name):
    try:
        snapshots = params.Snapshots(snapshot=[params.Snapshot(id=id_snap)])
        cluster = api.clusters.get(id=vm.cluster.id)
        api.vms.add(
            params.VM(
                name=new_name, snapshots=snapshots,
                cluster=cluster, template=api.templates.get(name="Blank")))
    except Exception as e:
        print(e.message)
        exit(-1)


def del_new_vm(new_name, api):
    try:
        api.vms.get(name=new_name).delete()
    except Exception as e:
        print(e.message)
        exit(-1)


def get_export_domain(api, vm):
    cluster = api.clusters.get(id=vm.cluster.id)
    dc = api.datacenters.get(id=cluster.data_center.id)

    export = None

    for sd in dc.storagedomains.list():
        if sd.type_ == "export":
            export = sd
    return export


def export_vm(new_name, api, export):
    try:
        api.vms.get(name=new_name).export(params.Action(storage_domain=export))
    except Exception as e:
        print(e.message)
        exit(1)


def import_vm(name, api, export, cluster, storage_name):
    """Change name of virtual machine to the production name
    @param name: name
    @param api: api
    @param export: export
    @param cluster: cluster
    @param storage_name: storage_name
    """
    try:
        api.storagedomains.get(export).vms.get(name).import_vm(
            params.Action(
                storage_domain=api.storagedomains.get(storage_name),
                cluster=api.clusters.get(name=cluster)))
        print("VM was imported successfully")
        print("Waiting for VM to reach Down status")
        while api.vms.get(name).status.state != 'down':
            sleep(10)
    except Exception as e:
        print("Failed to import VM:\n%s") % str(e)
        exit(-1)


def prod_name(name_vm):
    p_name = name_vm.split('-')
    return p_name[0]


def ch_prod_vm(vm_name, api):
    """Change name of virtual machine to the production name
    @param vm_name: vm_name
    @param api: api
    """
    vm_import = api.vms.get(name=vm_name)
    production_name = prod_name(vm_name)
    vm_import.name = production_name
    vm_import.update()
    vm_prod = api.vms.get(name=production_name)
    vm_prod.start()
    print("Virtual Machine import as %s") % vm_prod.name


def print_info(api, name):
    """Create a snapshot from a virtual machine with params:
    @param name: name
    @param api: api
    """
    count = 0
    vm1 = api.vms.get(name=name)
    print("VM ID: %s") % vm1.id
    for hd in vm1.disks.list():
        print("DISKS: %s %s %s %s") % (count, hd.name, hd.id, hd.size)
        count += 1

if __name__ == '__main__':
    print("This file is intended to be used as a library of functions")
    print(" and it's not expected to be executed directly")
