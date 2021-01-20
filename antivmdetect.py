#!/usr/bin/python3
# Mikael,@nsmfoo - blog.prowling.nu

# Tested on Ubuntu 20.04 LTS, MacOS 11.x, using several brands of computers and types..but there is no guarantee that it will work anyway..
# Prerequisites: see README.md

# Import stuff
import subprocess
import netifaces
import os.path
import dmidecode
import random
import uuid
import re
import time
import base64
import sys

# Welcome
print('--- Generate VirtualBox templates to help thwart VM detection and more .. - Mikael, @nsmfoo ---')

if not os.geteuid()==0:
    sys.exit("\n[*] You need to run this script as root\n")

# Check dependencies
dependencies = ["/usr/bin/cd-drive", "/usr/bin/acpidump", "DevManView.exe", "Volumeid.exe", "computer.lst", "user.lst", "/usr/bin/glxinfo", "/usr/sbin/smartctl"]
for dep in dependencies:
    if not (os.path.exists(dep)):
      print('[WARNING] Dependencies are missing, please verify that you have installed: ', dep)
      exit()

print('[*] Creating VirtualBox modifications ..')

# Randomize serial
def serial_randomize(start=0, string_length=10):
    rand = str(uuid.uuid4())
    rand = rand.upper()
    rand = re.sub('-', '', rand)
    return rand[start:string_length]

dmi_info = {}

try:
   for v in dmidecode.get_by_type(0):
     if type(v) == dict and v['DMIType'] == 0:
        dmi_info['DmiBIOSVendor'] =  "string:" + v['Vendor']
        dmi_info['DmiBIOSVersion'] =  "string:" + v['Version'].replace(" ", "")
        biosversion = v['BIOS Revision']
        dmi_info['DmiBIOSReleaseDate'] =  "string:" + v['Release Date']
except:
   # This typo is deliberate, as a previous version of py-dmidecode contained a typo 
   dmi_info['DmiBIOSReleaseDate'] =  "string:" + v['Relase Date']

try:
    dmi_info['DmiBIOSReleaseMajor'], dmi_info['DmiBIOSReleaseMinor'] = biosversion.split('.', 1)
except:
    dmi_info['DmiBIOSReleaseMajor'] = '** No value to retrieve **'
    dmi_info['DmiBIOSReleaseMinor'] = '** No value to retrieve **'

# python-dmidecode does not currently reveal all values .. this is plan B
dmi_firmware = subprocess.getoutput("dmidecode t0")
try:
    dmi_info['DmiBIOSFirmwareMajor'], dmi_info['DmiBIOSFirmwareMinor'] = re.search(
        "Firmware Revision: ([0-9A-Za-z. ]*)", dmi_firmware).group(1).split('.', 1)
except:
    dmi_info['DmiBIOSFirmwareMajor'] = '** No value to retrieve **'
    dmi_info['DmiBIOSFirmwareMinor'] = '** No value to retrieve **'

for v in dmidecode.get_by_type(2):
    if type(v) == dict and v['DMIType'] == 2:
        serial_number = v['Serial Number']
        dmi_info['DmiBoardVersion'] =  "string:" + v['Version'].replace(" ", "")
        dmi_info['DmiBoardProduct'] = "string:" + v['Product Name'].replace(" ", "")
        dmi_info['DmiBoardVendor'] =  "string:" + v['Manufacturer'].replace(" ", "")

# This is hopefully not the best solution ..
try:
    s_number = []
    if serial_number:
        # Get position
        if '/' in serial_number:
            for slash in re.finditer('/', serial_number):
                s_number.append(slash.start(0))
                # Remove / from string
                new_serial = re.sub('/', '', serial_number)
                new_serial = serial_randomize(0, len(new_serial))
            # Add / again
            for char in s_number:
                new_serial = new_serial[:char] + '/' + new_serial[char:]
        else:
            new_serial = serial_randomize(0, len(serial_number))
    else:
        new_serial = "** No value to retrieve **"
except:
    new_serial = "** No value to retrieve **"

dmi_info['DmiBoardSerial'] = new_serial

# python-dmidecode does not reveal all values .. this is plan B
dmi_board = subprocess.getoutput("dmidecode -t2")
try:
    asset_tag = re.search("Asset Tag: ([0-9A-Za-z ]*)", dmi_board).group(1)
except:
    asset_tag = '** No value to retrieve **'

dmi_info['DmiBoardAssetTag'] =  "string:" + asset_tag

try:
    loc_chassis = re.search("Location In Chassis: ([0-9A-Za-z ]*)", dmi_board).group(1)
except:
    loc_chassis = '** No value to retrieve **'

dmi_info['DmiBoardLocInChass'] = "string:" + loc_chassis.replace(" ", "")

# Based on the list from https://www.dmtf.org/sites/default/files/standards/documents/DSP0134_3.4.0.pdf
board_dict = {'Unknown': 1, 'Other': 2, 'Server Blade': 3, 'Connectivity Switch': 4, 'System Management Module': 5,
              'Processor Module': 6, 'I/O Module': 7, 'Memory Module': 8, 'Daughter board': 9, 'Motherboard': 10,
              'Processor/Memory Module': 11, 'Processor/IO Module': 12, 'Interconnect board': 13}
try:
    board_type = re.search("Type: ([0-9A-Za-z ]+)", dmi_board).group(1)
    board_type = str(board_dict.get(board_type))
except:
    board_type = '** No value to retrieve **'

dmi_info['DmiBoardBoardType'] = board_type

for v in dmidecode.get_by_type(1):
    if type(v) == dict and v['DMIType'] == 1:
        dmi_info['DmiSystemSKU'] = v['SKU Number']
        system_family = v['Family']
        system_serial = v['Serial Number']
        dmi_info['DmiSystemVersion'] = "string:" + v['Version'].replace(" ", "")
        dmi_info['DmiSystemProduct'] = "string:" + v['Product Name'].replace(" ", "")
        dmi_info['DmiSystemVendor'] = "string:" + v['Manufacturer'].replace(" ", "")

if not system_family:
    dmi_info['DmiSystemFamily'] = "Not Specified"
else:
    dmi_info['DmiSystemFamily'] = "string:" + system_family

# Create a new UUID
newuuid = str(uuid.uuid4())
dmi_info['DmiSystemUuid'] = newuuid.upper()
# Create a new system serial number
dmi_info['DmiSystemSerial'] = "string:" + (serial_randomize(0, len(system_serial)))

for v in dmidecode.get_by_type(3):
    dmi_info['DmiChassisVendor'] = "string:" + v['Manufacturer'].replace(" ", "")
    chassi_serial = v['Serial Number']
    dmi_info['DmiChassisVersion'] = "string:" + v['Version'].replace(" ", "")
    dmi_info['DmiChassisType'] = v['Type']

