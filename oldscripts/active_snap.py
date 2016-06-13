from ovirtvmbackup import OvirtBackup

manage = OvirtBackup("https://rhevm.i-t-m.local",
                     "lperez@itmlabs.local", "lab2016.")
manage.connect()

print(manage.api.vms.get("Web01").snapshots.list(
    all_content=True, description="test02")[0].get_initialization())

ovf_vm = manage.api.vms.get(
    all_content=True, name="Web01").get_initialization()\
    .get_configuration().get_data()
active_snap = manage.api.vms.get(all_content=True, name="Web01")\
    .snapshots.list(
        all_content=True, description="test02")[0].get_initialization()\
    .get_configuration().get_data()

print(active_snap)

with open('extracted.ovf', 'w') as ovfFile:
    ovfFile.write(ovf_vm)
