#!/usr/bin/python
# Mikael,@nsmfoo - blog.prowling.nu

# Tested on Ubuntu 14.04 and 16.04 LTS, using several brands of computers and types..but there is no guarantee that it will work anyway..
# Prerequisites: python-dmidecode, cd-drive and acpidump: apt-get install python-dmidecode libcdio-utils acpidump mesa-utils
# Windows binaries: DevManView(32 or 64-bit), Volumeid.exe, a text file with a list of computer/host and one with users.

# Import stuff
import commands
import os.path
import dmidecode
import random
import uuid
import re
import time
import StringIO

# Check dependencies
dependencies = ["/usr/bin/cd-drive", "/usr/bin/acpidump", "/usr/share/python-dmidecode", "DevManView.exe", "Volumeid.exe", "computer.lst", "user.lst", "/usr/bin/glxinfo"]
for dep in dependencies:
    if not (os.path.exists(dep)):
      print "[WARNING] Dependencies are missing, please verify that you have installed:", dep
      exit()

# Welcome
print '--- Generate VirtualBox templates to help thwart VM detection and more .. - Mikael, @nsmfoo ---'
print '[*] Creating VirtualBox modifications ..'

# Randomize serial
def serial_randomize(start=0, string_length=10):
    rand = str(uuid.uuid4())
    rand = rand.upper()
    rand = re.sub('-', '', rand)
    return rand[start:string_length]

dmi_info = {}

try:
   for v in dmidecode.bios().values():
     if type(v) == dict and v['dmi_type'] == 0:
        dmi_info['DmiBIOSVendor'] = v['data']['Vendor']
        dmi_info['DmiBIOSVersion'] = v['data']['Version']
        biosversion = v['data']['BIOS Revision']
        dmi_info['DmiBIOSReleaseDate'] = v['data']['Release Date']
except:
   dmi_info['DmiBIOSReleaseDate'] = v['data']['Relase Date']

try:
    dmi_info['DmiBIOSReleaseMajor'], dmi_info['DmiBIOSReleaseMinor'] = biosversion.split('.', 1)
except:
    dmi_info['DmiBIOSReleaseMajor'] = '** No value to retrieve **'
    dmi_info['DmiBIOSReleaseMinor'] = '** No value to retrieve **'

# python-dmidecode does not currently reveal all values .. this is plan B
dmi_firmware = commands.getoutput("dmidecode -t0")
try:
    dmi_info['DmiBIOSFirmwareMajor'], dmi_info['DmiBIOSFirmwareMinor'] = re.search(
        "Firmware Revision: ([0-9A-Za-z. ]*)", dmi_firmware).group(1).split('.', 1)
except:
    dmi_info['DmiBIOSFirmwareMajor'] = '** No value to retrieve **'
    dmi_info['DmiBIOSFirmwareMinor'] = '** No value to retrieve **'

for v in dmidecode.baseboard().values():
    if type(v) == dict and v['dmi_type'] == 2:
        serial_number = v['data']['Serial Number']
        dmi_info['DmiBoardVersion'] = v['data']['Version']
        dmi_info['DmiBoardProduct'] = "string:" + v['data']['Product Name']
        dmi_info['DmiBoardVendor'] = v['data']['Manufacturer']

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
dmi_board = commands.getoutput("dmidecode -t2")
try:
    asset_tag = re.search("Asset Tag: ([0-9A-Za-z ]*)", dmi_board).group(1)
except:
    asset_tag = '** No value to retrieve **'

dmi_info['DmiBoardAssetTag'] = asset_tag

try:
    loc_chassis = re.search("Location In Chassis: ([0-9A-Za-z ]*)", dmi_board).group(1)
except:
    loc_chassis = '** No value to retrieve **'

dmi_info['DmiBoardLocInChass'] = loc_chassis

# Based on the list from http://www.dmtf.org/sites/default/files/standards/documents/DSP0134_3.0.0.pdf
board_dict = {'Unknown': 1, 'Other': 2, 'Server Blade': 3, 'Connectivity Switch': 4, 'System Management Module': 5,
              'Processor Module': 6, 'I/O Module': 7, 'Memory Module': 8, 'Daughter board': 9, 'Motherboard': 10,
              'Processor/Memory Module': 11, 'Processor/IO Module': 12, 'Interconnect board': 13}
try:
    board_type = re.search("Type: ([0-9A-Za-z ]+)", dmi_board).group(1)
    board_type = str(board_dict.get(board_type))
except:
    board_type = '** No value to retrieve **'

dmi_info['DmiBoardBoardType'] = board_type

for v in dmidecode.system().values():
    if type(v) == dict and v['dmi_type'] == 1:
        dmi_info['DmiSystemSKU'] = v['data']['SKU Number']
        system_family = v['data']['Family']
        system_serial = v['data']['Serial Number']
        dmi_info['DmiSystemVersion'] = "string:" + v['data']['Version']
        dmi_info['DmiSystemProduct'] = v['data']['Product Name']
        dmi_info['DmiSystemVendor'] = v['data']['Manufacturer']