# Based on the list from https://www.dmtf.org/sites/default/files/standards/documents/DSP0134_3.4.0.pdf
chassi_dict = {'Other': 1, 'Unknown': 2, 'Desktop': 3, 'Low Profile Desktop': 4, 'Pizza Box': 5, 'Mini Tower': 6,
               'Tower': 7, 'Portable': 8, 'Laptop': 9, 'Notebook': 10, 'Hand Held': 11, 'Docking Station': 12,
               'All in One': 13, 'Sub Notebook': 14, 'Space-saving': 15, 'Lunch Box': 16, 'Main Server Chassis': 17,
               'Expansion Chassis': 18, 'SubChassis': 19, 'Bus Expansion Chassis': 20, 'Peripheral Chassis': 21, 'RAID Chassis': 22,
               'Rack Mount Chassis': 23, 'Sealed-case PC': 24, 'Multi-system chassis': 25, 'Compact PCI': 26, 'Advanced TCA': 27,
               'Blade': 28, 'Blade Enclosure': 29, 'Tablet': 30, 'Convertible': 31, 'Detachable': 32, 'IoT Gateway': 33,
               'Embedded PC': 34, 'Mini PC': 35, 'Stick PC': 36}

dmi_info['DmiChassisType'] = str(chassi_dict.get(dmi_info['DmiChassisType']))

# python-dmidecode does not reveal all values .. this is plan B
chassi = subprocess.getoutput("dmidecode -t3")
try:
    dmi_info['DmiChassisAssetTag'] = "string:" + re.search("Asset Tag: ([0-9A-Za-z ]*)", chassi).group(1)
except:
    dmi_info['DmiChassisAssetTag'] = '** No value to retrieve **'

# Create a new chassi serial number
dmi_info['DmiChassisSerial'] = "string:" + (serial_randomize(0, len(chassi_serial)))

for v in dmidecode.get_by_type(4):
    dmi_info['DmiProcVersion'] = "string:" + v['Version'].replace(" ", "")
    dmi_info['DmiProcManufacturer'] = "string:" + v['Manufacturer'].replace(" ", "")
# OEM strings

try:
    for v in dmidecode.get_by_type(11):
        oem_ver = v['Strings']['3']
        oem_rev = v['Strings']['2']
except:
    pass
try:
    dmi_info['DmiOEMVBoxVer'] = "string:" + oem_ver
    dmi_info['DmiOEMVBoxRev'] = "string:" + oem_rev
except:
    dmi_info['DmiOEMVBoxVer'] = '** No value to retrieve **'
    dmi_info['DmiOEMVBoxRev'] = '** No value to retrieve **'

# Write all data collected so far to file
name_of_file = dmi_info['DmiSystemProduct'].replace(' ', '').replace('string:', '')
if name_of_file:
    file_name = dmi_info['DmiSystemProduct'].replace(" ", "").replace("/", "_").replace(",", "_").replace('string:', '') + '.sh'
else:
    file_name = dmi_info['DmiChassisType'] + '_' + dmi_info['DmiBoardProduct'].replace("string:", "") + '.sh'

logfile = open(file_name, 'w+')
logfile.write('#Script generated on: ' + time.strftime("%H:%M:%S") + '\n')
bash = """ if [ $# -eq 0 ]
  then
    echo "[*] Please add vm name!"
    echo "[*] Available vms:"
    VBoxManage list vms | awk -F'"' {' print $2 '} | sed 's/"//g'
    exit
fi """
logfile.write(bash + '\n')

for k, v in sorted(dmi_info.items()):
    if '** No value to retrieve **' in v:
        logfile.write('# VBoxManage setextradata "$1" VBoxInternal/Devices/pcbios/0/Config/' + k + '\t' + v + '\n')
    else:
        logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/pcbios/0/Config/' + k + '\t\'' + v + '\'\n')
# Disk information
disk_dmi = {}
disk_name = subprocess.getoutput("df -P / | tail -n 1 | awk '/.*/ { print $1 }'")

# Handle Ubuntu live-cd 
if '/cow' in disk_name:
 disk_name = "/dev/sdb"

# Disk serial
try:
    if os.path.exists(disk_name):
        disk_serial = subprocess.getoutput("smartctl -i " + disk_name + " | grep -o 'Serial Number:  [A-Za-z0-9_\+\/ .\"-]*' | awk '{print $3}'")
        if 'SG_IO' in disk_serial:
          print('[WARNING] Unable to acquire the disk serial number! Will add one, but please try to run this script on another machine instead..')
          disk_serial = 'HUA721010KLA330'

        disk_dmi['SerialNumber'] = (serial_randomize(0, len(disk_serial)))

        if (len(disk_dmi['SerialNumber']) > 20):
            disk_dmi['SerialNumber'] = disk_dmi['SerialNumber'][:20]
except OSError:
    print('Error reading system disk..')

# Disk firmware rev
try:
    if os.path.exists(disk_name):
       disk_fwrev = subprocess.getoutput("smartctl -i " + disk_name + " | grep -o 'Firmware Version: [A-Za-z0-9_\+\/ .\"-]*' | awk '{print $3}'")
       disk_dmi['FirmwareRevision'] = disk_fwrev    
       if 'SG_IO' in disk_dmi['FirmwareRevision']:
         print('[WARNING] Unable to acquire the disk firmware revision! Will add one, but please try to run this script on another machine instead..')
         disk_dmi['FirmwareRevision'] = 'LMP07L3Q'
         disk_dmi['FirmwareRevision'] = (serial_randomize(0, len(disk_dmi['FirmwareRevision'])))
except OSError:
    print('Error reading system disk..')

# Disk model number
try:
    if os.path.exists(disk_name):
        disk_modelno = subprocess.getoutput("smartctl -i " + disk_name + " | grep -o 'Model Family: [A-Za-z0-9_\+\/ .\"-]*' | awk '{print $3}'")
        disk_dmi['ModelNumber'] = disk_modelno

        if 'SG_IO' in disk_dmi['ModelNumber']:
          print('[WARNING] Unable to acquire the disk model number! Will add one, but please try to run this script on another machine instead..')
          disk_vendor = 'SAMSUNG'
          disk_vendor_part1 = 'F8E36628D278'
          disk_vendor_part1 = (serial_randomize(0, len(disk_vendor_part1)))
          disk_vendor_part2 = '611D3'
          disk_vendor_part2 = (serial_randomize(0, len(disk_vendor_part2)))
          disk_dmi['ModelNumber'] = (serial_randomize(0, len(disk_dmi['ModelNumber'])))
          disk_dmi['ModelNumber'] = disk_vendor + ' ' + disk_vendor_part1 + '-' + disk_vendor_part2
except OSError:
     print('Error reading system disk..')

logfile.write('controller=`VBoxManage showvminfo "$1" --machinereadable | grep SATA`\n')

