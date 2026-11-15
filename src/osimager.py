"""
    This file is part of the Basata backup software.

    Basata is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Basata is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Basata.  If not, see <http://www.gnu.org/licenses/>.

Copyright 2018 by Michael Burns
    
"""

from pathlib import Path
import subprocess
import time
import json
import string
import os
import copy
import configparser
import shutil
import optparse

#sudo apt-get install cifs-utils
#sudo mount -t cifs -o username=d0gbert,password=PASSWORD //d0gbert-server/diskshare1 /mnt/shares/diskshare1




class OSImager:
	def __init__(self, do_compress=False):
		pass
		self.global_settings = {'batch_mode': 'sequential'}
		self.backup_list = {}
		self.temp_space = "/tmp/osimager"
		self.debug_level = 10
		self.compress_flag = do_compress
		self.create_temp_space()

	def create_temp_space(self):
		command = ["mkdir", "-p", self.temp_space]
		try:
			result = subprocess.run(command, capture_output=True, text=True, check=True)
			return result.stdout.strip() # Remove leading/trailing whitespace
		except subprocess.CalledProcessError as e:
			print(f"Command failed with error: {e.stderr}")
			raise Exception

	def mount(self, devpath, mount_point):
		command = ["mount", "-m", devpath, mount_point]
		try:
			result = subprocess.run(command, capture_output=True, text=True, check=True)
			return result.stdout.strip() # Remove leading/trailing whitespace
		except subprocess.CalledProcessError as e:
			print(f"Command failed with error: {e.stderr}")
			raise Exception

	def unmount(self, mount_point):
		command = ["umount", mount_point]
		try:
			result = subprocess.run(command, capture_output=True, text=True, check=True)
			return result.stdout.strip() # Remove leading/trailing whitespace
		except subprocess.CalledProcessError as e:
			print(f"Command failed with error: {e.stderr}")
			raise Exception

	def compress(self, filename):
		command = ["gzip", filename]
		try:
			result = subprocess.run(command, capture_output=True, text=True, check=True)
			return result.stdout.strip() # Remove leading/trailing whitespace
		except subprocess.CalledProcessError as e:
			print(f"Command failed with error: {e.stderr}")
			raise Exception

	def make_filesystem(self, devpath, fstype):
		if fstype == "swap":
			command = ["mkswap", devpath]
		else:
			command = ["mkfs.%s" % (fstype,), devpath]
		try:
			result = subprocess.run(command, capture_output=True, text=True, check=True)
			return result.stdout.strip() # Remove leading/trailing whitespace
		except subprocess.CalledProcessError as e:
			print(f"Command failed with error: {e.stderr}")
			raise Exception


	def get_partitions(self, drive_path):
		command = ["lsblk", "-JO", drive_path]
		partition_info = {'partitions': []}
		try:
			# Run the command and capture the output as text
			result = subprocess.run(command, capture_output=True, text=True, check=True)
			json_string_output = result.stdout.strip() # Remove leading/trailing whitespace
			# 2. Parse the JSON string into a Python dictionary
			lsblk_info = json.loads(json_string_output)			
			if len(lsblk_info['blockdevices']) != 1:
				print("Only one block device can be used at a time for creating an archive")
				raise Exception
			return lsblk_info['blockdevices'][0]
		except subprocess.CalledProcessError as e:
			print(f"Command failed with error: {e.stderr}")
			return None
		except json.JSONDecodeError:
			print("Failed to decode JSON from command output.")
			print("Output was:", json_string_output)
			return None
		except Exception as e:
			print(f"An unexpected error occurred: {e}")
			return None


	def overwrite_archive_file(self, img_filename, fetch_filename):
		archive_filename = img_filename.with_suffix(".tar")
		if self.compress_flag:
			raise Exception
		command1 = ["tar", "--delete", "-f", archive_filename, fetch_filename]
		command2 = ["tar", "-rf", archive_filename, fetch_filename]
		try:
			# Run the command and capture the output as text
			result = subprocess.run(command1, capture_output=True, text=True, check=True)
			result = subprocess.run(command2, capture_output=True, text=True, check=True)
			return result.stdout.strip()
		except subprocess.CalledProcessError as e:
			print(f"Command failed with error: {e.stderr}")
			return None
		except Exception as e:
			print(f"An unexpected error occurred: {e}")
			return None


	def fetch_archive_file(self, archive_filename, json_filename):
		if self.compress_flag:
			command_flags = "-xzf"
		else:
			command_flags = "-xf"
		command = ["tar", command_flags, archive_filename, json_filename, "-O"]
		try:
			# Run the command and capture the output as text
			result = subprocess.run(command, capture_output=True, text=True, check=True)
			return result.stdout.strip()
		except subprocess.CalledProcessError as e:
			print(f"Command failed with error: {e.stderr}")
			return None
		except Exception as e:
			print(f"An unexpected error occurred: {e}")
			return None