if not system_family:
    dmi_info['DmiSystemFamily'] = "Not Specified"
else:
    dmi_info['DmiSystemFamily'] = system_family

# Create a new UUID
newuuid = str(uuid.uuid4())
dmi_info['DmiSystemUuid'] = newuuid.upper()
# Create a new system serial number
dmi_info['DmiSystemSerial'] = (serial_randomize(0, len(system_serial)))

for v in dmidecode.chassis().values():
    dmi_info['DmiChassisVendor'] = v['data']['Manufacturer']
    chassi_serial = v['data']['Serial Number']
    dmi_info['DmiChassisVersion'] = v['data']['Version']
    dmi_info['DmiChassisType'] = v['data']['Type']

# Based on the list from http://www.dmtf.org/sites/default/files/standards/documents/DSP0134_3.0.0.pdf
chassi_dict = {'Other': 1, 'Unknown': 2, 'Desktop': 3, 'Low Profile Desktop': 4, 'Pizza Box': 5, 'Mini Tower': 6,
               'Tower': 7, 'Portable': 8, 'Laptop': 9, 'Notebook': 10, 'Hand Held': 11, 'Docking Station': 12,
               'All in One': 13, 'Sub Notebook': 14, 'Space-saving': 15, 'Lunch Box': 16, 'Main Server Chassis': 17,
               'Expansion Chassis': 18, 'SubChassis': 19, 'Bus Expansion Chassis': 20, 'Peripheral Chassis': 21, 'RAID Chassis': 22,
               'Rack Mount Chassis': 23, 'Sealed-case PC': 24, 'Multi-system chassis': 25, 'Compact PCI': 26, 'Advanced TCA': 27,
               'Blade': 28, 'Blade Enclosure': 29, 'Tablet': 30, 'Convertible': 31, 'Detachable': 32}

dmi_info['DmiChassisType'] = str(chassi_dict.get(dmi_info['DmiChassisType']))

# python-dmidecode does not reveal all values .. this is plan B
chassi = commands.getoutput("dmidecode -t3")
try:
    dmi_info['DmiChassisAssetTag'] = re.search("Asset Tag: ([0-9A-Za-z ]*)", chassi).group(1)
except:
    dmi_info['DmiChassisAssetTag'] = '** No value to retrieve **'

# Create a new chassi serial number
dmi_info['DmiChassisSerial'] = "string:" + (serial_randomize(0, len(chassi_serial)))

for v in dmidecode.processor().values():
    dmi_info['DmiProcVersion'] = v['data']['Version']
    dmi_info['DmiProcManufacturer'] = v['data']['Manufacturer']['Vendor']
# OEM strings
try:
    for v in dmidecode.type(11).values():
        oem_ver = v['data']['Strings']['3']
        oem_rev = v['data']['Strings']['2']
except:
    pass
try:
    dmi_info['DmiOEMVBoxVer'] = oem_ver
    dmi_info['DmiOEMVBoxRev'] = oem_rev
except:
    dmi_info['DmiOEMVBoxVer'] = '** No value to retrieve **'
    dmi_info['DmiOEMVBoxRev'] = '** No value to retrieve **'

# Write all data collected so far to file
if dmi_info['DmiSystemProduct']:
    file_name = dmi_info['DmiSystemProduct'].replace(" ", "").replace("/", "_") + '.sh'
else:
    file_name = dmi_info['DmiChassisType'] + '_' + dmi_info['DmiBoardProduct'] + '.sh'

logfile = file(file_name, 'w+')
logfile.write('#Script generated on: ' + time.strftime("%H:%M:%S") + '\n')
bash = """ if [ $# -eq 0 ]
  then
    echo "[*] Please add vm name!"
    echo "[*] Available vms:"
    VBoxManage list vms | awk -F'"' {' print $2 '} | sed 's/"//g'
    exit
fi """
logfile.write(bash + '\n')

for k, v in sorted(dmi_info.iteritems()):
    if '** No value to retrieve **' in v:
        logfile.write('# VBoxManage setextradata "$1" VBoxInternal/Devices/pcbios/0/Config/' + k + '\t' + v + '\n')
    else:
        logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/pcbios/0/Config/' + k + '\t\'' + v + '\'\n')
# Disk information
disk_dmi = {}
try:
    if os.path.exists("/dev/sda"):
        # Disk serial
        disk_serial = commands.getoutput("hdparm -i /dev/sda | grep -o 'SerialNo=[A-Za-z0-9_\+\/ .\"-]*' | awk -F= '{print $2}'")
        if 'SG_IO' in disk_serial:
          print '[WARNING] Unable to aquire the disk serial number! Will add one, but please try to run this script on another machine instead..'
          disk_serial = 'HUA721010KLA330'

        disk_dmi['SerialNumber'] = (serial_randomize(0, len(disk_serial)))

        if (len(disk_dmi['SerialNumber']) > 20):
            disk_dmi['SerialNumber'] = disk_dmi['SerialNumber'][:20]

        # Check for HP Legacy RAID
    elif os.path.exists("/dev/cciss/c0d0"):
        hp_old_raid = commands.getoutput("smartctl -d cciss,1 -i /dev/cciss/c0d0")
        disk_serial = re.search("Serial number:([0-9A-Za-z ]*)", hp_old_raid).group(1).replace(" ", "")
        disk_dmi['SerialNumber'] = (serial_randomize(0, len(disk_serial)))

        if (len(disk_dmi['SerialNumber']) > 20):
            disk_dmi['SerialNumber'] = disk_dmi['SerialNumber'][:20]