logfile.write('if [[ -z "$controller" ]]; then\n')
for k, v in disk_dmi.items():
    if '** No value to retrieve **' in v:
        logfile.write('# VBoxManage setextradata "$1" VBoxInternal/Devices/piix3ide/0/Config/PrimaryMaster/' + k + '\t' + v + '\n')
    else:
        logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/piix3ide/0/Config/PrimaryMaster/' + k + '\t\'' + v + '\'\n')

logfile.write('else\n')
for k, v in disk_dmi.items():
    if '** No value to retrieve **' in v:
        logfile.write('# VBoxManage setextradata "$1" VBoxInternal/Devices/ahci/0/Config/Port0/' + k + '\t' + v + '\n')
    else:
        logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/ahci/0/Config/Port0/' + k + '\t\'' + v + '\'\n')
logfile.write('fi\n')

# CD-ROM information
cdrom_dmi = {}
if os.path.islink('/dev/cdrom'):
    # CD-ROM serial - No access to a computer with a CD-ROM to verify a switch to smartcrl, at the moment.
    cdrom_serial = subprocess.getoutput("hdparm -i /dev/cdrom | grep -o 'SerialNo=[A-Za-z0-9_\+\/ .\"-]*' | awk -F= '{print $2}'")
    if cdrom_serial:
        cdrom_dmi['ATAPISerialNumber'] = (serial_randomize(0, len(cdrom_serial)))
    else:
        cdrom_dmi['ATAPISerialNumber'] = "** No value to retrieve **"

    # CD-ROM firmeware rev
    cdrom_fwrev = subprocess.getoutput("cd-drive | grep Revision | grep  ':' | awk {' print $3 \" \" $4'}")
    cdrom_dmi['ATAPIRevision'] = cdrom_fwrev.replace(" ", "")

    # CD-ROM Model numberA-Za-z0-9_\+\/ .\"-
    cdrom_modelno = subprocess.getoutput("cd-drive | grep Model | grep  ':' | awk {' print $3 \" \" $4'}")
    cdrom_dmi['ATAPIProductId'] = cdrom_modelno

    # CD-ROM Vendor
    cdrom_vendor = subprocess.getoutput("cd-drive | grep Vendor | grep  ':' | awk {' print $3 '}")
    cdrom_dmi['ATAPIVendorId'] = cdrom_vendor
else:
    logfile.write('# No CD-ROM detected: ** No values to retrieve **\n')

# And some more
if os.path.islink('/dev/cdrom'):

 logfile.write('if [[ -z "$controller" ]]; then\n')

 for k, v in cdrom_dmi.items():
     if '** No value to retrieve **' in v:
        logfile.write('# VBoxManage setextradata "$1" VBoxInternal/Devices/piix3ide/0/Config/PrimarySlave/' + k + '\t' + v + '\n')
     else:
        logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/piix3ide/0/Config/PrimarySlave/' + k + '\t\'' + v + '\'\n')

 logfile.write('else\n')

 for k, v in cdrom_dmi.items():
     if '** No value to retrieve **' in v:
        logfile.write('# VBoxManage setextradata "$1" VBoxInternal/Devices/ahci/0/Config/Port1/' + k + '\t' + v + '\n')
     else:
        logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/ahci/0/Config/Port1/' + k + '\t\'' + v + '\'\n')
 logfile.write('fi\n')

# Get and write DSDT image to file
print('[*] Creating a DSDT file...')
name_of_dsdt = dmi_info['DmiSystemProduct'].replace(' ', '').replace('string:', '')
if name_of_dsdt:
    dsdt_name = 'DSDT_' + dmi_info['DmiSystemProduct'].replace(" ", "").replace("/", "_").replace("string:", "") + '.bin'
    os.system("dd if=/sys/firmware/acpi/tables/DSDT of=" + dsdt_name + " >/dev/null 2>&1")
else:
    dsdt_name = 'DSDT_' + dmi_info['DmiChassisType'] + '_' + dmi_info['DmiBoardProduct'].replace("string:", "") + '.bin'
    os.system("dd if=/sys/firmware/acpi/tables/DSDT of=" + dsdt_name + " >/dev/null 2>&1")
   
try:
    if os.path.isfile(dsdt_name): 
     logfile.write('if [ ! -f "' + dsdt_name + '" ]; then echo "[WARNING] Unable to find the DSDT file!"; fi\t\n')   
     logfile.write('VBoxManage setextradata "$1" "VBoxInternal/Devices/acpi/0/Config/CustomTable"\t "$PWD"/' + dsdt_name + '\n')   
     print('[*] Finished: A DSDT dump has been created named:', dsdt_name)  
except:
     print('[WARNING] Unable to create the DSDT dump')
     pass

acpi_dsdt = subprocess.getoutput('acpidump -s | grep DSDT | grep -o "\(([A-Za-z0-9].*)\)" | tr -d "()"')
acpi_facp = subprocess.getoutput('acpidump -s | grep FACP | grep -o "\(([A-Za-z0-9].*)\)" | tr -d "()"')

if "option requires" in acpi_dsdt:
    acpi_error = subprocess.getoutput("lsb_release -r | awk {' print $2 '}")
    print('The version of acpidump included in', acpi_error, 'is not supported')
    exit()
else:
    acpi_list_dsdt = acpi_dsdt.split(' ')
    acpi_list_dsdt = list(filter(None, acpi_list_dsdt))

    acpi_list_facp = acpi_facp.split(' ')
    acpi_list_facp = list(filter(None, acpi_list_facp))

# An attempt to solve some of the issues with the AcpiCreatorRev values, I blame the VBox team ..
if isinstance(acpi_list_dsdt[5],str):
 acpi_list_dsdt[5] = re.sub("[^0-9]", "", acpi_list_dsdt[5])

logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/acpi/0/Config/AcpiOemId\t\'' + acpi_list_dsdt[1] + '\'\n')
logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/acpi/0/Config/AcpiCreatorId\t\'' + acpi_list_dsdt[4] + '\'\n')
logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/acpi/0/Config/AcpiCreatorRev\t\'' + acpi_list_dsdt[5] + '\'\n')

# Randomize MAC address, based on the host interface MAC
find_int = netifaces.gateways()['default'][netifaces.AF_INET][1]
macme = netifaces.ifaddresses(find_int)[netifaces.AF_LINK][0]['addr']
l = macme.split(':')
mac_seed = l[0]+l[1]+l[2]

pattern = re.compile("^([0-9A-Fa-f]{2}){5}([0-9A-Fa-f]{2})$")

match = None
while match is None:
    big_mac = mac_seed + "%02x:%02x:%02x" % (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        )

    le_big_mac = re.sub(':', '', big_mac)
    match = pattern.match(le_big_mac)

logfile.write('VBoxManage modifyvm "$1" --macaddress1\t' + le_big_mac + '\n')

# Copy and set the CPU brand string
cpu_brand = subprocess.getoutput("cat /proc/cpuinfo | grep -m 1 'model name' | cut -d  ':' -f2 | sed 's/^ *//'")