#tar -cvpf dude.tar -C /tmp/osimager osimager.json
#mount -m /dev/nvme1n1p1 /tmp/osimager/mounts/625192-121
#tar -rvpf dude.tar --transform='s,^,625192-121/,' --one-file-system /boot/firmware

	def generate_partition_info(self, lsblk_info):
		partition_info = {'partitions': []}
		partition_info.update({'parttype': lsblk_info['pttype'], 'diskuuid': lsblk_info['ptuuid']})
		for partition in lsblk_info['children']:
			partition_info['partitions'].append({'label': partition['label'], 'size': partition['size'], 'parttype': partition['parttype'], 'fstype': partition['fstype'], 'uuid': partition['partuuid']})
		return partition_info


	def create_archive(self, img_filename, partition_info):
		#print(lsblk_info)
		json_filename = "osimager.json"
		json_url = (self.temp_space+"/"+json_filename)
		with open(json_url, 'w') as json_file:
			json.dump(partition_info, json_file)
		command = ["tar", "-cvpf", img_filename, "-C", self.temp_space, json_filename]
		try:
			result = subprocess.run(command, capture_output=True, text=True, check=True)
			return result.stdout.strip() # Remove leading/trailing whitespace
		except subprocess.CalledProcessError as e:
			print(f"Command failed with error: {e.stderr}")
			raise Exception
		

#tar -rvpf dude.tar --transform 's,^,946e70a6/,' --one-file-system /boot/firmware/

	def addto_archive(self, img_filename, partuuid, mount_point, exclude_filename):
		#command = ["tar", "-rvpf", img_filename, "--transform", (f"s,^,{partuuid}/,"), "--one-file-system", mount_point]
		if exclude_filename is None:
			command = ["tar", "-rvpf", img_filename, "--transform", (f"s,^,{partuuid}/,"), "--one-file-system", "-C", mount_point, "."]
		else:
			command = ["tar", "-rvpf", img_filename, "--transform", (f"s,^,{partuuid}/,"), f"--exclude-tag={exclude_filename}", "--one-file-system", "-C", mount_point, "."]
		print(command)
		try:
			result = subprocess.run(command, capture_output=True, text=True, check=True)
			return result.stdout.strip() # Remove leading/trailing whitespace
		except subprocess.CalledProcessError as e:
			print(f"Command failed with error: {e.stderr}")
			raise Exception
		pass


	def backup_drive(self, drive_path, in_filename, exclude_filename):
		lsblk_info = self.get_partitions(drive_path)
		img_filename = in_filename.with_suffix(".tar")
		#print(lsblk_info)
		partition_info = self.generate_partition_info(lsblk_info)
		self.create_archive(img_filename, partition_info)
		for partition in lsblk_info['children']:
			#print(": ",partition)
			print("*** Backing up partition: %s" % (partition['path']))
			if partition['fstype'] == 'swap':
				continue
			if partition['mountpoint'] == None:
				mountpoint = "%s/mounts/%s" % (self.temp_space, partition['partuuid'])
				self.mount(partition['path'], mountpoint)
				self.addto_archive(img_filename, partition['partuuid'], mountpoint, exclude_filename)
				self.unmount(mountpoint)
			else:
				mountpoint = partition['mountpoint']
				print(partition['mountpoint'])
				self.addto_archive(img_filename, partition['partuuid'], mountpoint, exclude_filename)
		if self.compress_flag:
			self.compress(img_filename)
		pass

