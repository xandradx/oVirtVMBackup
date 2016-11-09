#!/usr/bin/python

import os

import datetime

from ovirtvmbackup import OvirtBackup, rename_clone
import sys
import ConfigParser
import subprocess
import time
import shutil

config_file='/etc/ovirt-vm-backup/ovirt-vm-backup.conf'
vms_path = "/master/vms/"
images_path = "/images/"

def log_tsm(vmname,tsmuser,tsmpass,message,level):
    if level == 'normal':
        level = 'I'
    if level == 'error':
        level = 'E'
    try:    
        subprocess.check_output(['sudo','/usr/bin/dsmadmc', '-id='+tsmuser, '-pa='+tsmpass, 'issue message '+level+' "'+message+' ('+vmname+')"','cwd=/tmp/'])
    except:
        pass


def log_all(conn,vmname,message,level):
    general = load_config(config_file)
    conn.log_event(vmname,message+' ('+vmname+')',level)
    date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = open(general['log_file'],'a')
    log_file.write(date+' '+message+' ('+vmname+') ['+level+']\n')
    log_file.close()
    print(message+' ('+vmname+') ')
    log_tsm(vmname,general['tsm_user'],general['tsm_pass'],message,level)

def export(conn, vm_name, new_name, description, export_domain):
    print("Export virtual machine {}".format(vm_name))

    if (conn.if_exists_vm(vm=vm_name)):
        status = conn.vm_state(vm=vm_name)
        print("Preparing Export Domain {}".format(export_domain))
        conn.manage_export(name=vm_name, export=export_domain)
        print("Cleaning Export Domain {} from previous restore's".format(export_domain))
        if conn.clean_export_domain(name=vm_name, export=export_domain):
            print("All checks: [ OK ]")
        else:
            print("Fail in clean exportdomain {}".format(export_domain))
            raise Exception(8)
        print("Export domain {} successful activated".format(export_domain))
        if (conn.if_exists_vm(vm=new_name)):
            print("Virtual Machine {} Backup already exists".format(new_name))
            print("Trying to delete Virtual Machine {}".format(new_name))
            if not conn.delete_tmp_vm(name=new_name):
                log_all(conn,vm_name,
                               'Delete Backup VM \'' + vm_name + '\' Failed, ' + new_name + ' already exist, you must delete \'' + new_name + '\' manually',
                               'error')
                raise Exception(9)
            else:
                print("Delete Virtual Machine {} [ OK ]".format(new_name))
        if status == 'up':
            log_all(conn,vm_name,'Backup Process for VM \''+vm_name+'\' state '+status+' has started','normal')
            log_all(conn,vm_name,"creating snapshot",'normal')
            try:
                conn.create_snap(desc=description, vm=vm_name)
                log_all(conn,vm_name,"create snapshot successful",'normal')
            except Exception as exit_code:
                log_all(conn,vm_name,"create snapshot failed ",'error')
                log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' Failed [exit-code:'+str(exit_code.args[0])+']','error')
                exit(exit_code)
            log_all(conn,vm_name,"creating new virtual machine {}".format(new_name),'normal')
            try:
                conn.create_vm_to_export(vm=vm_name, new_name=new_name, desc=description)
                log_all(conn,vm_name,"create virtual machine {} successful".format(new_name),'normal')
            except Exception as exit_code:
                log_all(conn,vm_name,"create virtual machine failed ",'error')
                log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' Failed [exit-code:'+str(exit_code.args[0])+']','error')
                exit(exit_code)
            log_all(conn,vm_name,"Export Virtual Machine {}".format(new_name),'normal')
            try:
                export_dom = conn.get_export_domain(vm=vm_name)
                conn.export_vm(new_name, export_dom, 'False')
                log_all(conn,vm_name,"Export Virtual Machine {} successful".format(export_domain),'normal')
            except Exception as exit_code:
                log_all(conn,vm_name,"Export Virtual Machine failed ",'error')
                log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' Failed [exit-code:'+str(exit_code.args[0])+']','error')
                exit(exit_code)
            print("Moving export to another location")
            log_all(conn,vm_name,'Backup VM preparing \''+vm_name+'\' for storage','normal')
            try:
                conn.create_dirs(vm_name=vm_name, export_path=path_export, images=images_path, vms=vms_path)
                conn.do_mv(vm=new_name, export_path=path_export, images=images_path, vms=vms_path)
            except Exception as exit_code:
                log_all(conn,vm_name,"Backup VM preparing failed ",'error')
                log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' Failed [exit-code:'+str(exit_code.args[0])+']','error')
                exit(exit_code)
            # trabajado con ovf's
            log_all(conn,vm_name,'Backup VM keeping \''+vm_name+'\' original configuration','normal')
            print("Change id's and paths")
            try:
                conn.get_running_ovf(vm=vm_name, desc=description, path=path_export)
                export_xml = conn.export_xml_path(path=path_export, vm=vm_name, find_path=vms_path)
                original_xml = conn.export_xml_path(path=path_export, vm=vm_name)
                xml_obj = conn.add_storage_id_xml(original_xml, export_xml)
                ovf_final = os.path.basename(original_xml)[8:]
                vms_path_save = path_export + vm_name + vms_path
                conn.save_new_ovf(path=vms_path_save, name=ovf_final, xml=xml_obj)
                conn.delete_tmp_ovf(path=path_export + vm_name + "/running-" + ovf_final)
                log_all(conn,vm_name,"Backup VM keep original configuration successful",'normal')
                rename_clone(export_xml, vms_path_save + conn.api.vms.get(vm_name).id + "/" + ovf_final, path_export + vm_name + images_path)
                print("Move successful")
            except Exception as exit_code:
                log_all(conn,vm_name,"Backup VM preparing failed ",'error')
                log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' Failed [exit-code:'+str(exit_code.args[0])+']','error')
                exit(exit_code)
            log_all(conn,vm_name,"Remove temporary snap and Virtual Machine",'normal')
            try:
                # Eliminando snapshot y {vm}-snap
                conn.delete_tmp_vm(name=new_name)
                log_all(conn,vm_name,"Remove temporary Virtual Machine sucessfull",'normal')
            except Exception as exit_code:
                log_all(conn,vm_name,"Remove temporary Virtual Machine failed",'failed')
                log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' Failed [exit-code:'+str(exit_code.args[0])+']','error')
                exit(exit_code)
            try:
                conn.delete_snap(vm=vm_name, desc=description)
                log_all(conn,vm_name,"Remove temporary snapshot sucessfull",'normal')
            except Exception as exit_code:
                log_all(conn,vm_name,"Remove temporary snapshot failed",'failed')
                log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' Failed [exit-code:'+str(exit_code.args[0])+']','error')
                exit(exit_code)
            #print("process finished successful")
            try:
                conn.change_dirname(path=path_export, vm=vm_name, timestamp=timestamp)
                log_all(conn,vm_name,'Backup VM \''+vm_name+'\' ready for storage','normal')
            except Exception as exit_code:
                log_all(conn,vm_name,'Backup VM \''+vm_name+'\' NOT ready for storage','failed')
                log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' Failed [exit-code:'+str(exit_code.args[0])+']','error')
                exit(exit_code)
        elif status == 'down':
            log_all(conn,vm_name,'Backup Process for VM \''+vm_name+'\' state '+status+' has started','normal')
            print("Virtual Machine {} is down".format(vm_name))
            log_all(conn,vm_name,"Export Virtual Machine {}".format(vm_name),'normal')
            try:
                export_dom = conn.get_export_domain(vm=vm_name)
                conn.export_vm(vm_name, export_dom, 'True')
                log_all(conn,vm_name,"Export Virtual Machine {} successful".format(vm_name),'normal')
            except Exception as exit_code:
                log_all(conn,vm_name,'Export Virtual Machine \''+vm_name+'\' failed','failed')
                log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' Failed [exit-code:'+str(exit_code.args[0])+']','error')
                exit(14)
            print("Moving export to another location")
            log_all(conn,vm_name,'Backup VM preparing \''+vm_name+'\' for storage','normal')
            try:
                conn.create_dirs(vm_name=vm_name, export_path=path_export, images=images_path, vms=vms_path)
                conn.do_mv(vm=vm_name, export_path=path_export, images=images_path, vms=vms_path)
                print("Move successful")
                conn.change_dirname(path=path_export, vm=vm_name, timestamp=timestamp)
                print("process for backup finished successful")
                log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' ready for storage', 'normal')
            except Exception as exit_code:
                log_all(conn,vm_name,'Backup VM \''+vm_name+'\' NOT ready for storage','failed')
                log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' Failed [exit-code:'+str(exit_code.args[0])+']','error')
                exit(exit_code)
        else:
            print("Virtual Machine {} status is {}".format(vm_name, status))
            log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' invalid status '+status, 'error')
            log_all(conn,vm_name, 'Backup VM \'' + vm_name + '\' Failed [exit-code:10]','error')
            exit(10)
            
    else:
        print("Virtual Machine {} doesn't exists".format(vm_name))
        exit(11)