except OSError:
    print "Haz RAID?"
    print commands.getoutput("lspci | grep -i raid")

# Disk firmware rev
try:
    if os.path.exists("/dev/sda"):
        disk_fwrev = commands.getoutput(
            "hdparm -i /dev/sda | grep -o 'FwRev=[A-Za-z0-9_\+\/ .\"-]*' | awk -F= '{print $2}'")
        disk_dmi['FirmwareRevision'] = disk_fwrev
    elif os.path.exists("/dev/cciss/c0d0"):
         hp_old_raid = commands.getoutput("smartctl -d cciss,1 -i /dev/cciss/c0d0")
         disk_dmi['FirmwareRevision'] = re.search("Revision:([0-9A-Za-z ]*)", hp_old_raid).group(1).replace(" ", "")
except OSError:
    print "Haz RAID?"
    print commands.getoutput("lspci | grep -i raid")

if 'SG_IO' in disk_dmi['FirmwareRevision']:
    print '[WARNING] Unable to aquire the disk firmware revision! Will add one, but please try to run this script on another machine instead..'
    disk_dmi['FirmwareRevision'] = 'LMP07L3Q'
    disk_dmi['FirmwareRevision'] = (serial_randomize(0, len(disk_dmi['FirmwareRevision'])))

# Disk model number
try:
    if os.path.exists("/dev/sda"):
        disk_modelno = commands.getoutput(
            "hdparm -i /dev/sda | grep -o 'Model=[A-Za-z0-9_\+\/ .\"-]*' | awk -F= '{print $2}'")
        disk_dmi['ModelNumber'] = disk_modelno
    elif os.path.exists("/dev/cciss/c0d0"):
        hp_old_raid = commands.getoutput("smartctl -d cciss,1 -i /dev/cciss/c0d0")
        disk_dmi['ModelNumber'] = re.search("Product:([0-9A-Za-z ]*)", hp_old_raid).group(1).replace(" ", "")
except OSError:
    print "Haz RAID?"
    print commands.getoutput("lspci | grep -i raid")

if 'SG_IO' in disk_dmi['ModelNumber']:
    print '[WARNING] Unable to aquire the disk model number! Will add one, but please try to run this script on another machine instead..'
    disk_vendor = 'SAMSUNG'
    disk_vendor_part1 = 'F8E36628D278'
    disk_vendor_part1 = (serial_randomize(0, len(disk_vendor_part1)))
    disk_vendor_part2 = '611D3'
    disk_vendor_part2 = (serial_randomize(0, len(disk_vendor_part2)))
    disk_dmi['ModelNumber'] = (serial_randomize(0, len(disk_dmi['ModelNumber'])))
    disk_dmi['ModelNumber'] = disk_vendor + ' ' + disk_vendor_part1 + '-' + disk_vendor_part2
    print disk_dmi['ModelNumber']

logfile.write('controller=`VBoxManage showvminfo "$1" --machinereadable | grep SATA`\n')

logfile.write('if [[ -z "$controller" ]]; then\n')
for k, v in disk_dmi.iteritems():
    if '** No value to retrieve **' in v:
        logfile.write('# VBoxManage setextradata "$1" VBoxInternal/Devices/piix3ide/0/Config/PrimaryMaster/' + k + '\t' + v + '\n')
    else:
        logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/piix3ide/0/Config/PrimaryMaster/' + k + '\t\'' + v + '\'\n')

logfile.write('else\n')
for k, v in disk_dmi.iteritems():
    if '** No value to retrieve **' in v:
        logfile.write('# VBoxManage setextradata "$1" VBoxInternal/Devices/ahci/0/Config/Port0/' + k + '\t' + v + '\n')
    else:
        logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/ahci/0/Config/Port0/' + k + '\t\'' + v + '\'\n')
logfile.write('fi\n')

# CD-ROM information
cdrom_dmi = {}
if os.path.islink('/dev/cdrom'):
    # CD-ROM serial
    cdrom_serial = commands.getoutput(
        "hdparm -i /dev/cdrom | grep -o 'SerialNo=[A-Za-z0-9_\+\/ .\"-]*' | awk -F= '{print $2}'")
    if cdrom_serial:
        cdrom_dmi['ATAPISerialNumber'] = (serial_randomize(0, len(cdrom_serial)))
    else:
        cdrom_dmi['ATAPISerialNumber'] = "** No value to retrieve **"

    # CD-ROM firmeware rev
    cdrom_fwrev = commands.getoutput("cd-drive | grep Revision | grep  ':' | awk {' print $3 \" \" $4'}")
    cdrom_dmi['ATAPIRevision'] = cdrom_fwrev.replace(" ", "")

    # CD-ROM Model numberA-Za-z0-9_\+\/ .\"-
    cdrom_modelno = commands.getoutput("cd-drive | grep Model | grep  ':' | awk {' print $3 \" \" $4'}")
    cdrom_dmi['ATAPIProductId'] = cdrom_modelno

    # CD-ROM Vendor
    cdrom_vendor = commands.getoutput("cd-drive | grep Vendor | grep  ':' | awk {' print $3 '}")
    cdrom_dmi['ATAPIVendorId'] = cdrom_vendor