# sudo parted /dev/sdX mklabel gpt
# sudo parted -a opt /dev/sdX mkpart primary ext4 0% 100%
#sudo parted /dev/sda mkpart primary fat32 0G 2G
#sudo parted /dev/sda mkpart primary ntfs 2GB 3GB
#sudo parted /dev/sda mkpart primary ext2 3000MB 3500MB
#sudo parted /dev/sda mkpart primary ext4 0% 100%
#sudo mkfs.ext4 /dev/sda1

# tar -xzf dude.tar.gz osimager.json -O


# [{'label': 'bootfs', 'size': '512M', 'type': 'vfat', 'uuid': 'a65ac1bc-01'}, {'label': 'rootfs', 'size': '58.9G', 'type': 'ext4', 'uuid': 'a65ac1bc-02'}]

#	sfdisk_part_types = {'ext4': 'L', 'ext3': 'L', 'vfat': 'U', 'fat32': 'U', 'ntfs': 'H'}
#

	def create_partitions(self, drive_path, partition_info, do_expand):
		if partition_info['parttype'] == 'dos':
			partition_script = ['label: dos\n']
			partition_script.append('label-id: %s\n' % (partition_info['diskuuid']))
			partition_count = len(partition_info['partitions'])
			for partition in partition_info['partitions']:
				parttype = partition['parttype'].replace("0x","")
				if do_expand and partition_count == 1:	
					partition_script.append('type=%s,uuid=%s,name=%s\n' % (parttype,partition['uuid'],partition['label']))
				else:
					partition_script.append('size=%s,type=%s,uuid=%s,name=%s\n' % (partition['size'],parttype,partition['uuid'],partition['label']))
				partition_count-=1
		elif partition_info['parttype'] == 'gpt':
			partition_script = ['label: gpt\n']
			partition_count = len(partition_info['partitions'])
			for partition in partition_info['partitions']:
				if do_expand and partition_count == 1:
					partition_script.append('type=%s,uuid=%s,name=%s\n' % (partition['parttype'],partition['uuid'],partition['label']))
				else:	
					partition_script.append('size=%s,type=%s,uuid=%s,name=%s\n' % (partition['size'],partition['parttype'],partition['uuid'],partition['label']))
				partition_count-=1
		else:
			print("Partition type not supported")
			raise Exception
		print("Partition script: \n", partition_script)
		try:
			subprocess.run(['sfdisk','--force',drive_path], input=''.join(partition_script), text=True, check=True)
		except subprocess.CalledProcessError as e:
			print(f"Command failed with error: {e.stderr}")
			raise Exception
		pass

	def create_filesystems(self, drive_path, lsblk_info, partition_info):
		#lsblk_info = self.get_partitions(drive_path)
		partition_counter = 0
		for partition in lsblk_info['children']:
			#print(partition)
			dev_path = partition['path']
			partuuid = partition_info['partitions'][partition_counter]['uuid']
			fstype = partition_info['partitions'][partition_counter]['fstype']
			if partition['partuuid'] == partuuid:
				self.make_filesystem(dev_path, fstype)
			else:
				print("%s != %s" % (partition['partuuid'], partuuid))
				raise Exception
			partition_counter+=1
		pass


	def extract_archive(self, img_filename, partuuid, mount_point):
		if self.compress_flag:
			command_flags = "-xzpf"
		else:
			command_flags = "-xpf"
		# --transform='s|^a65ac1bc-02/||'
		#command = ["tar", command_flags, img_filename, "-C", mount_point, "--strip-components=1", "%s/" % (partuuid)]
		command = ["tar", command_flags, img_filename, "-C", mount_point, "--transform", (f"s|^{partuuid}/||"), "%s/" % (partuuid)]
		print(command)
		try:
			result = subprocess.run(command, capture_output=True, text=True, check=True)
			return result.stdout.strip() # Remove leading/trailing whitespace
		except subprocess.CalledProcessError as e:
			print(f"Extraction of partition failed with error: {e.stderr}")
			print("Moving on to next step...")
		pass