def vm_import(name):
    print("Import virtual machine {}".format(name))
    pass

def du(path):
  return subprocess.check_output(['du','-sh', path]).split()[0].decode('utf-8')

def load_config(path):
    config = ConfigParser.ConfigParser()
    config.read(path)
    return dict(config.items("general"))

def change_meta(path):
    for image in os.listdir(path):
        image_id=image
        for file in os.listdir(path+'/'+image_id):
            if file.endswith(".meta"):
                subprocess.call(['sed','-i','s/^IMAGE=.*/IMAGE='+image_id+'/g',path+image_id+'/'+file])    

def upload_tsm(path,vmname):
    date=datetime.datetime.now().strftime("%Y/%m/%d")
    #date=time.strftime("%m/%d/%y", time.gmtime())
    output=[]
    command=subprocess.check_output(['sudo','dsmc','archive',path+'/','-subdir=yes','-description=\'VMDate: '+date+' VMName:'+vmname+'\''],cwd='/tmp') 
    for line in command.split('\n'):
        output.append(line)
    fi=output[len(output)-16].split(':',2)[1].replace(" ","")
    fa=output[len(output)-15].split(':',2)[1].replace(" ","")
    bi=output[len(output)-8].split(':',2)[1].replace(" ","")
    ba=output[len(output)-9].split(':',2)[1].replace(" ","")
    message=("Files: %s/%s Size: %s/%s") % (fa,fi,ba,bi)
    return message