if len(cpu_brand) < 47:
   cpu_brand = cpu_brand.ljust(47,' ')

eax_values=('80000002', '80000003', '80000004')
registers=('eax', 'ebx', 'ecx', 'edx')

i=4
while i<=47:
    for e in eax_values:
      for r in registers:
         k=i-4
         if len(cpu_brand[k:i]):
          rebrand = subprocess.getoutput("echo -n '" + cpu_brand[k:i] + "' |od -A n -t x4 | sed 's/ //'")
          logfile.write('VBoxManage setextradata "$1" VBoxInternal/CPUM/HostCPUID/' + e + '/' + r + '  0x' +rebrand + '\t\n')
         i=i+4

# Check the numbers of CPUs, should be 2 or more
logfile.write('cpu_count=$(VBoxManage showvminfo --machinereadable "$1" | grep cpus=[0-9]* | sed "s/cpus=//")\t\n')
logfile.write('if [ $cpu_count -lt "2" ]; then echo "[WARNING] CPU count is less than 2. Consider adding more!"; fi\t\n')

# Check the set memory size. If it's less than 2GB notify user
logfile.write('memory_size=$(VBoxManage showvminfo --machinereadable "$1" | grep memory=[0-9]* | sed "s/memory=//")\t\n')
logfile.write('if [ $memory_size -lt "2048" ]; then echo "[WARNING] Memory size is 2GB or less. Consider adding more memory!"; fi\t\n')

# Check if hostonlyifs IP address is the default
logfile.write('net_used=$(VBoxManage showvminfo "$1" | grep NIC | grep -v disabled | grep -o "vboxnet.")\t\n')
logfile.write('hostint_ip=$(VBoxManage list hostonlyifs | grep "$net_used\|IPAddress:" | sed -n \'2p\' | awk {\' print $2 \'} | grep \'192.168.56.1\')\t\n')
logfile.write('if [ "$hostint_ip" == \'192.168.56.1\' ]; then echo "[WARNING] You are using the default IP/IP-range. Consider changing the IP and the range used!"; fi\t\n')

# Check which paravirtualization interface is being used (Setting it to "none" will mitigate the "cpuid feature" check)
logfile.write('virtualization_type=$(VBoxManage showvminfo --machinereadable "$1" | grep -i ^paravirtprovider | cut -d "=" -f2 | sed \'s/"//g\')\t\n')
logfile.write('if [ ! $virtualization_type == \'none\' ]; then echo "[WARNING] Please switch paravirtualization interface to: None!"; fi\t\n')

# Check if audio support is enabled
logfile.write('audio=$(VBoxManage showvminfo --machinereadable "$1" | grep audio | cut -d "=" -f2 | sed \'s/"//g\' | head -1)\t\n')
logfile.write('if [ $audio == \'none\' ]; then echo "[WARNING] Please consider adding an audio device!"; fi\t\n')

# Check if you have the correct DevManview binary for the target architecture
arc_devman = subprocess.getoutput("file -b DevManView.exe | grep -o '80386\|64' | sed 's/80386/32/'")
logfile.write('arc_devman=' + arc_devman + '\t\n')
logfile.write('devman_arc=$(VBoxManage showvminfo --machinereadable "$1" | grep ostype | cut -d "=" -f2 | grep -o "(.*)" | sed \'s/(//;s/)//;s/-bit//\')\t\n')
logfile.write('if [ $devman_arc != $arc_devman ]; then echo "[WARNING] Please use the DevManView version that coresponds to the guest architecture: $devman_arc "; fi\t\n')

# Done!
logfile.close()

print('[*] Finished: A template shell script has been created named:', file_name)

# Check file size
try:
    if os.path.getsize(dsdt_name) > 64000:
        print('[WARNING] Size of the DSDT file is too large (> 64k). Try to build the template from another computer')
except:
    pass

print('[*] Creating guest based modification file (to be run inside the guest)...')

# Write all data to file
name_of_ps1 = dmi_info['DmiSystemProduct'].replace(' ', '').replace('string:', '')
if name_of_ps1:
    file_name = dmi_info['DmiSystemProduct'].replace(" ", "").replace("/", "_").replace('string:', '') + '.ps1'
else:
    file_name = dmi_info['DmiChassisType'] + '_' + dmi_info['DmiBoardProduct'].replace('string:', '') + '.ps1'

logfile = open(file_name, 'w+')

# Tested on DELL, Lenovo clients and some "noname" boxes, running Windows natively
if ('DELL' in acpi_list_dsdt[1] or 'INTEL' in acpi_list_dsdt[1]):
      manu = acpi_list_dsdt[1] + '__'
else:
  manu = acpi_list_dsdt[1]

# OS version - W7 or W10
logfile.write('$version = (Get-WmiObject win32_operatingsystem).version\r\n')

# DSDT
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\DSDT\VBOX__ -Destination HKLM:\HARDWARE\ACPI\DSDT\\' + manu + ' -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\DSDT\VBOX__ -Recurse\r\n')
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\DSDT\\' + manu + '\VBOXBIOS -Destination HKLM:\HARDWARE\ACPI\DSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___' +  ' -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\DSDT\\' + manu + '\VBOXBIOS -Recurse\r\n')
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\DSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\00000002 -Destination HKLM:\HARDWARE\ACPI\DSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\' + acpi_list_dsdt[3] + ' -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\DSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\00000002 -Recurse\r\n')

if 'INTEL' in acpi_list_dsdt[1]:
      manu = acpi_list_dsdt[1] + '_'
else:
  manu = acpi_list_dsdt[1]

# FADT
logfile.write('if ($version -like \'10.0*\') {\r\n')
logfile.write('$oddity = "HKLM:\HARDWARE\ACPI\FADT\\" + (Get-ChildItem "HKLM:\HARDWARE\ACPI\FADT" -Name)\r\n')
logfile.write('if ($oddity -ne "HKLM:\HARDWARE\ACPI\FADT\\' + manu + '") {\r\n')
logfile.write('Invoke-Expression ("Copy-Item -Path " + $oddity + " -Destination HKLM:\HARDWARE\ACPI\FADT\\' + manu +  ' -Recurse")\r\n')
logfile.write('Invoke-Expression ("Remove-Item -Path " + $oddity + " -Recurse")\r\n')
logfile.write('}\r\n')
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\FADT\\' + manu + '\VBOXFACP -Destination HKLM:\HARDWARE\ACPI\FADT\\' + manu + '\\' + acpi_list_facp[2] + '___ -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\FADT\\' + manu + '\VBOXFACP -Recurse\r\n')
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\FADT\\' + manu + '\\' + acpi_list_facp[2] + '___\\00000001 -Destination HKLM:\HARDWARE\ACPI\FADT\\' + manu + '\\' + acpi_list_facp[2] + '___\\' + acpi_list_facp[3] + ' -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\FADT\\' + manu + '\\' + acpi_list_facp[2] + '___\\00000001 -Recurse\r\n')
logfile.write('}else{\r\n')
#Win7
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\FADT\\' + manu + '\VBOXFACP -Destination HKLM:\HARDWARE\ACPI\FADT\\' + manu + '\\' + acpi_list_facp[2] + '___ -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\FADT\\' + manu + '\VBOXFACP -Recurse\r\n')
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\FADT\\' + manu + '\\' + acpi_list_facp[2] + '___\\00000001 -Destination HKLM:\HARDWARE\ACPI\FADT\\' + manu + '\\' + acpi_list_facp[2] + '___\\' + acpi_list_facp[3] + ' -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\FADT\\' + manu + '\\' + acpi_list_facp[2] + '___\\00000001 -Recurse\r\n')
logfile.write('}\r\n')