else:
    logfile.write('# No CD-ROM detected: ** No values to retrieve **\n')

# And some more
if os.path.islink('/dev/cdrom'):

 logfile.write('if [[ -z "$controller" ]]; then\n')

 for k, v in cdrom_dmi.iteritems():
     if '** No value to retrieve **' in v:
        logfile.write('# VBoxManage setextradata "$1" VBoxInternal/Devices/piix3ide/0/Config/PrimarySlave/' + k + '\t' + v + '\n')
     else:
        logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/piix3ide/0/Config/PrimarySlave/' + k + '\t\'' + v + '\'\n')

 logfile.write('else\n')

 for k, v in cdrom_dmi.iteritems():
     if '** No value to retrieve **' in v:
        logfile.write('# VBoxManage setextradata "$1" VBoxInternal/Devices/ahci/0/Config/Port1/' + k + '\t' + v + '\n')
     else:
        logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/ahci/0/Config/Port1/' + k + '\t\'' + v + '\'\n')
 logfile.write('fi\n')

# Get and write DSDT image to file
print '[*] Creating a DSDT file...'
if dmi_info['DmiSystemProduct']:
    dsdt_name = 'DSDT_' + dmi_info['DmiSystemProduct'].replace(" ", "").replace("/", "_") + '.bin'
    os.system("dd if=/sys/firmware/acpi/tables/DSDT of=" + dsdt_name + " >/dev/null 2>&1")
    logfile.write('VBoxManage setextradata "$1" "VBoxInternal/Devices/acpi/0/Config/CustomTable"\t' + os.getcwd() + '/' + dsdt_name + '\n')

else:
    dsdt_name = 'DSDT_' + dmi_info['DmiChassisType'] + '_' + dmi_info['DmiBoardProduct'] + '.bin'
    os.system("dd if=/sys/firmware/acpi/tables/DSDT of=" + dsdt_name + " >/dev/null 2>&1")
    logfile.write('VBoxManage setextradata "$1" "VBoxInternal/Devices/acpi/0/Config/CustomTable"\t' + os.getcwd() + '/' + dsdt_name + '\n')

acpi_dsdt = commands.getoutput('acpidump -s | grep DSDT | grep -o "\(([A-Za-z0-9].*)\)" | tr -d "()"')
acpi_facp = commands.getoutput('acpidump -s | grep FACP | grep -o "\(([A-Za-z0-9].*)\)" | tr -d "()"')

if "option requires" in acpi_dsdt:
    acpi_error = commands.getoutput("lsb_release -r | awk {' print $2 '}")
    print "The version of acpidump included in", acpi_error, 'is not supported'
    exit()
else:
    acpi_list_dsdt = acpi_dsdt.split(' ')
    acpi_list_dsdt = filter(None, acpi_list_dsdt)

    acpi_list_facp = acpi_facp.split(' ')
    acpi_list_facp = filter(None, acpi_list_facp)


logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/acpi/0/Config/AcpiOemId\t\'' + acpi_list_dsdt[1] + '\'\n')
logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/acpi/0/Config/AcpiCreatorId\t\'string:' + acpi_list_dsdt[4] + '\'\n')
logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/acpi/0/Config/AcpiCreatorRev\t\'' + acpi_list_dsdt[5] + '\'\n')

# Randomize MAC address, based on the host interface MAC
mac_seed = ':'.join(re.findall('..', '%012x' % uuid.getnode()))[0:9]
big_mac = mac_seed + "%02x:%02x:%02x" % (
    random.randint(0, 255),
    random.randint(0, 255),
    random.randint(0, 255),
)
le_big_mac = re.sub(':', '', big_mac)
logfile.write('VBoxManage modifyvm "$1" --macaddress1\t' + le_big_mac + '\n')

# Copy and set the CPU brand string
cpu_brand = commands.getoutput("cat /proc/cpuinfo | grep -m 1 'model name' | cut -d  ':' -f2 | sed 's/^ *//'")

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
          rebrand = commands.getoutput("echo -n '" + cpu_brand[k:i] + "' |od -A n -t x4 | sed 's/ //'")
          logfile.write('VBoxManage setextradata "$1" VBoxInternal/CPUM/HostCPUID/' + e + '/' + r + '  0x' +rebrand + '\t\n')
         i=i+4

