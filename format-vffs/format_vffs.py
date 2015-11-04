#!/usr/bin/env python

"""
Format SSD as VFFS!

Requires pyVmomi, zsphere didn't work.

pyVmomi references:
* https://github.com/vmware/pyvmomi
* http://vmware.github.io/pyvmomi-community-samples/

To spoof a flash device, refer to:
* http://www.v-front.de/2013/10/faq-using-ssds-with-esxi.html
* http://www.virtuallyghetto.com/2013/07/emulating-ssd-virtual-disk-in-vmware.html
"""

import argparse
import atexit
import json
import requests

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

#======================================================================

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--destroy', default=False, action='store_true',
                        help='Destroy an existing VFFS volume')
    parser.add_argument('-l', '--list', default=False, action='store_true',
                        help='No modification, only print volume list')
    parser.add_argument('-a', '--address', required=True, action='store',
                        help='vCenter address')
    parser.add_argument('-o', '--port', type=int, default=443, action='store',
                        help='vCenter port')
    parser.add_argument('-u', '--user', required=True, action='store',
                        help='vCenter username')
    parser.add_argument('-p', '--password', required=True, action='store',
                        help='vCenter password')
    parser.add_argument('-e', '--host', required=True, action='store',
                        help='ESXi host name')
    parser.add_argument('-s', '--ssd', default='/none', action='store',
                        help='SSD path')
    args = parser.parse_args()
    return args


def sizeof_fmt(num):
    for item in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, item)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def print_fs(host_fs):
    print "{}\t{}\t".format("Name:     ", host_fs.volume.name)
    print "{}\t{}\t".format("UUID:          ", host_fs.volume.uuid)
    print "{}\t{}\t".format("Capacity:      ", sizeof_fmt(
        host_fs.volume.capacity))
    print "{}\t{}\t".format("Type:          ", host_fs.volume.type)
    print "{}\t{}\t".format("Version:  ", host_fs.volume.version)
    print "{}\t{}\t".format("Path:      ", host_fs.mountInfo.path)
    print

#======================================================================

def main():
    args = get_args()

    print "Retrieving service instance"
    # Disable secure connection checking
    # http://stackoverflow.com/a/28002687
    requests.packages.urllib3.disable_warnings()
    service_instance = connect.SmartConnect(host=args.address,
                                            user=args.user,
                                            pwd=args.password,
                                            port=args.port)

    atexit.register(connect.Disconnect, service_instance)

    print "Retrieving hosts"
    content = service_instance.RetrieveContent()
    objview = content.viewManager.CreateContainerView(content.rootFolder,
                                                      [vim.HostSystem],
                                                      True)
    esxi_hosts = objview.view
    objview.Destroy()

    for esxi_host in esxi_hosts:
        if esxi_host.name == args.host:
            storage_system = esxi_host.configManager.storageSystem
            host_file_sys_vol_mount_info = \
                storage_system.fileSystemVolumeInfo.mountInfo

            # Check for existing VFFS volumes
            print "Checking for existing VFFS volumes\n"
            raise_exist = False
            device_disk_name = args.ssd.split("/")[-1]
            for host_mount_info in host_file_sys_vol_mount_info:
                if host_mount_info.volume.type == "VFFS":
                    extents = host_mount_info.volume.extent
                    print_fs(host_mount_info)
                    for extent in extents:
                        if extent.diskName == device_disk_name:
                            raise_exist = host_mount_info.mountInfo.path

            # List volumes and exit
            if args.list:
                exit()

            # Handle volume exists cases including destroy (-d)
            # If volume was found, raise_exist is device path
            if raise_exist:
                if args.destroy:
                    print ("Found VFFS volume for device '%s', " \
                           "attempting destroy" % device_disk_name)
                    storage_system.DestroyVffs(vffsPath=raise_exist)
                    print "Done"
                    exit()
                else:
                    print ("Device '%s' is already formatted as VFFS at path " \
                           "'%s'" % (device_disk_name, raise_exist))
                    exit(-1)

            # Create the VFFS spec
            host_vffs_spec = vim.host.VffsVolume.Specification()
            host_vffs_spec.devicePath = args.ssd
            host_vffs_spec.majorVersion = 1
            host_vffs_spec.volumeName = "vffs-vol-1"
            print "Attempting format with spec: \n%s\n" % host_vffs_spec

            # Format VFFS volume
            host_vffs_vol = storage_system.FormatVffs(createSpec=host_vffs_spec)
            print "Device successfully formatted!\n"
            print host_vffs_vol

#======================================================================

if __name__ == "__main__":
    main()