# RSDT
logfile.write('if ($version -like \'10.0*\') {\r\n')
logfile.write('$noproblem = "HKLM:\HARDWARE\ACPI\RSDT\\" + (Get-ChildItem "HKLM:\HARDWARE\ACPI\RSDT" -Name)\r\n')
logfile.write('if ($noproblem  -ne "HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '") {\r\n')
logfile.write('Invoke-Expression ("Copy-Item -Path " + $noproblem + " -Destination HKLM:\HARDWARE\ACPI\RSDT\\' + manu +  ' -Recurse")\r\n')
logfile.write('Invoke-Expression ("Remove-Item -Path " + $noproblem + " -Recurse")\r\n')
logfile.write('}\r\n')
logfile.write('$cinnamon = "HKLM:\HARDWARE\ACPI\RSDT\\" + (Get-ChildItem "HKLM:\HARDWARE\ACPI\RSDT" -Name)\r\n')
logfile.write('$the_mero = "HKLM:\HARDWARE\ACPI\RSDT\\" + (Get-ChildItem "HKLM:\HARDWARE\ACPI\RSDT" -Name) + "\\" + (Get-ChildItem $cinnamon -Name)\r\n')
logfile.write('Invoke-Expression ("Copy-Item -Path " + $the_mero + " -Destination HKLM:\HARDWARE\ACPI\RSDT\\' + manu +  '\\' + acpi_list_dsdt[2] + '___ -Recurse")\r\n')
logfile.write('Invoke-Expression ("Remove-Item -Path " + $the_mero + " -Recurse")\r\n')
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\00000001 -Destination HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\' + acpi_list_dsdt[3] + ' -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\00000001 -Recurse\r\n')
logfile.write('}else{\r\n')

#Win7
logfile.write('$check_exist = (Test-Path HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\00000001)\r\n')
logfile.write('if ($check_exist) {\r\n')
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\00000001 -Destination HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\' + acpi_list_dsdt[3] + ' -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\00000001 -Recurse\r\n')    
logfile.write('}else{\r\n')
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '\\00000001 -Destination HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '\\' + acpi_list_dsdt[3] + ' -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '\\00000001 -Recurse\r\n')
logfile.write('}}\r\n')

# W10 specific settings:
logfile.write('if ($version  -like \'10.0*\') {\r\n')

# SDDT .. very beta ..
new_SDDT1 = subprocess.getoutput("sudo acpidump -s | grep SSDT | grep -o '\(([A-Za-z0-9].*)\)' | head -n 1 | awk {' print $2 '}")
new_SDDT2 = subprocess.getoutput("sudo acpidump -s | grep SSDT | grep -o '\(([A-Za-z0-9].*)\)' | head -n 1 | awk {' print $3 '}")
new_SDDT3 = subprocess.getoutput("sudo acpidump -s | grep SSDT | grep -o '\(([A-Za-z0-9].*)\)' | head -n 1 | awk {' print $4 '}")

# Check if the key is present.. apparently it is not always the case? Feedback welcome
logfile.write('$check_exist = (Test-Path HKLM:\HARDWARE\ACPI\SSDT)\r\n')
logfile.write('if ($check_exist) {\r\n')
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\SSDT\VBOX__ -Destination HKLM:\HARDWARE\ACPI\SSDT\\' + new_SDDT1 + ' -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\SSDT\VBOX__ -Recurse\r\n')
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\SSDT\\' + new_SDDT1 + '\VBOXCPUT -Destination HKLM:\HARDWARE\ACPI\SSDT\\' + new_SDDT1 + '\\' + new_SDDT2 + '___ -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\SSDT\\' + new_SDDT1 + '\VBOXCPUT -Recurse\r\n')
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\SSDT\\' + new_SDDT1 + '\\' + new_SDDT2 + '___\\00000002 -Destination HKLM:\HARDWARE\ACPI\SSDT\\' + new_SDDT1 + '\\' + new_SDDT2 + '___\\' + new_SDDT3 + ' -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\SSDT\\' + new_SDDT1 + '\\' + new_SDDT2 + '___\\00000002 -Recurse\r\n')
logfile.write('}\r\n}\r\n')

# SystemBiosVersion - TODO: get real values
logfile.write('New-ItemProperty -Path HKLM:\HARDWARE\DESCRIPTION\System -Name SystemBiosVersion -Value "'+ acpi_list_dsdt[1] + ' - ' + acpi_list_dsdt[0] + '" -PropertyType "String" -force\r\n')

# VideoBiosVersion - TODO: get real values
logfile.write('New-ItemProperty -Path HKLM:\HARDWARE\DESCRIPTION\System -Name VideoBiosVersion -Value "' + acpi_list_dsdt[0] + '" -PropertyType "String" -force\r\n')

# SystemBiosDate
d_month, d_day, d_year = dmi_info['DmiBIOSReleaseDate'].split('/')
d_month = d_month.replace('string:','')
if len(d_year) > 2:
    d_year = d_year[2:]
logfile.write('New-ItemProperty -Path HKLM:\HARDWARE\DESCRIPTION\System -Name SystemBiosDate -Value "' + d_month + '/' + d_day + '/' + d_year + '" -PropertyType "String" -force\r\n')

# OS Install Date (InstallDate)
format = '%m/%d/%Y %I:%M %p'
start = "1/1/2012 5:30 PM"
end = time.strftime("%m/%d/%Y %I:%M %p")
prop = random.random()
stime = time.mktime(time.strptime(start, format))
etime = time.mktime(time.strptime(end, format))
ptime = stime + prop * (etime - stime)
logfile.write('New-ItemProperty -Path \"HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\" -Name InstallDate -Value "' + hex(int(ptime)) + '" -PropertyType "DWord" -force\r\n')
logfile.write('New-ItemProperty -Path \"HKCU:\SOFTWARE\Microsoft\Internet Explorer\SQM\" -Name InstallDate -Value "' + hex(int(ptime)) + '" -PropertyType "DWord" -force\r\n')

