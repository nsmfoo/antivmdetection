#!/usr/bin/python
# Mikael,@nsmfoo - blog.prowling.nu

# Tested on Ubuntu 14.04 LTS, using several brands of computers and types..but there is not an guarantee that it will work anyway
# Prerequisites: python-dmidecode, cd-drive and acpidump: apt-get install python-dmidecode libcdio-utils acpidump

# Import stuff
import commands
import os.path
import dmidecode
import random
import uuid
import re
import time

# Check dependencies
if not (os.path.exists("/usr/bin/cd-drive")) or not (os.path.exists("/usr/bin/acpidump")) or not (os.path.exists("/usr/share/python-dmidecode")):
 print '[WARNING] Dependencies are missing, please verify that you have installed: cd-drive, acpidump and python-dmidecode'
 exit()

# Welcome
print '--- Generate VirtualBox templates to help thwart vm detection - Mikael, @nsmfoo ---'
print '[*] Creating VirtualBox modifications ..'

# Randomize serial
def serial_randomize(start=0, string_length=10):
    rand = str(uuid.uuid4())
    rand = rand.upper()
    rand = re.sub('-', '', rand)
    return rand[start:string_length]

dmi_info = {}

for v in dmidecode.bios().values():
    if type(v) == dict and v['dmi_type'] == 0:
        dmi_info['DmiBIOSVendor'] = v['data']['Vendor']
        dmi_info['DmiBIOSReleaseDate'] = v['data']['Relase Date']
        dmi_info['DmiBIOSVersion'] = v['data']['Version']
        biosversion = v['data']['BIOS Revision']

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
    file_name = dmi_info['DmiSystemProduct'].replace(" ", "") + '.sh'
else:
    file_name = dmi_info['DmiChassisType'] + '_' + dmi_info['DmiBoardProduct'] + '.sh'