# Check the numbers of CPUs, should be 2 or more
logfile.write('cpu_count=$(VBoxManage showvminfo --machinereadable "$1" | grep cpus=[0-9]* | sed "s/cpus=//")\t\n')
logfile.write('if [ $cpu_count -lt "2" ]; then echo "[WARNING] CPU count is less than 2. Consider adding more!"; fi\t\n')

# Check the set memory size. If it's less them 2GB notify user
logfile.write('memory_size=$(VBoxManage showvminfo --machinereadable "$1" | grep memory=[0-9]* | sed "s/memory=//")\t\n')
logfile.write('if [ $memory_size -lt "2048" ]; then echo "[WARNING] Memory size is 2GB or less. Consider adding more memory!"; fi\t\n')

# Check if hostonlyifs IP address is the default
logfile.write('hostint_ip=$(VBoxManage list hostonlyifs | grep IPAddress: | awk {\' print $2 \'})\t\n')
logfile.write('if [ $hostint_ip == \'192.168.56.1\' ]; then echo "[WARNING] You are using the default IP/IP-range. Consider changing the IP and the range used!"; fi\t\n')

# Check witch paravirtualization interface is being used (Setting it to "none" will mitigate the "cpuid feature" check)
logfile.write('virtualization_type=$(VBoxManage showvminfo --machinereadable "$1" | grep -i ^paravirtprovider | cut -d "=" -f2 | sed s\'/"//g\')\t\n')
logfile.write('if [ ! $virtualization_type == \'none\' ]; then echo "[WARNING] Please switch paravirtualization interface to: None!"; fi\t\n')

# Check if audio support is enabled
logfile.write('audio=$(VBoxManage showvminfo --machinereadable "$1" | grep audio | cut -d "=" -f2 | sed \'s/"//g\')\t\n')
logfile.write('if [ $audio == "none" ]; then echo "[WARNING] Please consider adding an audio device!"; fi\t\n')

# Check if you have the correct DevManview binary for the target architecture
logfile.write('devman_arc=$(VBoxManage showvminfo --machinereadable "$1" | grep ostype | cut -d "=" -f2 | grep -o "(.*)" | sed \'s/(//;s/)//;s/-bit//\')\t\n')
logfile.write('arc_devman=$(file -b DevManView.exe | grep -o \'80386\|64\' | sed \'s/80386/32/\')\t\n')
logfile.write('if [ $devman_arc != $arc_devman ]; then echo "[WARNING] Please use the DevManView version that coresponds to the guest architecture: $devman_arc "; fi\t\n')

# Done!
logfile.close()

print '[*] Finished: A template shell script has been created named:', file_name
print '[*] Finished: A DSDT dump has been created named:', dsdt_name

# Check file size
try:
    if os.path.getsize(dsdt_name) > 64000:
        print "[WARNING] Size of the DSDT file is too large (> 64k). Try to build the template from another computer"
except:
    pass

print '[*] Creating guest based modification file (to be run inside the guest)...'

# Write all data to file
if dmi_info['DmiSystemProduct']:
    file_name = dmi_info['DmiSystemProduct'].replace(" ", "").replace("/", "_") + '.ps1'
else:
    file_name = dmi_info['DmiChassisType'] + '_' + dmi_info['DmiBoardProduct'] + '.ps1'

logfile = file(file_name, 'w+')

# Tested on DELL, Lenovo clients and HP (old) server hardware, running Windows natively
if 'DELL' in acpi_list_dsdt[1]:
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

# FADT
logfile.write('if ($version -like \'10.0*\') {\r\n')
logfile.write('$oddity = "HKLM:\HARDWARE\ACPI\FADT\\" + (Get-ChildItem "HKLM:\HARDWARE\ACPI\FADT" -Name)\r\n')
logfile.write('Invoke-Expression ("Copy-Item -Path " + $oddity + " -Destination HKLM:\HARDWARE\ACPI\FADT\\' + manu +  ' -Recurse")\r\n')
logfile.write('Invoke-Expression ("Remove-Item -Path " + $oddity + " -Recurse")\r\n')

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
logfile.write('Invoke-Expression ("Copy-Item -Path " + $noproblem + " -Destination HKLM:\HARDWARE\ACPI\RSDT\\' + manu +  ' -Recurse")\r\n')
logfile.write('Invoke-Expression ("Remove-Item -Path " + $noproblem + " -Recurse")\r\n')
logfile.write('$cinnamon = "HKLM:\HARDWARE\ACPI\RSDT\\" + (Get-ChildItem "HKLM:\HARDWARE\ACPI\RSDT" -Name)\r\n')
logfile.write('$the_mero = "HKLM:\HARDWARE\ACPI\RSDT\\" + (Get-ChildItem "HKLM:\HARDWARE\ACPI\RSDT" -Name) + "\\" + (Get-ChildItem $cinnamon -Name)\r\n')
logfile.write('Invoke-Expression ("Copy-Item -Path " + $the_mero + " -Destination HKLM:\HARDWARE\ACPI\RSDT\\' + manu +  '\\' + acpi_list_dsdt[2] + '___ -Recurse")\r\n')
logfile.write('Invoke-Expression ("Remove-Item -Path " + $the_mero + " -Recurse")\r\n')
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\00000001 -Destination HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\' + acpi_list_dsdt[3] + ' -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\00000001 -Recurse\r\n')