# MachineGuid
machineGuid = str(uuid.uuid4())
logfile.write('New-ItemProperty -Path HKLM:\SOFTWARE\Microsoft\Cryptography -Name MachineGuid -Value "' + machineGuid + '" -PropertyType "String" -force\r\n')

# W10 specific settings:
logfile.write('if ($version  -like \'10.0*\') {\r\n')

# DacType
new_dactype1 = subprocess.getoutput("lspci | grep -i VGA | cut -d ':' -f3 | awk {' print $1 '}")
new_dactype2 = subprocess.getoutput("lspci | grep -i VGA | cut -d ':' -f3 | awk {' print $2 '}")

logfile.write('$DacType = ((Get-ItemProperty -path \'HKLM:\SYSTEM\CurrentControlSet\Control\Video\*\\0000\')."HardwareInformation.DacType")\r\n')
logfile.write('if ($DacType -eq \'Oracle Corporation\') {\r\n')
logfile.write('New-ItemProperty -Path HKLM:\SYSTEM\CurrentControlSet\Control\Video\*\\0000 -Name HardwareInformation.DacType -Value "' + new_dactype1 + " " + new_dactype2 + '" -PropertyType "String" -force }\r\n')

logfile.write('$DacType = ((Get-ItemProperty -path \'HKLM:\SYSTEM\ControlSet001\Control\Class\*\\0016\')."HardwareInformation.DacType")\r\n')
logfile.write('if ($DacType -eq \'Oracle Corporation\') {\r\n')
logfile.write('New-ItemProperty -Path HKLM:\SYSTEM\ControlSet001\Control\Class\*\\0016 -Name HardwareInformation.DacType -Value "' + new_dactype1 + " " + new_dactype2 + '" -PropertyType "String" -force }\r\n')

# ChipType
new_chiptype1 = subprocess.getoutput("glxinfo -B | grep 'OpenGL renderer string' | cut -d ':' -f2 | sed  's/Mesa DRI//' | awk {' print $1 '} ")
new_chiptype2 = subprocess.getoutput("glxinfo -B | grep 'OpenGL renderer string' | cut -d ':' -f2 | sed  's/Mesa DRI//' | awk {' print $2 '} ")

if 'Error: unable to open display' in new_chiptype1:
    print('[WARNING] Unable to retrieve correct information! You are probably using a server distribution (at least not in X). Will add some semi correct data ...')
    new_chiptype1 = subprocess.getoutput("lshw -c video | grep -i vendor: | awk ' { print  $2 } '")
    new_chiptype2 = subprocess.getoutput("lshw -c video | grep -i vendor: | awk ' { print  $3 } '")

# Having access to only a limited amount of native Windows 10 installed hardware, I have at least noted that W10 reports Sandybridge/Ivybridge for systems that gxlinfo reports being equipped with Ivybridge.
if 'Ivybridge' in new_chiptype2:
    new_chiptype2 = 'Sandybridge/Ivybridge'

logfile.write('$ChipType = ((Get-ItemProperty -path HKLM:\SYSTEM\CurrentControlSet\Control\Video\*\\0000)."HardwareInformation.ChipType")\r\n')
logfile.write('if ($ChipType -eq \'VirtualBox VESA BIOS\') {\r\n')
logfile.write('New-ItemProperty -Path HKLM:\SYSTEM\CurrentControlSet\Control\Video\*\\0000 -Name HardwareInformation.ChipType -Value "' + new_chiptype1 + " " + new_chiptype2 + '" -PropertyType "String" -force }\r\n')

logfile.write('$ChipType = ((Get-ItemProperty -path HKLM:\SYSTEM\ControlSet001\Control\Class\*\\0016)."HardwareInformation.ChipType")\r\n')
logfile.write('if ($ChipType -eq \'VirtualBox VESA BIOS\') {\r\n')
logfile.write('New-ItemProperty -Path HKLM:\SYSTEM\ControlSet001\Control\Class\*\\0016 -Name HardwareInformation.ChipType -Value "' + new_chiptype1 + " " + new_chiptype2 + '" -PropertyType "String" -force }\r\n')

# BiosString
logfile.write('$BiosString = ((Get-ItemProperty -path HKLM:\SYSTEM\CurrentControlSet\Control\Video\*\\0000)."HardwareInformation.BiosString")\r\n')
logfile.write('if ($BiosString -eq \'Oracle VM VirtualBox VBE Adapte\') {\r\n')
logfile.write('New-ItemProperty -Path HKLM:\SYSTEM\CurrentControlSet\Control\Video\*\\0000 -Name HardwareInformation.BiosString -Value "' + new_chiptype1 + " " + new_chiptype2 + '" -PropertyType "String" -force }\r\n')

logfile.write('$BiosString = ((Get-ItemProperty -path HKLM:\SYSTEM\ControlSet001\Control\Class\*\\0016)."HardwareInformation.BiosString")\r\n')
logfile.write('if ($BiosString -eq \'Oracle VM VirtualBox VBE Adapte\') {\r\n')
logfile.write('New-ItemProperty -Path HKLM:\SYSTEM\ControlSet001\Control\Class\*\\0016 -Name HardwareInformation.BiosString -Value "' + new_chiptype1 + " " + new_chiptype2 + '" -PropertyType "String" -force }\r\n')

logfile.write('}\r\n')

# Requires a copy of the DevManView.exe for the target architecture. Reference: https://www.nirsoft.net/utils/device_manager_view.html
with open("DevManView.exe", "rb") as file:
    data = file.read()
s = base64.b64encode(data).decode("utf-8")

logfile.write('$base64_devmanview = \'')
logfile.write(s + '\'')

DevManView = """\r\n
[IO.File]::WriteAllBytes('DevManView.exe',[System.Convert]::FromBase64String($base64_devmanview))\r\n
$devman = @'\r\n
        ./DevManView.exe /uninstall *"DEV_CAFE"* /use_wildcard\r\n
'@\r\n
Invoke-Expression -Command:$devman\r\n"""
logfile.write(DevManView)

# Second attempt to fill the clipbord buffer with something, will be evolved in future versions. Windows command courtesy of a tweet by @shanselman
# Check if there is a user supplied list of things to populate the clipboard with
if (os.path.exists("clipboard_buffer")):
  with open("clipboard_buffer", "rb") as file:
    data = file.read()
  s = base64.b64encode(data).decode("utf-8")

  logfile.write('$base64_clipboard = \'')
  logfile.write(s + '\'')

  clipper = """\r\n
  [IO.File]::WriteAllBytes("clipboard_buffer",[System.Convert]::FromBase64String($base64_clipboard))\r\n
  $clippy = Get-Random -InputObject (get-content clipboard_buffer)\r\n
  Invoke-Expression "echo $clippy | clip"\r\n
  Remove-Item clipboard_buffer\r\n
  """
  logfile.write(clipper + '\r\n')
