# OvirtVMBackup
Scripts for backup VM with Ovirt API

Procedure

1. Generate Snapshot to a VM
2. Clone VM from snapshot
3. Validate export domain for backups
4. Export VM
5. Move export VM to another location ( for integrate with third party software backup )
6. Generate xml from running VM snapshot
7. Modify xml to add storageId and Disks from clone VM ovf
8. Finish Backup

##### What is this repository for? #####

* Script for Backup VM in RHEV/Ovirt
* Version 0.1

&copy; Luis Armando Perez Marin   
<luis.luimarin@gmail.com>   
<lperez@i-t-m.com>


