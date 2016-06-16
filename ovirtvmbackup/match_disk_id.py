from __future__ import print_function
from xml.dom import minidom
import os, shutil


file_name_old = "/exportdomain/Web01/master/vms/67ebbd18-01c5-4434-b1ae-928ef33be56e/67ebbd18-01c5-4434-b1ae-928ef33be56e.ovf"
file_name_final = "/exportdomain/Web01/master/vms/a583ffd9-3a88-4347-b9b2-5bbce28414f7/a583ffd9-3a88-4347-b9b2-5bbce28414f7.ovf"
path_images="/exportdomain/Web01/images/"

def rename_clone(path_ovf_old, path_ovf_final, path):
    xml_doc_old = minidom.parse(path_ovf_old)
    xml_doc_final = minidom.parse(file_name_final)
    
    disks_old = xml_doc_old.getElementsByTagName('Disk')
    disks_final = xml_doc_final.getElementsByTagName('Disk')
    for disks in range(len(disks_old)):
        # obteniendo los objetos ovf:fileRef del XML
        old_xml = disks_old[disks].attributes["ovf:fileRef"].value
        final_xml = disks_final[disks].attributes["ovf:fileRef"].value
        # separando directorio del disco del value ovf:fileRef
        directory_src_name = os.path.dirname(old_xml)
        directory_dst_name = os.path.dirname(final_xml)
        # creando el path de los directorios involucrados
        directory_src = os.path.join(path, directory_src_name)
        directory_dst = os.path.join(path, directory_dst_name)
        # creando directorios nuevos
        os.mkdir(directory_dst)
        print("DIR from {} to {}".format(directory_src, directory_dst))
        # separando archivo del disco del value ovf:fileRef
        file_src = os.path.basename(old_xml)
        file_dst = os.path.basename(final_xml)
        # creando el path de los archivos involucrados
        old_file = os.path.join(path, directory_src_name, file_src)
        final_file = os.path.join(path, directory_dst_name, file_dst)
        # moviendo los archivos de disco
        print("FILE from {} to {}".format(old_file, final_file))
        shutil.move(old_file, final_file)
        # creando los path de META files
        old_file_meta = old_file + ".meta"
        final_file_meta = final_file + ".meta"
        # moviendo los archivos META 
        print("META from {} to {}".format(old_file + ".meta", final_file + ".meta"))
        shutil.move(old_file_meta, final_file_meta)
        #print("from {} to {}".format(path + file_src, path + file_dst))
        shutil.rmtree(directory_src)
        print("***********")
    shutil.rmtree(os.path.dirname(path_ovf_old))

rename_clone(file_name_old, file_name_final, path_images)