else:
 print("[Info] Could not find a user supplied file called: clipboard_buffer, a random string will be generated instead")
 palinka = """\r\n
 [Reflection.Assembly]::LoadWithPartialName("System.Web")\r\n
 $length = Get-Random -minimum 5 -maximum 115\r\n
 $none = Get-Random -minimum 5 -maximum $length\r\n
 $clipboard = [System.Web.Security.Membership]::GeneratePassword($length, $none)\r\n
 Invoke-Expression 'echo $clipboard | clip'\r\n
 """
 logfile.write(palinka)

# Start notepad with random files so that the system looks more homely(?), could easily be extended to other applications
langered = """\r\n
$location = "$ENV:userprofile\Desktop", "$ENV:userprofile\Documents", "$ENV:homedrive", "$ENV:userprofile\Downloads", "$ENV:userprofile\Pictures"\r\n

$notepad = @()\r\n
foreach ($x in $location){\r\n
 Get-ChildItem $x | where {$_.extension -eq ".txt"} | % {\r\n
     $notepad += $_.FullName\r\n
 }\r\n
}\r\n
$notepad = $notepad | Sort-Object -unique {Get-Random}\r\n

$a = 0\r\n
foreach ($knackered in $notepad) {\r\n
    if ($a -le 3) {\r\n
     Start-Process "C:\windows\system32\\notepad.exe" -ArgumentList $knackered -WindowStyle Minimized\r\n
     $a++\r\n
     }\r\n
}\r\n
"""
logfile.write(langered)

################################################################
# "First" boot changes, requires reboot in order to be finalized
################################################################
# Check if this has been done before ..
waldo_check = """
if (Test-Path "kummerspeck") {\r\n
  Remove-Item "kummerspeck"\r\n
  Remove-Item "DevManView.exe"\r\n
  [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")\r\n
  [System.Windows.Forms.MessageBox]::Show("You are now ready to infected!")\r\n
  exit\r\n
} \r\n"""
logfile.write(waldo_check + '\r\n')

# Microsoft Product ID (ProductId)
serial = [5,3,7,5]
o = []
for x in serial:
 o.append("%s" % ''.join(["%s" % random.randint(0, 9) for num in range(0, x)]))
newProductId = "{0}-{1}-{2}-{3}".format(o[0], o[1], o[2], o[3])

logfile.write('New-ItemProperty -Path \"HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\" -Name ProductId -Value "' + newProductId + '" -PropertyType "String" -force\r\n')
logfile.write('New-ItemProperty -Path \"HKLM:\SOFTWARE\Microsoft\Internet Explorer\Registration\" -Name ProductId -Value "' + newProductId + '" -PropertyType "String" -force\r\n')
logfile.write('New-ItemProperty -Path \"HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\DefaultProductKey\" -Name ProductId -Value "' + newProductId + '" -PropertyType "String" -force\r\n')

# Clear the Product key from the registry (prevents people from stealing it)
logfile.write('$slmgr="cscript $ENV:windir\system32\slmgr.vbs /cpky"\r\n')
logfile.write('iex $slmgr\r\n')

logfile.write('$newProductId = "' + newProductId + '"\r\n')

prodId = """\r\n
$newProductId = $newProductId.ToCharArray()\r\n

$convert = ""\r\n
foreach ($x in $newProductId) {\r\n
 $convert += $x -as [int]\r\n
}\r\n
$newNewProductId = $convert -split "(..)" | ? { $_ }\r\n

$convertID = @()\r\n
foreach ($x in $newNewProductId) {\r\n
 $convertID += [Convert]::ToString($x,16)\r\n
}\r\n

$data = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\DefaultProductKey" -Name DigitalProductId).DigitalProductId\r\n

$convertData = ""\r\n
foreach ($x in $data) {\r\n
 $convertData += [Convert]::ToString($x,16)\r\n
}\r\n

$con1 = $convertData.Substring(0,62)\r\n
$con2 = $convertData.Substring(62)\r\n
$con2 = $con2 -split "(..)" | ? { $_}\r\n
$static = @("A4","00","00","00","03","00","00","00")\r\n

# Finalize\r\n
$hexDigitalProductId = $static + $convertID + $con2\r\n

$hexHexDigitalProductId = @()\r\n
foreach ($xxx in $hexDigitalProductId) {\r\n
   $hexHexDigitalProductId += "0x$xxx"\r\n
}\r\n

Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" -Name DigitalProductId  -Value ([byte[]] $hexHexDigitalProductId)\r\n
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Internet Explorer\Registration" -Name DigitalProductId  -Value ([byte[]] $hexHexDigitalProductId)\r\n
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\DefaultProductKey" -Name DigitalProductId  -Value ([byte[]] $hexHexDigitalProductId)\r\n

# Agree on the Volumeid EULA - Reference: https://peter.hahndorf.eu/blog/WorkAroundSysinternalsLicenseP.html\r\n
$check_exist = (Test-Path HKCU:\Software\Sysinternals)\r\n
if (-Not $check_exist) {\r\n
    New-Item -Path HKCU:\Software\Sysinternals\r\n
    New-Item -Path HKCU:\Software\Sysinternals\VolumeId\r\n
    New-ItemProperty -Path HKCU:\Software\Sysinternals\VolumeId -Name EulaAccepted -Value "1" -PropertyType "Dword" -force\r\n
}\r\n
"""
logfile.write(prodId +'\r\n')

# Requires a copy of the VolumeId.exe - Reference: https://technet.microsoft.com/en-us/sysinternals/bb897436.aspx
with open("Volumeid.exe", "rb") as file:
    data = file.read()
s = base64.b64encode(data).decode("utf-8")

logfile.write('$base64_volumeid = \'')
logfile.write(s)

logfile.write("\'\r\n[IO.File]::WriteAllBytes('Volumeid.exe',[System.Convert]::FromBase64String($base64_volumeid))\r\n")

# Requires a file with a list of "computer"(host) names - A start would be to use a list from this site: https://www.outpost9.com/files/WordLists.html
with open("computer.lst", "rb") as file:
    data = file.read()
s = base64.b64encode(data).decode("utf-8")

logfile.write('$base64_computer = \'')
logfile.write(s)

logfile.write("\'\r\n[IO.File]::WriteAllBytes('computer.lst',[System.Convert]::FromBase64String($base64_computer))\r\n")

# Requires a file with a list of "usernames" - A start would be to use a list from this site: https://www.outpost9.com/files/WordLists.html
with open("user.lst", "rb") as file:
    data = file.read()
s = base64.b64encode(data).decode("utf-8")

logfile.write('$base64_user = \'')
logfile.write(s)

logfile.write("\'\r\n[IO.File]::WriteAllBytes('user.lst',[System.Convert]::FromBase64String($base64_user))\r\n")