logfile = file(file_name, 'w+')
logfile.write('# Generated on: ' + time.strftime("%H:%M:%S") + '\n')
bash = """ if [ $# -eq 0 ]
  then
    echo "[*] Please add vm name!"
    echo "[*] Available vms:"
    VBoxManage list vms | awk {' print $1 '} | sed 's/"//g'
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
        disk_serial = commands.getoutput(
            "hdparm -i /dev/sda | grep -o 'SerialNo=[A-Za-z0-9_\+\/ .\"-]*' | awk -F= '{print $2}'")
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

# Disk Model number
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

# Write more things to file
for k, v in disk_dmi.iteritems():
    if '** No value to retrieve **' in v:
        logfile.write('# VBoxManage setextradata "$1" VBoxInternal/Devices/piix3ide/0/Config/PrimaryMaster/' + k + '\t' + v + '\n')
    else:
        logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/piix3ide/0/Config/PrimaryMaster/' + k + '\t\'' + v + '\'\n')

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
for k, v in cdrom_dmi.iteritems():
    if '** No value to retrieve **' in v:
        logfile.write('# VBoxManage setextradata "$1" VBoxInternal/Devices/piix3ide/0/Config/SecondaryMaster/' + k + '\t' + v + '\n')
    else:
        logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/piix3ide/0/Config/SecondaryMaster/' + k + '\t\'' + v + '\'\n')

# Get and write DSDT image to file
print '[*] Creating a DSDT file...'
if dmi_info['DmiSystemProduct']:
    dsdt_name = 'DSDT_' + dmi_info['DmiSystemProduct'].replace(" ", "") + '.bin'
    os.system("dd if=/sys/firmware/acpi/tables/DSDT of=" + dsdt_name + " >/dev/null 2>&1")
    logfile.write('VBoxManage setextradata "$1" "VBoxInternal/Devices/acpi/0/Config/CustomTable"\t' + os.getcwd() + '/' + dsdt_name + '\n')

else:
    dsdt_name = 'DSDT_' + dmi_info['DmiChassisType'] + '_' + dmi_info['DmiBoardProduct'] + '.bin'
    os.system("dd if=/sys/firmware/acpi/tables/DSDT of=" + dsdt_name + " >/dev/null 2>&1")
    logfile.write('VBoxManage setextradata "$1" "VBoxInternal/Devices/acpi/0/Config/CustomTable"\t' + os.getcwd() + '/' + dsdt_name + '\n')

acpi_misc = commands.getoutput('acpidump -s | grep DSDT | grep -o "\(([A-Za-z0-9].*)\)" | tr -d "()"')
acpi_list = acpi_misc.split(' ')
acpi_list = filter(None, acpi_list)

logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/acpi/0/Config/AcpiOemId\t\'' + acpi_list[1] + '\'\n')
logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/acpi/0/Config/AcpiCreatorId\t\'' + acpi_list[4] + '\'\n')
logfile.write('VBoxManage setextradata "$1" VBoxInternal/Devices/acpi/0/Config/AcpiCreatorRev\t\'' + acpi_list[5] + '\'\n')

# Randomize MAC address, based on onboard interface MAC
mac_seed = ':'.join(re.findall('..', '%012x' % uuid.getnode()))[0:9]
big_mac = mac_seed + "%02x:%02x:%02x" % (
    random.randint(0, 255),
    random.randint(0, 255),
    random.randint(0, 255),
)
le_big_mac = re.sub(':', '', big_mac)
# The last thing!
logfile.write('VBoxManage modifyvm "$1" --macaddress1\t' + le_big_mac)
# Done!
logfile.close()

print '[*] Finished: A template shell script has been created named:', file_name
print '[*] Finished: A DSDT dump has been created named:', dsdt_name

# check file size
try:
    if os.path.getsize(dsdt_name) > 64000:
        print "[WARNING] Size of the DSDT file is too large (> 64k). Try to build a template from another computer"
except:
    pass

print '[*] Creating guest based modification file (to be run inside the guest)...'

# Write all data to file
if dmi_info['DmiSystemProduct']:
    file_name = dmi_info['DmiSystemProduct'].replace(" ", "") + '.bat'
else:
    file_name = dmi_info['DmiChassisType'] + '_' + dmi_info['DmiBoardProduct'] + '.bat'

logfile = file(file_name, 'w+')

# Tested on DELL, Lenovo clients and HP (old) server hardware running Windows natively
if 'DELL' in acpi_list[1]:
      manu = acpi_list[1] + '__'
else:
  manu = acpi_list[1]

logfile.write('@ECHO OFF\r\n')

# DSDT
logfile.write('@reg copy HKLM\HARDWARE\ACPI\DSDT\VBOX__ HKLM\HARDWARE\ACPI\DSDT\\' + manu + ' /s /f\r\n')
logfile.write('@reg delete HKLM\HARDWARE\ACPI\DSDT\VBOX__ /f\r\n')

logfile.write('@reg copy HKEY_LOCAL_MACHINE\HARDWARE\ACPI\DSDT\\' + manu + '\VBOXBIOS HKEY_LOCAL_MACHINE\HARDWARE\ACPI\DSDT\\' + manu + '\\' + acpi_list[2] + '___' + ' /s /f\r\n')
logfile.write('@reg delete HKEY_LOCAL_MACHINE\HARDWARE\ACPI\DSDT\\' + manu + '\VBOXBIOS /f\r\n')

logfile.write('@reg copy HKEY_LOCAL_MACHINE\HARDWARE\ACPI\DSDT\\' + manu + '\\' + acpi_list[2] + '___\\00000002 HKEY_LOCAL_MACHINE\HARDWARE\ACPI\DSDT\\' + manu + '\\' + acpi_list[2] + '___\\' + acpi_list[3] + ' /s /f\r\n')
logfile.write('@reg delete HKEY_LOCAL_MACHINE\HARDWARE\ACPI\DSDT\\' + manu + '\\' + acpi_list[2] + '___\\00000002 /f\r\n')

# FADT
logfile.write('@reg copy HKLM\HARDWARE\ACPI\FADT\VBOX__ HKLM\HARDWARE\ACPI\FADT\\' + manu + ' /s /f\r\n')
logfile.write('@reg delete HKLM\HARDWARE\ACPI\FADT\VBOX__ /f\r\n')

logfile.write('@reg copy HKEY_LOCAL_MACHINE\HARDWARE\ACPI\FADT\\' + manu + '\VBOXFACP HKEY_LOCAL_MACHINE\HARDWARE\ACPI\FADT\\' + manu + '\\' + acpi_list[2] + '___  /s /f\r\n')
logfile.write('@reg delete HKEY_LOCAL_MACHINE\HARDWARE\ACPI\FADT\\' + manu + '\VBOXFACP /f\r\n')
logfile.write('@reg copy HKEY_LOCAL_MACHINE\HARDWARE\ACPI\FADT\\' + manu + '\\' + acpi_list[2] + '___\\00000001 HKEY_LOCAL_MACHINE\HARDWARE\ACPI\FADT\\' + manu + '\\' + acpi_list[2] + '___\\' + acpi_list[3] + ' /s /f\r\n')
logfile.write('@reg delete HKEY_LOCAL_MACHINE\HARDWARE\ACPI\FADT\\' + manu + '\\' + acpi_list[2] + '___\\00000001 /f\r\n')

logfile.write('@reg copy HKLM\HARDWARE\ACPI\RSDT\VBOX__ HKLM\HARDWARE\ACPI\RSDT\\' + manu + ' /s /f\r\n')
logfile.write('@reg delete HKLM\HARDWARE\ACPI\RSDT\VBOX__ /f\r\n')
# RSDT - differs between XP and W7
logfile.write('@reg query HKEY_LOCAL_MACHINE\HARDWARE\ACPI\RSDT\\' + manu + '\\VBOXRSDT > nul 2> nul\r\n')
# if XP then ..
logfile.write('if %ERRORLEVEL% equ 0 (\r\n')
logfile.write('@reg copy HKEY_LOCAL_MACHINE\HARDWARE\ACPI\RSDT\\' + manu + '\VBOXRSDT HKEY_LOCAL_MACHINE\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list[2] + '___  /s /f\r\n')
logfile.write('@reg delete HKEY_LOCAL_MACHINE\HARDWARE\ACPI\RSDT\\' + manu + '\VBOXRSDT /f\r\n')
logfile.write('@reg copy HKEY_LOCAL_MACHINE\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list[2] + '___\\00000001 HKEY_LOCAL_MACHINE\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list[2] + '___\\' + acpi_list[3] + ' /s /f\r\n')
logfile.write('@reg delete HKEY_LOCAL_MACHINE\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list[2] + '___\\00000001 /f\r\n')
logfile.write(') else (\r\n')
# if W7 then ..
logfile.write('@reg copy HKEY_LOCAL_MACHINE\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list[2] + '___\\00000001 HKEY_LOCAL_MACHINE\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list[2] + '___\\' + acpi_list[3] + ' /s /f\r\n')
logfile.write('@reg delete HKEY_LOCAL_MACHINE\HARDWARE\ACPI\RSDT\\' + manu + '\\' + acpi_list[2] + '___\\00000001 /f\r\n')
logfile.write(')\r\n')

# SystemBiosVersion - TODO: get real values
logfile.write('@reg add HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System /v SystemBiosVersion /t REG_MULTI_SZ /d "' + acpi_list[1] + ' - ' + acpi_list[0] + '" /f\r\n')
# VideoBiosVersion - TODO: get real values
logfile.write('@reg add HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System /v VideoBiosVersion /t REG_MULTI_SZ /d "' + acpi_list[0] + '" /f\r\n')
# SystemBiosDate
d_month, d_day, d_year = dmi_info['DmiBIOSReleaseDate'].split('/')

if len(d_year) > 2:
    d_year = d_year[:2]

logfile.write('@reg add HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System /v SystemBiosDate /t REG_MULTI_SZ /d "' + d_month + '/' + d_day + '/' + d_year + '" /f\r\n')

# OS Install Date
format = '%m/%d/%Y %I:%M %p'
start = "1/1/2012 5:30 PM"
end = time.strftime("%m/%d/%Y %I:%M %p")
prop = random.random()
stime = time.mktime(time.strptime(start, format))
etime = time.mktime(time.strptime(end, format))
ptime = stime + prop * (etime - stime)
logfile.write('@reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v InstallDate /t REG_DWORD /d "' + hex(int(ptime)) + '" /f\r\n')
logfile.write('@reg add "HKEY_CURRENT_USER\SOFTWARE\Microsoft\Internet Explorer\SQM" /v InstallDate /t REG_DWORD /d "' + hex(int(ptime)) + '" /f\r\n')

# MachineGuid
machineGuid = str(uuid.uuid4())
logfile.write('@reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography" /v MachineGuid /t REG_SZ /d "' + machineGuid + '" /f\r\n')

# Prevent WMI identification
# logfile.write('@reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\PlugPlay /v Start /t REG_MULTI_SZ /d "4" /f\r\n')

logfile.write('@reg copy HKLM\SYSTEM\ControlSet001\Services\VBoxGuest HKLM\SYSTEM\ControlSet001\Services\VBGuest /s /f\r\n')
logfile.write('@reg delete HKLM\SYSTEM\ControlSet001\Services\VBoxGuest /f\r\n')
logfile.write('@reg copy HKLM\SYSTEM\ControlSet001\Services\VBoxMouse HKLM\SYSTEM\ControlSet001\Services\VBMouse /s /f\r\n')
logfile.write('@reg delete HKLM\SYSTEM\ControlSet001\Services\VBoxMouse /f\r\n')
logfile.write('@reg copy HKLM\SYSTEM\ControlSet001\Services\VBoxService HKLM\SYSTEM\ControlSet001\Services\VBService /s /f\r\n')
logfile.write('@reg delete HKLM\SYSTEM\ControlSet001\Services\VBoxService /f\r\n')
logfile.write('@reg copy HKLM\SYSTEM\ControlSet001\Services\VBoxSF HKLM\SYSTEM\ControlSet001\Services\VBSF /s /f\r\n')
logfile.write('@reg delete HKLM\SYSTEM\ControlSet001\Services\VBoxSF /f\r\n')
logfile.write('@reg copy HKLM\SYSTEM\ControlSet001\Services\VBoxVideo HKLM\SYSTEM\ControlSet001\Services\VBVideo /s /f\r\n')
logfile.write('@reg delete HKLM\SYSTEM\ControlSet001\Services\VBoxVideo /f\r\n')
logfile.write('@reg copy HKLM\SYSTEM\ControlSet001\Services\VBoxVideo HKLM\SYSTEM\ControlSet001\Services\VBVideo /s /f\r\n')
logfile.write('@reg delete HKLM\SYSTEM\ControlSet001\Services\VBoxVideo /f\r\n')

logfile.write('@reg copy   HKLM\SYSTEM\CurrentControlSet\Enum\IDE\CdRomVBOX_CD-ROM_____________________________1.0_____ HKLM\SYSTEM\CurrentControlSet\Enum\IDE\CdRomVB_CD-ROM_____________________________1.0_____ /s /f\r\n')
logfile.write('@reg delete HKLM\SYSTEM\CurrentControlSet\Enum\IDE\CdRomVBOX_CD-ROM_____________________________1.0_____ /f\r\n')
logfile.write('@reg delete HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\IDE\CdRomVB_CD-ROM_____________________________1.0_____\\42562d3231303037333036372020202020202020 /v FriendlyName /f\r\n')
logfile.write('@reg add    HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\IDE\CdRomVB_CD-ROM_____________________________1.0_____\\42562d3231303037333036372020202020202020 /v FriendlyName /d "VB CD-ROM" /f\r\n')
logfile.write('@reg delete HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\IDE\CdRomVB_CD-ROM_____________________________1.0_____\\42562d3231303037333036372020202020202020 /v HardwareID /f\r\n')
logfile.write('@reg add    HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\IDE\CdRomVB_CD-ROM_____________________________1.0_____\\42562d3231303037333036372020202020202020 /v HardwareID /t "REG_MULTI_SZ" /d "IDE\CdRomVB_CD-ROM_____________________________1.0_____" /f\r\n')


logfile.write('@reg copy   HKLM\SYSTEM\CurrentControlSet\Enum\IDE\DiskVBOX_HARDDISK___________________________1.0_____  HKLM\SYSTEM\CurrentControlSet\Enum\IDE\DiskVB_HARDDISK___________________________1.0_____ /s /f\r\n')
logfile.write('@reg delete HKLM\SYSTEM\CurrentControlSet\Enum\IDE\DiskVBOX_HARDDISK___________________________1.0_____ /f\r\n')
logfile.write('@reg delete HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\IDE\DiskVB_HARDDISK___________________________1.0_____\\42563862613534626132362d3564663966332064 /v FriendlyName /f\r\n')
logfile.write('@reg add    HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\IDE\DiskVB_HARDDISK___________________________1.0_____\\42563862613534626132362d3564663966332064 /v FriendlyName /d "VB HARDDISK" /f\r\n')
logfile.write('@reg delete HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\IDE\DiskVB_HARDDISK___________________________1.0_____\\42563862613534626132362d3564663966332064 /v HardwareID /f\r\n')
logfile.write('@reg add    HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\IDE\DiskVB_HARDDISK___________________________1.0_____\\42563862613534626132362d3564663966332064 /v HardwareID /t "REG_MULTI_SZ" /d "IDE\DiskVB_HARDDISK___________________________1.0_____" /f\r\n')



logfile.close()
print '[*] Finished: A Windows batch file has been created named:', file_name