def remove_temp(path):
    shutil.rmtree(path)

def usage():
    print("Usage: {} VMNAME".format(sys.argv[0]))
    sys.exit(1)

    

def main():
    if (len(sys.argv) > 1):
        if not (os.path.isfile(config_file)):
            print("No configuration file found")
            sys.exit(2)
        for vmname in sys.argv[1:]:
            print("Backup for vm {}".format(vmname))
            general = load_config(config_file)
            global path_export
            global dsmc
            global timestamp
            path_export = general['exportpath']
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
            dsmc = general['dsmc']

            new_name = vmname + '-SNAP'
            description = "oVirtBackup"
            url = "https://" + general['manager']
            print(description)
            is_export = True
            oVirt = OvirtBackup(url, general['api_user'], general['api_pass'])
            print("Trying auth...")
            oVirt.connect()
            try:
                print("Auth [ OK ]")
                if oVirt.verify_environment(path=path_export, vm=vmname, export=general['export']):
                    export(
                        conn=oVirt, vm_name=vmname, new_name=new_name,
                        description=description, export_domain=general['export']
                    )
                else:
                    exit(3)
            except Exception as exit_code:
                if (oVirt.if_exists_vm(vm=vmname)):
                    log_all(oVirt, vmname,
                            "Backup VM '" + vmname + "' Failed [exit-code:" + str(exit_code.args[0]) + "]", "error")
                exit(exit_code)
            try:
                log_all(oVirt,vmname, "Preparing VM " + vmname + " for TSM Backup", "normal")
                change_meta(path_export + vmname + "-" + timestamp + images_path)
            except:
                log_all(oVirt,vmname, "Preparing VM " + vmname + " for TSM Backup Failed", "error")
                exit(5)
            try:
                print("Uploading VM {} to TSM".format(vmname))
                log_all(oVirt,vmname, 'Uploading VM ' + vmname + ' to TSM as '+ vmname + '-' + timestamp, 'normal')
                command = upload_tsm(path_export + vmname + "-" + timestamp, vmname)
                log_all(oVirt,vmname, 'Uploading VM ' + vmname + ' to TSM has been completed ' + command + '.',
                                'normal')
            except subprocess.CalledProcessError as e:
                tempdir = path_export + vmname + '-' + timestamp
                log_all(oVirt,vmname,
                                'Uploading VM ' + vmname + ' to TSM has failed with exit code: ' + str(e.returncode),
                                'error')
                log_all(oVirt,vmname, 'Uploading VM ' + vmname + ' to TSM has failed and moved to ' + tempdir,
                                'error')
                log_all(oVirt,vmname, "Backup VM '" + vmname + "' Failed [exit-code:6]","error")
                exit(6)
            try:
                remove_temp(path_export + vmname + "-" + timestamp)
            except:
                print("Couldn't delete {}".format(path_export + vmname + "-" + timestamp))
                log_all(oVirt,vmname, "Backup VM '" + vmname + "' Failed [exit-code:7]","error")
                exit(7)
            log_all(oVirt,vmname,"Backup Process for VM '"+vmname+"' finished without errors [exit-code:0]","normal")
    else:
        usage()

if __name__ == '__main__':
    main()