# {"partitions": [{"label": "bootfs", "size": "512M", "type": "vfat", "uuid": "946e70a6-01"}, 
#                 {"label": "rootfs", "size": "931G", "type": "ext4", "uuid": "946e70a6-02"}], 
#  "parttype": "dos", 
#  "diskuuid": "946e70a6"}

	def restore_drive(self, drive_path, in_filename, json_filename, do_expand):
		if self.compress_flag:
			img_filename = in_filename.with_suffix(".tar.gz")
		else:
			img_filename = in_filename.with_suffix(".tar")
		print("Restoring the archive: %s" % (str(img_filename),))	
		lsblk_info = self.get_partitions(drive_path)
		for partition in lsblk_info.get('children',[]):
			if not partition['mountpoint'] is None:
				print("Unmounting %s from %s" % (partition['path'], partition['mountpoint']))
				self.unmount(partition['mountpoint'])
		if json_filename is None:
			partition_info = json.loads(self.fetch_archive_file(img_filename, "osimager.json"))
		else:
			with open(json_filename, 'r') as file:
				partition_info = json.load(file)
		#for partition in partition_info['partitions']:
		#	print("Label: %s\tType: %s\tSize: %s" % (partition['label'], partition['parttype'], partition['size']))
		self.create_partitions(drive_path, partition_info, do_expand)
		print("Partitions created, waiting 30 seconds...")
		time.sleep(30)
		lsblk_info = self.get_partitions(drive_path)
		self.create_filesystems(drive_path, lsblk_info, partition_info)
		for partition in lsblk_info['children']:
			if(partition['fstype'] == 'swap'):
				continue
			mountpoint = "%s/mounts/%s" % (self.temp_space, partition['partuuid'])
			self.mount(partition['path'], mountpoint)
			self.extract_archive(img_filename, partition['partuuid'], mountpoint)
			self.unmount(mountpoint)
			print("Label: %s\tType: %s\tSize: %s" % (partition['label'], partition['parttype'], partition['size']))
		pass

# tar -xvf dude.tar osimager.json
# tar -rvf dude.tar osimager.json
# tar --delete -f dude.tar osimager.json

#sudo osimager backup /dev/sda artimus_laptop2 -c yes
#sudo osimager restore /dev/sda artimus_laptop2 -j artimus_partitions.json -c yes -x no
#

def main_program():
	argparse = optparse.OptionParser(description="OSImager Utility | Copyright 2026 by Michael Burns ",
												usage="usage: osimager.py (backup|restore|fetch) drive_path imgfile [options]",
												version="version 1.0")
	argparse.add_option("-c","--compress",dest="do_compress",default="no",help="The archive is or will be compressed using gzip (default: %default)")
	argparse.add_option("-j","--jsonfile",dest="jsonfilename",default="NONE",help="Use a custom partition json file for restore operation")
	argparse.add_option("-e","--exclude",dest="excludetag",default=".osimager_exclude",help="Exclude tag filename or NONE (default: %default)")
	argparse.add_option("-x","--expand",dest="do_expand",default="yes",help="Make the last partition take up the remaining space on a restore (default: %default)")
	(options, args) = argparse.parse_args()
	if len(args) < 1:
		print("*** No command given for Backup Program")
		return

	do_compress = options.do_compress
	do_expand = options.do_expand
	json_filename = options.jsonfilename
	exclude_filename = options.excludetag
	
	theapp= OSImager((True if do_compress == 'yes' else False))

	command = args[0]
	if command == "backup":
		if len(args) == 3:
			drive_path = args[1]
			img_filename = Path(args[2]).expanduser().resolve()
			exclude_filename = (None if exclude_filename == "NONE" else exclude_filename)
			theapp.backup_drive(drive_path, img_filename, exclude_filename)
		else:
			print("Invalid number of arguments")
	elif command == "restore":
		if len(args) == 3:
			drive_path = args[1]
			img_filename = Path(args[2]).expanduser().resolve()
			json_filename = (None if json_filename == "NONE" else json_filename)
			theapp.restore_drive(drive_path, img_filename, json_filename, (True if do_expand == "yes" else False))
		else:
			print("Invalid number of arguments")
	elif command == "fetch":
		if len(args) == 3:
			img_filename = Path(args[1]).expanduser().resolve()
			if do_compress == 'yes':
				img_filename = in_filename.with_suffix(".tar.gz")
			else:
				img_filename = in_filename.with_suffix(".tar")
			print(theapp.fetch_archive_file(img_filename, args[2]))
		else:
			print("Invalid number of arguments")
	else:
		print("*** Invalid command used with OSImager Program")


if __name__ == "__main__":
	main_program()
