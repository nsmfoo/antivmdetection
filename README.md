# antivmdetection
Script to create templates to use with VirtualBox to make vm detection harder.

My first post on the subject was in 2012 and has after that been updated at random times. The blog format might have not been the best way of publishing the information and some people did make nice and "easy to apply" script based on the content.

As a way to make it easier for me to add new content, I have decided to do the very same.
This version includes some new things, nothing major. But there are more things to come soon..

The purpose of this script is to use available settings without modifying the VirtualBox base. There are people who do really neat things by patching Virtualbox. But that is out of the scoop for this script.

When you run the script, the output will be: 

* One shell script, that can be used as a template. 
* A dump of the DSDT, that is used in the template script above. 
* A Windows batch file to be use inside the guest

#Notes:

1) Create the VM, but don't start it. The shell script needs to be run before installation! Verify that "I/O APIC" is enabled (system > Motherboard). The script assumes that the storage controller is IDE.
2) Run the shell script to apply the setting to the guest 
3) Install the Operating System 
4) Move the batch script to the newly installed guest.
5) Run the batch script inside the guest. Remember that the settings that gets modified are reverted after each reboot. So make it auto run if needed. 


You can use the scrip to prepare not only your cuckoo guests, but any vm that you need to make vm detection harder on.
Before you apply the batch script inside the guest, please disable UAC otherwise you will not be able to modify the registry with the script

Virtualbox 5 users should stick to using the "Legacy" (System -> Acceleration) paravirtulization interface for now.




/Mikael

Feedback is always welcome!

