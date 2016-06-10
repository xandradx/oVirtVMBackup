from ovirtvmbackup.ovirtbackup import OvirtBackup

DC_NAME =       'ITM'
CLUSTER_NAME =  'CProd'
HOST_NAME =     'vmnode01.i-t-m.local'
STORAGE_NAME =  'DS01'
EXPORT_NAME =   'LabExport'
VM_NAME =       'fedora23-test'

ovirt = OvirtBackup('https://rhevm.i-t-m.local/api', 'lperez@itmlabs.local', 'lab2016.')
ovirt.connect()

VM = ovirt.api.vms.get(VM_NAME)
CLUSTER = ovirt.get_cluster(VM_NAME)
DATACENTER = ovirt.get_dc(VM_NAME)

STORAGE_DOMAINS = ovirt.get_storage_domains(VM_NAME)

print("VM id: {} name: {}".format(VM.id, VM.name))
print("CLUSTER id: {} name: {}".format(CLUSTER.id, CLUSTER.name))
print("DATACENTER id: {} name: {}".format(DATACENTER.id, DATACENTER.name))
for st in STORAGE_DOMAINS:
    print("STORAGE id: {} name: {} type: {}".format(st.id, st.name, st.type_))

print(ovirt.api.datacenters.get(id=DATACENTER.id).storagedomains.get(
                EXPORT_NAME).get_status().get_state())