user_computer = """\r\n
    $result = ""\r\n
    $char_set = "ABCDEF0123456789".ToCharArray()\r\n
    for ($x = 0; $x -lt 8; $x++) {\r\n
     $result += $char_set | Get-Random\r\n
    }\r\n

    $volid1 = $result.Substring(0,4)\r\n
    $volid2 = $result.Substring(4)\r\n
    $weltschmerz = "c:"\r\n
    $dieweltschmerz = "$weltschmerz $volid1-$volid2"\r\n
    Invoke-Expression "./volumeid.exe $dieweltschmerz"\r\n

    $computer = Get-Random -InputObject (get-content computer.lst)\r\n
    (Get-WmiObject Win32_ComputerSystem).Rename($computer)\r\n

    $user = Get-Random -InputObject (get-content user.lst)\r\n
    $current_user = $ENV:username\r\n
    (Get-WmiObject Win32_UserAccount -Filter "Name='$current_user'").Rename($user)\r\n

    # Add waldo file\r\n
    New-Item kummerspeck -type file\r\n
    \r\n"""
logfile.write(user_computer + '\r\n')

# Chunk of Powershell code connected to the creation of random files and the randomization of the background image
ps_blob = """
# Pop-up\r\n
 # Windows 10 (Enterprise..) does not ask for confirmation by default\r\n
 if ($version -notlike '10.0*') {\r\n
  [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")\r\n
  [System.Windows.Forms.MessageBox]::Show("Before you continue, please make sure that you have disabled 'Delete File confirmation dialog' (Right-click Recycle Bin -> Properties)")\r\n
 }\r\n
# RandomDate function\r\n
function RandomDate {\r\n
  $days = Get-Random -minimum 300 -maximum 2190\r\n
  $hours = Get-Random -minimum 5 -maximum 24\r\n
  $minutes = Get-Random -minimum 20 -maximum 60\r\n
  $seconds = Get-Random -minimum 12 -maximum 60\r\n
  return $days,$hours,$minutes,$seconds\r\n
}\r\n

# Generate files\r\n
function GenFiles([string]$status) {\r\n
 $TimeStamp = RandomDate\r\n
 $ext = Get-Random -input ".pdf",".txt",".docx",".doc",".xls", ".xlsx",".zip",".png",".jpg", ".jpeg", ".gif", ".bmp", ".html", ".htm", ".ppt", ".pptx"\r\n
 $namely = Get-Random -InputObject (get-content computer.lst)\r\n
 
 if ($version -notlike '10.0*') {\r\n
  $location = Get-Random -input "$ENV:userprofile\Desktop\\", "$ENV:userprofile\Documents\\", "$ENV:homedrive\\", "$ENV:userprofile\Downloads\\", "$ENV:userprofile\Pictures\\"\r\n
 } else {\r\n
  $location = Get-Random -input "$ENV:userprofile\Desktop\\", "$ENV:userprofile\Documents\\", "$ENV:userprofile\Downloads\\", "$ENV:userprofile\Pictures\\"\r\n
 }\r\n
 $length = Get-Random -minimum 300 -maximum 4534350\r\n
 $buffer = New-Object Byte[] $length\r\n
 
 New-Item $location$namely$ext -type file -value $buffer\r\n
 Get-ChildItem $location$namely$ext | % {$_.CreationTime = ((get-date).AddDays(-$TimeStamp[0]).AddHours(-$TimeStamp[1]).AddMinutes(-$TimeStamp[2]).AddSeconds(-$TimeStamp[3])) }\r\n
 Get-ChildItem $location$namely$ext | % {$_.LastWriteTime = ((get-date).AddDays(-$TimeStamp[0]).AddHours(-$TimeStamp[1]).AddMinutes(-$TimeStamp[2]).AddSeconds(-$TimeStamp[3])) }\r\n

 if ($status -eq "delete"){\r\n
# Now thrown them away!\r\n
  $shell = new-object -comobject "Shell.Application"\r\n
  $item = $shell.Namespace(0).ParseName("$location$namely$ext")\r\n
  $item.InvokeVerb("delete")\r\n
  }\r\n
}\r\n

# Generate files and then throw them away\r\n
 $amount = Get-Random -minimum 10 -maximum 30\r\n
 for ($x=0; $x -le $amount; $x++) {\r\n
   GenFiles delete\r\n
 }\r\n

# Generate files, but these we keep\r\n
 $amount = Get-Random -minimum 15 -maximum 45\r\n
for ($x=0; $x -le $amount; $x++) {\r\n
   GenFiles\r\n
 }
# Set new background image (will only be visible after reboot)\r\n
 $image = Get-ChildItem -recurse c:\Windows\Web\Wallpaper -name -include *.jpg | Get-Random -Count 1\r\n
 Set-Itemproperty -path "HKCU:Control Panel\Desktop" -name WallPaper -value C:\Windows\Web\Wallpaper\$image\r\n """

logfile.write(ps_blob + '\r\n')

# Associate file extensions. Reference: https://www.proofpoint.com/us/threat-insight/post/massive-adgholas-malvertising-campaigns-use-steganography-and-file-whitelisting-to-hide-in-plain-sight
# Feel free to associate the file extensions with something else then Windows Media Player ..
assocblob = """\r\n
$assoc_ext = @('.divx=WMP11.AssocFile.WAV','.mkv=WMP11.AssocFile.WAV','.m4p=WMP11.AssocFile.WAV','.skype=WMP11.AssocFile.WAV','.flac=WMP11.AssocFile.WAV','.psd=WMP11.AssocFile.WAV','.torrent=WMP11.AssocFile.WAV')\r\n
$cmd = 'cmd /c'\r\n
$associ = 'assoc'\r\n

foreach ($z in $assoc_ext) {\r\n
 Invoke-Expression $cmd$associ$z\r\n
}\r\n
"""
logfile.write(assocblob + '\r\n')

# De-associate file extensions. Reference: https://www.proofpoint.com/us/threat-insight/post/massive-adgholas-malvertising-campaigns-use-steganography-and-file-whitelisting-to-hide-in-plain-sight
# Disabled by default in this version, enable if you wish
#assocblob2 = """
#$assoc_remove = @('.py=','.saz=','.pcap=,'.chls=')
#$cmd = 'cmd /c'
#$associ 'assoc'
#foreach ($z in $assoc_remove) {
# Invoke-Expression $cmd$associ$z
#}
#"""
#logfile.write(assocblob2 + '\r\n')

# Sanitize
logfile.write('Remove-Item Volumeid.exe, user.lst, computer.lst, DevManView.exe\r\n')
logfile.write('Remove-Item -Path HKCU:\Software\Sysinternals\VolumeID -Recurse\r\n')
logfile.write('Remove-Item -Path HKCU:\Software\Sysinternals -Recurse\r\n')
# Reboot notification
logfile.write('[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")\r\n')
logfile.write('[System.Windows.Forms.MessageBox]::Show("The computer needs to reboot")\r\n')
logfile.write('Restart-Computer\r\n')

logfile.close()
print('[*] Finished: A Powershell file has been created, named:', file_name)