logfile.write('}else{\r\n')
#Win7
logfile.write('Copy-Item -Path HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\00000001 -Destination HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\' + acpi_list_dsdt[3] + ' -Recurse\r\n')
logfile.write('Remove-Item -Path HKLM:\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list_dsdt[2] + '___\\00000001 -Recurse\r\n')
logfile.write('}\r\n')

# W10 specific settings:
logfile.write('if ($version  -like \'10.0*\') {\r\n')
# SDDT .. very beta ..
new_SDDT1 = commands.getoutput("sudo acpidump -s | grep SSDT | grep -o '\(([A-Za-z0-9].*)\)' | grep '00001000' | head -n 1 | awk {' print $2 '}")
new_SDDT2 = commands.getoutput("sudo acpidump -s | grep SSDT | grep -o '\(([A-Za-z0-9].*)\)' | grep '00001000' | head -n 1 | awk {' print $3 '}")
new_SDDT3 = commands.getoutput("sudo acpidump -s | grep SSDT | grep -o '\(([A-Za-z0-9].*)\)' | grep '00001000' | head -n 1 | awk {' print $4 '}")

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
new_dactype1 = commands.getoutput("lspci | grep -i VGA | cut -d ':' -f3 | awk {' print $1 '}")
new_dactype2 = commands.getoutput("lspci | grep -i VGA | cut -d ':' -f3 | awk {' print $2 '}")

logfile.write('$DacType = ((Get-ItemProperty -path \'HKLM:\SYSTEM\CurrentControlSet\Control\Video\*\\0000\')."HardwareInformation.DacType")\r\n')
logfile.write('if ($DacType -eq \'Oracle Corporation\') {\r\n')
logfile.write('New-ItemProperty -Path HKLM:\SYSTEM\CurrentControlSet\Control\Video\*\\0000 -Name HardwareInformation.DacType -Value "' + new_dactype1 + " " + new_dactype2 + '" -PropertyType "String" -force }\r\n')

logfile.write('$DacType = ((Get-ItemProperty -path \'HKLM:\SYSTEM\ControlSet001\Control\Class\*\\0016\')."HardwareInformation.DacType")\r\n')
logfile.write('if ($DacType -eq \'Oracle Corporation\') {\r\n')
logfile.write('New-ItemProperty -Path HKLM:\SYSTEM\ControlSet001\Control\Class\*\\0016 -Name HardwareInformation.DacType -Value "' + new_dactype1 + " " + new_dactype2 + '" -PropertyType "String" -force }\r\n')

# ChipType
new_chiptype1 = commands.getoutput("glxinfo -B | grep 'OpenGL renderer string' | cut -d ':' -f2 | sed  's/Mesa DRI//' | awk {' print $1 '} ")
new_chiptype2 = commands.getoutput("glxinfo -B | grep 'OpenGL renderer string' | cut -d ':' -f2 | sed  's/Mesa DRI//' | awk {' print $2 '} ")

if 'Error: unable to open display' in new_chiptype1:
    print "[WARNING] Unable to retrieve correct information! You are probably using a server distribution. Will add some semi correct data ... "
    new_chiptype1 = commands.getoutput("lshw -c video | grep -i vendor: | awk ' { print  $2 } '")
    new_chiptype2 = commands.getoutput("lshw -c video | grep -i vendor: | awk ' { print  $3 } '")

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

# Requires a copy of the DevManView.exe for the target architecture. Reference: http://www.nirsoft.net/utils/device_manager_view.html
with open("DevManView.exe", "rb") as file:
    data = file.read()
s = StringIO.StringIO(data.encode("base64"))

logfile.write('$base64_devmanview = \'')
for line in s:
    logfile.write(line)

DevManView = """'\r\n
[IO.File]::WriteAllBytes('DevManView.exe',[System.Convert]::FromBase64String($base64_devmanview))
$devman = @'
 ./DevManView.exe /uninstall *"DEV_CAFE"* /use_wildcard
'@
Invoke-Expression -Command:$devman\r\n"""
logfile.write(DevManView)

# Second attempt to fill the clipbord buffer with something, will be evolved in future versions. Windows command courtesy of a tweet by @shanselman
# Check if there is a user supplied list of things to populate the clipboard with
if (os.path.exists("clipboard_buffer")):
  with open("clipboard_buffer", "rb") as file:
    data = file.read()
  s = StringIO.StringIO(data.encode("base64"))

  logfile.write('$base64_clipboard = \'')
  for line in s:
    logfile.write(line)

  clipper = """'\r\n
  [IO.File]::WriteAllBytes('clipboard_buffer',[System.Convert]::FromBase64String($base64_clipboard))
  $clippy = Get-Random -InputObject (get-content clipboard_buffer)
  Invoke-Expression 'echo $clippy | clip'
  Remove-Item clipboard_buffer
  """
  logfile.write(clipper + '\r\n')
else:
 print '[Info] Could not find a user supplied file called: clipboard_buffer, a random string will be generated instead'
 palinka = """
 [Reflection.Assembly]::LoadWithPartialName("System.Web")
 $length = Get-Random -minimum 5 -maximum 115
 $none = Get-Random -minimum 5 -maximum $length
 $clipboard = [System.Web.Security.Membership]::GeneratePassword($length, $none)
 Invoke-Expression 'echo $clipboard | clip'
 """
 logfile.write(palinka)

# Start notepad with random files so that the system looks more homely(?), could easily be extended to other applications

langered = """
$location = "$ENV:userprofile\Desktop\", "$ENV:userprofile\Documents\", "$ENV:homedrive\", "$ENV:userprofile\Downloads\", "$ENV:userprofile\Pictures\"

$notepad = @()
foreach ($x in $location){
 Get-ChildItem $x | where {$_.extension -eq ".txt"} | % {
     $notepad += $_.FullName
 }
}
$notepad = $notepad | Sort-Object -unique {Get-Random}

$a = 0
foreach ($knackered in $notepad) {
    if ($a -le 3) {
     Start-Process 'C:\windows\system32\\notepad.exe' -ArgumentList $knackered -WindowStyle Minimized
     $a++
     }
}
"""
logfile.write(langered)

#################################################################
# "First" boot changes, requires reboot in order to be finalized
################################################################
# Check if this has been done before ..
waldo_check = """
if (Test-Path "kummerspeck") {
  Remove-Item "kummerspeck"
  Remove-Item "DevManView.exe"
  [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
  [System.Windows.Forms.MessageBox]::Show("You are now ready to infected!")
  exit
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

prodId = """
$newProductId = $newProductId.ToCharArray()

$convert = ""
foreach ($x in $newProductId) {
 $convert += $x -as [int]
}
$newNewProductId = $convert -split '(..)' | ? { $_ }

$convertID = @()
foreach ($x in $newNewProductId) {
 $convertID += [Convert]::ToString($x,16)
}

$data = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\DefaultProductKey" -Name DigitalProductId).DigitalProductId

$convertData = ""
foreach ($x in $data) {
 $convertData += [Convert]::ToString($x,16)
}

$con1 = $convertData.Substring(0,62)
$con2 = $convertData.Substring(62)
$con2 = $con2 -split '(..)' | ? { $_}
$static = @('A4','00','00','00','03','00','00','00')

# Finalize
$hexDigitalProductId = $static + $convertID + $con2

$hexHexDigitalProductId = @()
foreach ($xxx in $hexDigitalProductId) {
   $hexHexDigitalProductId += "0x$xxx"
}

Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" -Name DigitalProductId  -Value ([byte[]] $hexHexDigitalProductId)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Internet Explorer\Registration" -Name DigitalProductId  -Value ([byte[]] $hexHexDigitalProductId)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\DefaultProductKey" -Name DigitalProductId  -Value ([byte[]] $hexHexDigitalProductId)

# Agree on the Volumeid EULA - Reference: https://peter.hahndorf.eu/blog/WorkAroundSysinternalsLicenseP.html
New-Item -Path HKCU:\Software\Sysinternals
New-Item -Path HKCU:\Software\Sysinternals\VolumeId
New-ItemProperty -Path HKCU:\Software\Sysinternals\VolumeId -Name EulaAccepted -Value "1" -PropertyType "Dword" -force

"""
logfile.write(prodId +'\r\n')

# Requires a copy of the VolumeId.exe - Reference: https://technet.microsoft.com/en-us/sysinternals/bb897436.aspx
with open("Volumeid.exe", "rb") as file:
    data = file.read()
s = StringIO.StringIO(data.encode("base64"))

logfile.write('$base64_volumeid = \'')
for line in s:
    logfile.write(line)

logfile.write("\'\r\n[IO.File]::WriteAllBytes('Volumeid.exe',[System.Convert]::FromBase64String($base64_volumeid))\r\n")

# Requires a file with a list of "computer"(host) names - A start would be to use a list from this site: http://www.outpost9.com/files/WordLists.html
with open("computer.lst", "rb") as file:
    data = file.read()
s = StringIO.StringIO(data.encode("base64"))

logfile.write('$base64_computer = \'')
for line in s:
    logfile.write(line)

logfile.write("\'\r\n[IO.File]::WriteAllBytes('computer.lst',[System.Convert]::FromBase64String($base64_computer))\r\n")

# Requires a file with a list of "usernames" - A start would be to use a list from this site: http://www.outpost9.com/files/WordLists.html
with open("user.lst", "rb") as file:
    data = file.read()
s = StringIO.StringIO(data.encode("base64"))

logfile.write('$base64_user = \'')
for line in s:
    logfile.write(line)

logfile.write("\'\r\n[IO.File]::WriteAllBytes('user.lst',[System.Convert]::FromBase64String($base64_user))\r\n")

user_computer = """
    $result = ""
    $char_set = "ABCDEF0123456789".ToCharArray()
    for ($x = 0; $x -lt 8; $x++) {
     $result += $char_set | Get-Random
    }

    $volid1 = $result.Substring(0,4)
    $volid2 = $result.Substring(4)
    $weltschmerz = "c:"
    $dieweltschmerz = "$weltschmerz $volid1-$volid2"
    Invoke-Expression "./volumeid.exe $dieweltschmerz"

    $computer = Get-Random -InputObject (get-content computer.lst)
    (Get-WmiObject Win32_ComputerSystem).Rename($computer)

    $user = Get-Random -InputObject (get-content user.lst)
    $current_user = $ENV:username
    (Get-WmiObject Win32_UserAccount -Filter "Name='$current_user'").Rename($user)

    # Add waldo file
    New-Item kummerspeck -type file
    \r\n"""
logfile.write(user_computer + '\r\n')

# Chunk of Powershell code connected to the creation of random files and the randomization of the background image
ps_blob = """
# Pop-up
 # Windows 10 (Enterprise..) does not ask for confirmation by default
 if ($version -notlike '10.0*') {
  [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
  [System.Windows.Forms.MessageBox]::Show("Before you continue, please make sure that you have disabled 'Delete File confirmation dialog' (Right-click Recycle Bin -> Properties)")
 }
# RandomDate function
function RandomDate {
  $days = Get-Random -minimum 300 -maximum 2190
  $hours = Get-Random -minimum 5 -maximum 24
  $minutes = Get-Random -minimum 20 -maximum 60
  $seconds = Get-Random -minimum 12 -maximum 60
  return $days,$hours,$minutes,$seconds
}

# Generate files
function GenFiles([string]$status) {
 $TimeStamp = RandomDate
 $ext = Get-Random -input ".pdf",".txt",".docx",".doc",".xls", ".xlsx",".zip",".png",".jpg", ".jpeg", ".gif", ".bmp", ".html", ".htm", ".ppt", ".pptx"
 $namely = Get-Random -InputObject (get-content computer.lst)
 if ($version -notlike '10.0*') {
  $location = Get-Random -input "$ENV:userprofile\Desktop\\", "$ENV:userprofile\Documents\\", "$ENV:homedrive\\", "$ENV:userprofile\Downloads\\", "$ENV:userprofile\Pictures\\"
 } else {
  $location = Get-Random -input "$ENV:userprofile\Desktop\\", "$ENV:userprofile\Documents\\", "$ENV:userprofile\Downloads\\", "$ENV:userprofile\Pictures\\"
 }
 $length = Get-Random -minimum 300 -maximum 4534350
 $buffer = New-Object Byte[] $length
 New-Item $location$namely$ext -type file -value $buffer
 Get-ChildItem $location$namely$ext | % {$_.CreationTime = ((get-date).AddDays(-$TimeStamp[0]).AddHours(-$TimeStamp[1]).AddMinutes(-$TimeStamp[2]).AddSeconds(-$TimeStamp[3])) }
 Get-ChildItem $location$namely$ext | % {$_.LastWriteTime = ((get-date).AddDays(-$TimeStamp[0]).AddHours(-$TimeStamp[1]).AddMinutes(-$TimeStamp[2]).AddSeconds(-$TimeStamp[3])) }

 if ($status -eq "delete"){
# Now thrown them away!
  $shell = new-object -comobject "Shell.Application"
  $item = $shell.Namespace(0).ParseName("$location$namely$ext")
  $item.InvokeVerb("delete")
  }
}

# Generate files and then throw them away
 $amount = Get-Random -minimum 10 -maximum 30
  for ($x=0; $x -le $amount; $x++) {
   GenFiles delete
 }

# Generate files, but these we keep
 $amount = Get-Random -minimum 15 -maximum 45
  for ($x=0; $x -le $amount; $x++) {
   GenFiles
 }
# Set new background image (will only be visible after reboot)
 $image = Get-ChildItem -recurse c:\Windows\Web\Wallpaper -name -include *.jpg | Get-Random -Count 1
 Set-Itemproperty -path "HKCU:Control Panel\Desktop" -name WallPaper -value C:\Windows\Web\Wallpaper\$image\r\n """

logfile.write(ps_blob + '\r\n')

# Associate file extensions. Reference: https://www.proofpoint.com/us/threat-insight/post/massive-adgholas-malvertising-campaigns-use-steganography-and-file-whitelisting-to-hide-in-plain-sight
# Feel free to associate the file extensions with something else then Windows Media Player ..
assocblob = """
$assoc_ext = @('.divx=WMP11.AssocFile.WAV','.mkv=WMP11.AssocFile.WAV','.m4p=WMP11.AssocFile.WAV','.skype=WMP11.AssocFile.WAV','.flac=WMP11.AssocFile.WAV','.psd=WMP11.AssocFile.WAV','.torrent=WMP11.AssocFile.WAV')
$cmd = 'cmd /c'
$associ = 'assoc'

foreach ($z in $assoc_ext) {
 Invoke-Expression $cmd$associ$z
}
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
print '[*] Finished: A Powershell file has been created, named:', file_name
